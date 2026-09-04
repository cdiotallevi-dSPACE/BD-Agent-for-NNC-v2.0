from __future__ import annotations
import asyncio, json, logging, os, re, threading
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
import fitz
import httpx
import jsonschema
from bs4 import BeautifulSoup
from .config_manager import load_yaml, load_search_config
from .core import atomic_json, local_run_directory_timestamp, normalize_url, run_timestamp, sha256_text, slugify, utc_now
from .model_runtime import EMBEDDING_MODEL, FINAL_REPORT_MODEL
from .portfolio_index import retrieve, validate_index, portfolio_scope, prefetch_portfolio, local_model_post
from .execution_resources import http_scope, ordered_downloads, pdf_hashes, bounded_page_text
from .search_orchestrator import discover_sync
from .relevant_evidence_builder import build_relevant_evidence
from .llm_context_builder import build_llm_context, fit_complete_prompt
from .report_generator import render_reports, report_identity
from .ownership_contract_builder import enrich_ownership
from .prompt_loader import PromptBundleError, build_effective_prompt, load_prompt_bundle
from .narrative_ownership_validator import validate_narrative_ownership
from .llm_response_validator import detect_truncation, parse_json_without_repair
from .nnc_domain import evaluate_nnc_gates, score_nnc_applicability
from .nnc_scoring import aggregate_company_scores
from .company_attribution import establish_document_company_attribution
from .evidence_context import extract_document_evidence

log = logging.getLogger(__name__)
SPECIFICATION_VERSION="1.10"
DESIGN_DOCUMENT_VERSION="1.10.0"

SOURCE_COUNT_KEYS=(
    "total_retrieved_sources","total_retrieved_and_approved_sources",
    "total_retrieved_pdfs","total_retrieved_and_approved_pdfs",
    "total_retrieved_patents","total_retrieved_and_approved_patents",
)

def consolidate_use_case_mappings(mappings:list[dict], maximum:int=3)->list[dict]:
    """Publish one mapping per use case and separate evidence from product capability."""
    by_case={}
    for mapping in mappings:
        case=str(mapping.get("use_case_id") or mapping.get("target_company_entity_id") or "").strip()
        if case and (case not in by_case or int(mapping.get("dspace_applicability_score",0))>int(by_case[case].get("dspace_applicability_score",0))):
            by_case[case]=mapping
    result=[]
    for case,mapping in sorted(by_case.items(),key=lambda pair:-int(pair[1].get("dspace_applicability_score",0)))[:maximum]:
        readiness=mapping.get("nnc_use_case_scoring",{}).get("deployment_readiness",{})
        customer=(f"Customer evidence supports {case.replace('_',' ')}. Current ONNX adoption: "
                  f"{readiness.get('onnx_adoption','unconfirmed')}; generated-code workflow: "
                  f"{readiness.get('generated_code_workflow','unconfirmed')}.")
        capability="Neural Net Coder potential capability: neural-model handover, optimized embedded C/C++ generation, and deployment verification; this does not assert current customer adoption."
        item=dict(mapping); item.update({"mapping_id":f"MAP-{len(result)+1:04d}","use_case_id":case,
            "customer_evidence_and_readiness":customer,"nnc_product_capability":capability,"mapping_display":customer+" "+capability})
        result.append(item)
    return result


def calculate_cycle_source_counts(sources:list[dict],relevant:dict)->dict[str,int]:
    """Calculate cycle counts; approved includes use-case and company-background evidence."""
    failed={"retrieval_failed","parse_failed","not_attempted","pdf_document_budget_excluded","pdf_page_budget_excluded"}
    retrieved=[source for source in sources
               if source.get("retrieval_status") not in failed and not source.get("retrieval_error")
               and bool(source.get("content_hash"))]
    relevant_items=[*relevant.get("relevant_evidence",[]),*relevant.get("company_background_evidence",[])]
    approved_ids={item.get("source_id") for item in relevant_items if item.get("source_id")}
    source_by_id={source.get("source_id"):source for source in sources}
    retrieved_pdfs={source["source_id"] for source in retrieved if source.get("source_type")=="pdf"}
    approved_pdfs={source_id for source_id in approved_ids if source_by_id.get(source_id,{}).get("source_type")=="pdf"}

    def patent_key(source:dict)->str|None:
        url=str(source.get("url") or "").casefold()
        if not (source.get("normalized_publication_number") or source.get("source_domain_class")=="specialist_patent_source" or
                "patents.google.com/patent/" in url or "data.uspto.gov/" in url or "api.uspto.gov/" in url):
            return None
        return str(source.get("normalized_publication_number") or source.get("url") or source.get("source_id"))

    retrieved_patents={key for source in retrieved if (key:=patent_key(source))}
    relevant_by_id={item.get("source_id"):item for item in relevant_items}
    approved_patents={key for source_id in approved_ids if (key:=(patent_key(source_by_id.get(source_id,{})) or
        (str(source_id) if relevant_by_id.get(source_id,{}).get("source_category")=="target_company_patent" else None)))}
    return {
        "total_retrieved_sources":len(retrieved),
        "total_retrieved_and_approved_sources":len(approved_ids),
        "total_retrieved_pdfs":len(retrieved_pdfs),
        "total_retrieved_and_approved_pdfs":len(approved_pdfs),
        "total_retrieved_patents":len(retrieved_patents),
        "total_retrieved_and_approved_patents":len(approved_patents),
    }

def normalize_llm_list_fields(summary: dict) -> tuple[dict, dict]:
    """Remove content-free list entries without repairing substantive schema errors."""
    normalization={"applied":False,"removed_empty_information_gaps":0,"removed_empty_recommended_actions":0}
    gaps=summary.get("key_information_gaps")
    if isinstance(gaps,list):
        normalized_gaps=[]
        for item in gaps:
            if isinstance(item,str) and not item.strip():
                normalization["removed_empty_information_gaps"]+=1
                continue
            normalized_gaps.append(item.strip() if isinstance(item,str) else item)
        summary["key_information_gaps"]=normalized_gaps
    actions=summary.get("recommended_next_actions")
    if isinstance(actions,list):
        normalized_actions=[]
        for item in actions:
            if isinstance(item,str) and not item.strip():
                normalization["removed_empty_recommended_actions"]+=1
                continue
            normalized_actions.append(item.strip() if isinstance(item,str) else item)
        summary["recommended_next_actions"]=normalized_actions
    normalization["applied"]=bool(normalization["removed_empty_information_gaps"] or normalization["removed_empty_recommended_actions"])
    return summary,normalization


def build_source_records(docs: list[dict], candidates_by_url: dict[str,dict], protected: set[str]) -> list[dict]:
    """Build report-facing source records while preserving authoritative patent metadata."""
    records=[]
    for index,doc in enumerate(docs,1):
        candidate=candidates_by_url.get(doc["requested_url"],{})
        patent_title=(candidate.get("patent_title") or candidate.get("title_hint") or "").strip()
        retrieved_title=(doc.get("title") or "").strip()
        title=patent_title or retrieved_title if candidate.get("normalized_publication_number") else retrieved_title or patent_title
        records.append({
            "source_id":f"SRC-{index:04d}","url":candidate.get("report_canonical_url") or doc["url"],
            "title":title,"source_type":doc["source_type"],"retrieved_at":utc_now(),
            "content_hash":doc["content_hash"],
            "official":candidate.get("source_domain_class") in {"official_company","official_company_asset"},
            "source_domain_class":candidate.get("source_domain_class","third_party_analytics"),
            "protected_seed":doc["requested_url"] in protected,"retrieval_status":doc["parse_status"],
            "retrieval_error":doc["error"],"normalized_publication_number":candidate.get("normalized_publication_number"),
            "patent_application_number":candidate.get("patent_application_number"),
            "patent_title":patent_title,"patent_abstract":candidate.get("snippet","")})
    return records

class Pipeline:
    def __init__(self, root: Path, run_profile: str = "standard"):
        self.root = root
        self.cfg = root / "config"
        self.run_profile=run_profile

    @staticmethod
    def _progress(message: str) -> None:
        print(f"[BDA] {message}", flush=True)

    @http_scope
    async def _retrieve(self, urls: list[str]) -> list[dict]:
        cfg=load_search_config(self.root,self.run_profile)["retrieval"]
        urls=list(dict.fromkeys(urls))
        limits = httpx.Limits(max_connections=8, max_keepalive_connections=4)
        timeout = httpx.Timeout(20, connect=8)
        concurrency=int(cfg["download_concurrency"])
        patent_only = bool(urls) and all((urlparse(url).hostname or "").lower() in {"patents.google.com", "api.uspto.gov"} for url in urls)
        if patent_only:
            concurrency = 1
        progress_interval=int(cfg["progress_interval_documents"])
        maximum_bytes=int(cfg["max_download_bytes"])
        maximum_pdf_documents=int(cfg["maximum_pdf_documents"])
        maximum_pages_per_pdf=int(cfg["maximum_pages_per_pdf"])
        remaining_pdf_pages=int(cfg["maximum_total_parsed_pdf_pages"])
        parsed_pdf_documents=0
        results=[]
        self._progress(f"Retrieval started: {len(urls)} URLs; PDF budget {remaining_pdf_pages} total pages, {maximum_pages_per_pdf} pages per PDF, {maximum_pdf_documents} PDFs.")
        async with httpx.AsyncClient(follow_redirects=True, limits=limits, timeout=timeout, headers={"User-Agent":"BDA-NNC/2.0 (+evidence research)"}) as client:
            async def download(url: str) -> dict:
                delays = (0, 2, 5, 12) if (urlparse(url).hostname or "").lower() in {"patents.google.com", "api.uspto.gov"} else (0,)
                last_exc = None
                for delay in delays:
                    if delay: await asyncio.sleep(delay)
                    try:
                        request_headers = {"X-API-KEY": os.getenv("USPTO_API_KEY", "")} if (urlparse(url).hostname or "").lower() == "api.uspto.gov" else None
                        response=(await client.get(url, headers=request_headers)) if request_headers else (await client.get(url))
                        if getattr(response, "status_code", 200) in {429,500,502,503,504}: response.raise_for_status()
                        response.raise_for_status()
                        if len(response.content)>maximum_bytes: raise ValueError("download limit exceeded")
                        return {"requested_url":normalize_url(url),"response":response,"error":None}
                    except Exception as exc:
                        last_exc = exc
                        status = getattr(getattr(exc, "response", None), "status_code", None)
                        if status not in {429,500,502,503,504}: break
                return {"requested_url":normalize_url(url),"url":normalize_url(url),"error":type(last_exc).__name__,
                        "http_status":getattr(getattr(last_exc, "response", None), "status_code", None)}

            async def ordered_batches():
                if patent_only:
                    # Keep the established patent-only pacing, including sleep
                    # before parsing. Do not turn retries into parallel bursts.
                    for url in urls:
                        item = await download(url)
                        await asyncio.sleep(0.8)
                        yield [item]
                else:
                    async for item in ordered_downloads(urls, download, concurrency):
                        yield [item]

            async for downloaded in ordered_batches():
                for item in downloaded:
                    requested_url=item["requested_url"]
                    if item["error"]:
                        is_pdf=".pdf" in requested_url.lower()
                        result={"requested_url":requested_url,"url":requested_url,"title":"","text":"","pages":[],"source_type":"pdf" if is_pdf else "html","content_hash":"","parse_status":"parse_failed" if is_pdf else "retrieval_failed","error":item["error"],"available_page_count":0,"pages_skipped_by_budget":0}
                    else:
                        response=item["response"]
                        content_type=response.headers.get("content-type","").lower()
                        is_pdf=response.content.startswith(b"%PDF-") or "application/pdf" in content_type
                        if not is_pdf:
                            soup=BeautifulSoup(response.text,"html.parser"); content=soup.get_text(" ",strip=True)[:500_000]
                            result={"requested_url":requested_url,"url":normalize_url(str(response.url)),"title":soup.title.string.strip() if soup.title and soup.title.string else "","text":content,"pages":[{"page":None,"text":content}],"source_type":"html","content_hash":sha256_text(content),"parse_status":"retrieved","error":None,"available_page_count":1,"pages_skipped_by_budget":0}
                        else:
                            title=Path(str(response.url).split("?",1)[0]).name
                            try:
                                pdf=fitz.open(stream=response.content,filetype="pdf")
                                available=pdf.page_count
                                if parsed_pdf_documents>=maximum_pdf_documents:
                                    allowed=0; status="pdf_document_budget_excluded"
                                else:
                                    allowed=min(available,maximum_pages_per_pdf,remaining_pdf_pages)
                                    status="pdf_page_budget_excluded" if allowed==0 else "pdf_parsed"
                                try:
                                    pages=[{"page":index+1,"text":pdf[index].get_text("text")[:200_000]} for index in range(allowed)]
                                finally:
                                    pdf.close()
                                text_value=bounded_page_text(pages)
                                if allowed:
                                    parsed_pdf_documents+=1; remaining_pdf_pages-=allowed
                                    if not any(page["text"].strip() for page in pages): status="ocr_required"
                                    elif allowed<available: status="pdf_parsed_truncated"
                                result={"requested_url":requested_url,"url":normalize_url(str(response.url)),"title":title,"text":text_value,"pages":pages,"source_type":"pdf",**pdf_hashes(response.content),"parse_status":status,"error":None,"available_page_count":available,"pages_skipped_by_budget":available-allowed}
                            except Exception as exc:
                                result={"requested_url":requested_url,"url":normalize_url(str(response.url)),"title":title,"text":"","pages":[],"source_type":"pdf","content_hash":"","parse_status":"parse_failed","error":type(exc).__name__,"available_page_count":0,"pages_skipped_by_budget":0}
                    results.append(result)
                    completed=len(results)
                    if completed==len(urls) or completed%progress_interval==0:
                        self._progress(f"Retrieval progress: {completed}/{len(urls)} documents; {sum(len(x['pages']) for x in results if x['source_type']=='pdf')} PDF pages parsed; {remaining_pdf_pages} pages remain in budget.")
        self._progress("Retrieval and bounded PDF parsing completed.")
        return results

    def _extract(self, docs: list[dict]) -> tuple[list[dict], list[dict]]:
        """Compatibility helper for tests; production uses attributed extraction."""
        tax = load_yaml(self.cfg / "domains/tiny_edge_ai/company_domain_taxonomy.yaml")
        accepted, rejected = [], []
        next_id = 1
        for doc_no, doc in enumerate(docs, 1):
            if doc.get("error"): continue
            item = dict(doc, source_id=f"SRC-{doc_no:04d}")
            attribution={"scan_target_company_id":"test_company","attributed_company_id":"test_company","company_attribution_status":"established","mapping_eligible":True,"reason_codes":[]}
            result=extract_document_evidence(item,tax,attribution,next_id)
            accepted.extend(result["accepted"]); rejected.extend(result["rejected"]); next_id=result["next_evidence_id"]
        return accepted, rejected

    @portfolio_scope
    def run(self, company: str, official_domain: str, seed_urls: list[str] | None = None, *, country: str | None = None, company_aliases: list[str] | None = None, validated_source_assignees: list[str] | None = None, cycle_id: str | None = None, previous_score: int | None = None, deterministic_persisted_callback=None, provider_cycle_state=None) -> Path:
        self._progress(f"Stage 1/8 - Starting assessment for {company}.")
        index_preflight=validate_index(self.root)
        if not index_preflight["ready"]: raise RuntimeError("failed_portfolio_index_preflight")
        stamp, slug = run_timestamp(), slugify(company)
        directory_stamp = local_run_directory_timestamp()
        out = self.root / "output/companies" / slug / directory_stamp; out.mkdir(parents=True)
        self._progress("Stage 2/8 - Discovering and ranking candidate sources.")
        discovery = discover_sync(self.root, out, company, official_domain, seed_urls, provider_cycle_state, company_aliases,self.run_profile,validated_source_assignees)
        urls = [item["canonical_url"] for item in discovery["retrieval_candidates"]]
        self._progress(f"Discovery completed: {len(discovery['candidates'])} retained candidates; {len(urls)} selected for retrieval.")
        self._progress("Stage 3/8 - Downloading sources and parsing PDFs within configured budgets.")
        docs = asyncio.run(self._retrieve(urls))
        patent_manifest_path=out/"patent_full_text_manifest.json"
        if patent_manifest_path.exists():
            patent_manifest=json.loads(patent_manifest_path.read_text(encoding="utf-8"))
            docs_by_url={d["requested_url"]:d for d in docs}
            for selected_patent in patent_manifest.get("selected",[]):
                document=docs_by_url.get(normalize_url(selected_patent["patent_url"]))
                selected_patent["retrieval_status"]=document["parse_status"] if document else "not_selected_or_not_attempted"
                selected_patent["retrieval_error"]=document.get("error") if document else None
                selected_patent["full_text_retrieved"]=bool(document and not document.get("error") and document.get("text"))
            failed_slots=sum(not item.get("full_text_retrieved") for item in patent_manifest.get("selected",[]))
            if failed_slots:
                rankings_path=out/"patent_metadata_rankings.json"
                rankings=json.loads(rankings_path.read_text(encoding="utf-8")).get("rankings",[]) if rankings_path.exists() else []
                attempted_publications={item.get("publication_number") for item in patent_manifest.get("selected",[])}
                attempted_urls={d["requested_url"] for d in docs}
                replacement_limit=int(load_search_config(self.root,self.run_profile)["patent_discovery_budget"].get("maximum_replacement_patent_attempts",failed_slots))
                alternates=[record for record in sorted(rankings,key=lambda row:(
                    0 if row.get("source_provider")=="uspto_patent_file_wrapper" else 1,
                    -int(row.get("local_rank_score",0))))
                    if record.get("publication_number") not in attempted_publications
                    and normalize_url(record.get("patent_url","")) not in attempted_urls]
                recovered=attempts=0
                while alternates and recovered<failed_slots and attempts<replacement_limit:
                    batch=alternates[:min(5,replacement_limit-attempts)]; alternates=alternates[len(batch):]
                    replacement_docs=asyncio.run(self._retrieve([record["patent_url"] for record in batch]))
                    attempts+=len(batch); docs.extend(replacement_docs)
                    for record,document in zip(batch,replacement_docs):
                        success=bool(not document.get("error") and document.get("text"))
                        recovered+=int(success)
                        patent_manifest["selected"].append({
                            "publication_number":record.get("publication_number"),"patent_url":record.get("patent_url"),
                            "use_case_families":record.get("matched_use_case_families",[]),
                            "reservation_family":"replacement_after_full_text_failure",
                            "replacement_attempt":True,"retrieval_status":document.get("parse_status"),
                            "retrieval_error":document.get("error"),"full_text_retrieved":success})
                        discovery["candidates"].append({
                            "candidate_id":f"replacement_{record.get('publication_number')}",
                            "canonical_url":normalize_url(record["patent_url"]),"original_url":record["patent_url"],
                            "report_canonical_url":record.get("report_canonical_url") or record.get("patent_portal_url"),
                            "patent_application_number":record.get("application_number"),
                            "scan_target_company_id":slug.replace("-","_"),"attributed_company_id":None,
                            "company_attribution_status":"unverified","discovery_channel":"patent_native_replacement",
                            "provider_id":record.get("source_provider"),"source_domain_class":"specialist_patent_source",
                            "source_type_hint":"html","title_hint":record.get("title",""),"snippet":record.get("abstract",""),
                            "normalized_publication_number":record.get("publication_number"),
                            "official_patent_assignees":list(dict.fromkeys([*record.get("current_assignees",[]),*record.get("original_assignees",[])])),
                            "provenance":{"enumeration_assignee":record.get("enumeration_assignee"),"native_source_provider":record.get("source_provider")},
                            "retrieval_status":document.get("parse_status"),"protected_for_retrieval":False})
                patent_manifest["replacement_policy"]={"failed_initial_slots":failed_slots,"replacement_attempts":attempts,
                    "successful_replacements":recovered,"provider_preference":["uspto_patent_file_wrapper","google_patents","justia_patents"]}
            patent_manifest["status"]="completed"
            patent_manifest["completed_at"]=utc_now()
            atomic_json(patent_manifest_path,patent_manifest)
        protected={item["canonical_url"] for item in discovery["retrieval_candidates"] if item.get("protected_for_retrieval")}
        seed_results=[{"canonical_url":url,"registration_status":"registered","selected_for_retrieval":True,"retrieval_status":next((doc["parse_status"] for doc in docs if doc["requested_url"]==url),"not_attempted"),"retrieval_error":next((doc["error"] for doc in docs if doc["requested_url"]==url),None)} for url in sorted(protected)]
        atomic_json(out/"seed_retrieval_results.json",{"seeds_registered":discovery["seed_registration"]["seeds_registered"],"results":seed_results})
        failed_seed_retrievals=sum(item["retrieval_status"] in {"retrieval_failed","parse_failed","not_attempted"} for item in seed_results)
        if failed_seed_retrievals:
            discovery["report"].setdefault("degradation_flags",[]).append("explicit_seed_retrieval_partial")
            discovery["report"]["metrics"]["explicit_seed_retrieval_failures"]=failed_seed_retrievals
        by_url={item["canonical_url"]:item for item in discovery["candidates"]}
        sources=build_source_records(docs,by_url,protected)
        web_pdf_manifest={"page_budget":{"maximum_total_parsed_pdf_pages":load_search_config(self.root,self.run_profile)["retrieval"]["maximum_total_parsed_pdf_pages"],"parsed_pdf_pages":sum(len(d["pages"]) for d in docs if d["source_type"]=="pdf"),"pages_skipped_by_budget":sum(d.get("pages_skipped_by_budget",0) for d in docs if d["source_type"]=="pdf")},"documents":[{"url":d["url"],"filename":d["title"],"content_hash":d["content_hash"],"page_count":len(d["pages"]),"available_page_count":d.get("available_page_count",len(d["pages"])),"pages_skipped_by_budget":d.get("pages_skipped_by_budget",0),"status":d["parse_status"],"error":d["error"]} for d in docs if d["source_type"]=="pdf"]}
        pdf_docs=[d for d in docs if d["source_type"]=="pdf"]
        for record, document in zip(web_pdf_manifest["documents"], pdf_docs):
            record.update({key: document[key] for key in ("raw_content_hash", "content_hash_encoding") if key in document})
        atomic_json(out/"web_pdf_manifest.json",web_pdf_manifest)
        discovery["report"]["metrics"]["web_pdfs_downloaded"]=sum(1 for d in docs if d["source_type"]=="pdf" and not d["error"])
        discovery["report"]["metrics"]["web_pdfs_parsed"]=sum(1 for d in docs if d["parse_status"].startswith("pdf_parsed"))
        discovery["report"]["metrics"]["web_pdf_pages_parsed"]=web_pdf_manifest["page_budget"]["parsed_pdf_pages"]
        discovery["report"]["metrics"]["web_pdf_pages_skipped_by_budget"]=web_pdf_manifest["page_budget"]["pages_skipped_by_budget"]
        atomic_json(out/"source_discovery_report.json",discovery["report"])
        self._progress("Stage 4/8 - Establishing company attribution and extracting local NNC context bundles.")
        taxonomy=load_yaml(self.cfg/"domains/tiny_edge_ai/company_domain_taxonomy.yaml")
        attributions=[]; accepted=[]; rejected=[]; background=[]; context_bundles=[]; next_evidence_id=1
        for index,doc in enumerate(docs,1):
            doc["source_id"]=f"SRC-{index:04d}"
            candidate=by_url.get(doc["requested_url"],{})
            doc["source_category_hint"]=candidate.get("source_category_hint")
            doc["source_domain_class"]=candidate.get("source_domain_class","third_party_analytics")
            doc["normalized_publication_number"]=candidate.get("normalized_publication_number")
            doc["patent_application_number"]=candidate.get("patent_application_number")
            doc["patent_title"]=candidate.get("patent_title") or candidate.get("title_hint")
            doc["patent_abstract"]=candidate.get("snippet","")
            attribution=establish_document_company_attribution(
                doc,company=company,official_domain=official_domain,
                company_aliases=company_aliases,
                validated_source_assignees=discovery["profile"].get("validated_source_assignees", []),
                candidate=candidate,
            )
            attributions.append(attribution)
            if doc.get("error"): continue
            extracted=extract_document_evidence(doc,taxonomy,attribution,next_evidence_id)
            accepted.extend(extracted["accepted"]); rejected.extend(extracted["rejected"])
            background.extend(extracted["background"]); context_bundles.extend(extracted["context_bundles"])
            next_evidence_id=extracted["next_evidence_id"]
            if index==len(docs) or index%10==0:
                self._progress(f"Evidence progress: {index}/{len(docs)} documents; {len(accepted)} target-company facts; {len(context_bundles)} complete context bundles; {len(background)} background matches.")
        eligible_evidence=[e for e in accepted if e["mapping_eligibility"]["eligible"] and e["context_bundle_gate_status"]=="pass"]
        entity_ids = sorted({e["taxonomy_term_id"] for e in eligible_evidence})
        gates = evaluate_nnc_gates(set(entity_ids))
        self._progress("Stage 5/8 - Building deterministic applicability mappings and retrieving dSPACE grounding.")
        rules = load_yaml(self.cfg / "dspace_portfolio/applicability_mapping_rules.yaml")["mapping_rules"]
        portfolio_profiles=load_yaml(self.cfg/"dspace_portfolio/dspace_portfolio_profiles.yaml")["dspace_portfolio_items"]
        portfolio_by_id={profile["dspace_portfolio_item_id"]:profile for profile in portfolio_profiles}
        mappings=[]; assessed=[]; retrieval_records=[]
        portfolio_queries=[]
        for rule in rules:
            hits=sorted(set(rule["target_company_side"]["required_entity_ids"]) & set(entity_ids))
            if hits and gates["positive_applicability_candidate"]:
                item=rule["dspace_side"]["dspace_portfolio_item_id"]
                portfolio_queries.append("; ".join([*hits,*rule["neutral_need_side"]["engineering_need_ids"],*rule["dspace_side"]["required_capability_ids"],item]))
        prefetch_portfolio(self.root, portfolio_queries)
        for rule in rules:
            hits = sorted(set(rule["target_company_side"]["required_entity_ids"]) & set(entity_ids))
            item = rule["dspace_side"]["dspace_portfolio_item_id"]
            deterministic_candidate=bool(hits) and gates["positive_applicability_candidate"]
            score = min(100, 45 + 15*len(hits) + 10*len(rule["neutral_need_side"]["engineering_need_ids"])) if deterministic_candidate else 0
            selected=[]
            retrieval_id=f"ret_{len(retrieval_records)+1:04d}"
            if deterministic_candidate:
                query="; ".join([*hits,*rule["neutral_need_side"]["engineering_need_ids"],*rule["dspace_side"]["required_capability_ids"],item])
                record=retrieve(self.root,query,item,8); record["retrieval_query_id"]=retrieval_id
                retrieval_records.append(record)
                selected=[c for c in record["returned_chunks"] if c["selected"]]
            grounded=deterministic_candidate and bool(selected)
            assessed.append({"dspace_portfolio_item_id":item,"entity_scope":"dspace_portfolio","hard_rule_passed":grounded,"dspace_applicability_score":score if grounded else 0,"decision":"applicable" if grounded else "insufficient_dspace_portfolio_grounding" if deterministic_candidate else "rejected","retrieval_query_ids":[retrieval_id] if deterministic_candidate else [],"supporting_dspace_document_chunk_ids":[c["chunk_id"] for c in selected]})
            if grounded:
                profile=portfolio_by_id.get(item,{})
                commercial_name=profile.get("commercial_name")
                offering_type=profile.get("offering_type")
                if not commercial_name or not offering_type: raise RuntimeError(f"invalid dSPACE portfolio commercial profile: {item}")
                for target in hits:
                    target_records=[e for e in eligible_evidence if e["taxonomy_term_id"]==target]
                    ev = [e["evidence_id"] for e in target_records]
                    scored_record=max((e for e in target_records if e.get("nnc_use_case_scoring")),key=lambda e:e["nnc_use_case_scoring"]["use_case_score"],default={})
                    use_case_scoring=scored_record.get("nnc_use_case_scoring",{})
                    mapping_class=use_case_scoring.get("mapping_class") or "nnc_maximum_workflow_fit"
                    bundle_ids=sorted({bundle_id for e in target_records for bundle_id in e["context_bundle_ids"]})
                    for need in rule["neutral_need_side"]["engineering_need_ids"]:
                        chain=[target,need,rule["dspace_side"]["required_capability_ids"][0],item]
                        mappings.append({"mapping_id":f"MAP-{len(mappings)+1:04d}","mapping_chain":chain,"mapping_display":" -> ".join(chain),"target_company_entity_id":target,"engineering_need_id":need,"dspace_capability_id":rule["dspace_side"]["required_capability_ids"][0],"dspace_capability_ids":rule["dspace_side"]["required_capability_ids"],"dspace_portfolio_item_id":item,"dspace_commercial_name":commercial_name,"dspace_offering_type":offering_type,"target_company_evidence_ids":ev,"supporting_company_evidence_ids":ev,"context_bundle_ids":bundle_ids,"mapping_eligibility":{"eligible":True,"reason_codes":["complete_local_context_bundle"]},"supporting_dspace_document_chunk_ids":[c["chunk_id"] for c in selected],"retrieval_query_ids":[retrieval_id],"applicability_relations":rule.get("applicability_relations",["simulate","test","validate"]),"hard_rule_passed":True,"dspace_applicability_score":score,"dspace_source_references":[{"source_filename":c["source_filename"],"page_start":c["page_start"],"page_end":c["page_end"],"section":c["section"],"chunk_id":c["chunk_id"]} for c in selected]})
                        qualifier={"nnc_influence_opportunity":"Influence opportunity - edge target/workflow not yet public","nnc_deployment_fit":"Deployment fit - onboard execution confirmed","nnc_maximum_workflow_fit":"Maximum workflow fit - compatible handover/code-generation confirmed"}.get(mapping_class,mapping_class)
                        use_cases=scored_record.get("use_case_classes",[])
                        use_case_id=next((x for x in use_cases if x!="indirect_physical_state_and_virtual_sensing"),use_cases[0] if use_cases else target)
                        mappings[-1].update({"mapping_class":mapping_class,"nnc_use_case_scoring":use_case_scoring,"use_case_id":use_case_id,"mapping_display":mappings[-1]["mapping_display"]+f" - {qualifier}","dspace_applicability_score":use_case_scoring.get("use_case_score",score),"mapping_eligibility":{"eligible":True,"reason_codes":["v1_10_neural_application_mapping"] if use_case_scoring else ["complete_local_context_bundle"]}})
        if gates["positive_applicability_candidate"] and not mappings:
            grounding_failure={"status":"failed_portfolio_grounding","reason":"no grounded dSPACE portfolio recommendation","assessed_dspace_portfolio_items":assessed}
            atomic_json(out/f"{slug}_{stamp}_dspace_portfolio_assessment.json",grounding_failure)
            atomic_json(out/f"{slug}_{stamp}_retrieval_records.json",{"index_preflight":index_preflight,"retrieval_records":retrieval_records})
            raise RuntimeError("failed_portfolio_grounding")
        needs=sorted({m["engineering_need_id"] for m in mappings})
        company_assessment={"company_name":company,"company_slug":slug,"target_company_entities":[{"target_company_entity_id":x,"entity_scope":"target_company","evidence_ids":[e["evidence_id"] for e in eligible_evidence if e["taxonomy_term_id"]==x]} for x in entity_ids],"neutral_engineering_needs":[{"engineering_need_id":x,"entity_scope":"neutral_engineering_need","evidence_status":"inferred"} for x in needs],"semantic_gates":gates,"company_role":gates["company_role_gate"]["role"],"context_bundle_gate":{"passed":bool(context_bundles),"passed_bundle_ids":[b["context_bundle_id"] for b in context_bundles]},"company_attribution_summary":{"established_sources":sum(a["company_attribution_status"]=="established" for a in attributions),"not_established_sources":sum(a["company_attribution_status"]=="not_established" for a in attributions)},"information_gaps":[name for name,gate in (("neural network architecture",gates["neural_network_gate"]),("embedded MCU or ECU target",gates["embedded_target_gate"]),("model-to-software deployment workflow",gates["deployment_workflow_gate"])) if not gate["passed"]]}
        eligible=sorted((x["dspace_applicability_score"]/100 for x in assessed if x["hard_rule_passed"]),reverse=True)
        strongest=eligible[0] if eligible else 0.0; second=eligible[1] if len(eligible)>1 else 0.0
        evidence_quality=(sum(e["confidence"] for e in eligible_evidence)/len(eligible_evidence)) if eligible_evidence else 0.0
        detailed_mappings=list(mappings)
        relevant=build_relevant_evidence(accepted,sources,detailed_mappings)
        relevant_source_ids={item["source_id"] for item in relevant["relevant_evidence"]}
        company_scoring = aggregate_company_scores([item for item in accepted if item.get("source_id") in relevant_source_ids])
        legacy_rating, legacy_components = score_nnc_applicability(gates,evidence_quality)
        rating = company_scoring["overall_product_match"] if company_scoring["use_cases"] else legacy_rating
        score_components = {"v1_10_company_scoring": company_scoring, "legacy_fallback": legacy_components}
        unrounded=float(rating)
        rating_detail={"previous_excel_rating":previous_score,"strongest_dspace_portfolio_applicability_score":strongest,"second_dspace_portfolio_applicability_score":second,"evidence_quality_score":evidence_quality,"score_components":score_components,"use_case_scores":company_scoring["use_cases"],"opportunity_breadth_bonus":company_scoring["opportunity_breadth_bonus"],"deployment_readiness":{"included_in_overall_product_match":False},"commercial_toolchain_status":"unknown","unrounded_score":unrounded,"new_excel_rating":rating,"score_change":None if previous_score is None else rating-previous_score,"band":company_scoring["rating"] if company_scoring["use_cases"] else ("strong" if rating>=80 else "good" if rating>=60 else "moderate" if rating>=40 else "low" if rating>=20 else "no_fit")}
        final={"run_id":f"{slug}-{stamp}","cycle_id":cycle_id,"company_name":company,"domain_id":"tiny_edge_ai","portfolio_item_id":"neural_net_coder","company_role":gates["company_role_gate"]["role"],"semantic_gates":gates,"models":{"embedding_provider":"ollama","embedding_model":EMBEDDING_MODEL,"llm_provider":"ollama","llm_model":FINAL_REPORT_MODEL},"semantic_scopes":{"target_company":company_assessment["target_company_entities"],"neutral_engineering_need":company_assessment["neutral_engineering_needs"],"dspace_portfolio":assessed},"applicability_mappings":mappings,"overall_product_match":rating_detail,"overall_dspace_portfolio_applicability":rating,"llm_summary_status":"pending"}
        enrich_ownership(final,portfolio_profiles)
        final["target_company"]["official_domain"]=official_domain
        final["target_company"]["country"]=country or "Not specified"
        if relevant["source_count"]==0:
            rating=0
            rating_detail.update({"use_case_scores":[],"opportunity_breadth_bonus":0,"unrounded_score":0,
                                  "new_excel_rating":0,"score_change":None if previous_score is None else -previous_score,"band":"no_fit"})
            final["overall_product_match"]=rating_detail
            final["overall_dspace_portfolio_applicability"]=0
        mappings=consolidate_use_case_mappings(detailed_mappings,3) if relevant["source_count"] else []
        final["applicability_mappings"]=mappings
        final["search_coverage"]={"patents":discovery["report"].get("patent_search_coverage",{})}
        final["cycle_source_counts"]=calculate_cycle_source_counts(sources,relevant)
        self._progress(f"Mapping completed: {len(mappings)} mappings; {relevant['source_count']} Relevant Evidence sources; {relevant['background_source_count']} Company Background Evidence sources; provisional score {rating}/100.")
        final["report_data"]={"relevant_evidence_source_ids":[item["source_id"] for item in relevant["relevant_evidence"]],"relevant_evidence_count":relevant["source_count"],
            "company_background_evidence_source_ids":[item["source_id"] for item in relevant["company_background_evidence"]],"company_background_evidence_count":relevant["background_source_count"],
            "applicability_mapping_ids":[item["mapping_id"] for item in mappings],"applicability_mapping_count":len(mappings)}
        model_cfg=load_yaml(self.cfg/"runtime/models.yaml")
        try:
            prompt_bundle=load_prompt_bundle(self.root,FINAL_REPORT_MODEL)
            effective_prompt_manifest=prompt_bundle["effective_manifest"]
        except Exception as exc:
            prompt_bundle={"error":{"type":type(exc).__name__,"message":str(exc)}}
            effective_prompt_manifest={"prompt_bundle_id":"company_summary_v3.0","model":FINAL_REPORT_MODEL,"validation_result":"invalid","error":prompt_bundle["error"]}
        self._progress("Stage 6/8 - Building the bounded company-specific LLM context.")
        context_artifact=build_llm_context(final,relevant,retrieval_records,model_cfg["llm_context"])
        artifacts={"search_queries":{"queries":discovery["queries"]},"search_execution":{"executions":discovery["executions"]},"provider_results":{"results":discovery["provider_results"]},"candidate_sources":{"sources":discovery["candidates"]},"source_discovery_report":discovery["report"],"web_pdf_manifest":web_pdf_manifest,"company_sources":{"sources":sources},"company_attribution":{"attributions":attributions},"background_technology_evidence":{"evidence":background},"context_bundles":{"context_bundles":context_bundles},"evidence_records":{"accepted":accepted,"rejected":rejected},"relevant_evidence":relevant,"llm_summary_context":context_artifact,"effective_prompt_manifest":effective_prompt_manifest,"deduplication_report":{"unique":len(accepted),"duplicates":len(rejected)},"company_assessment":company_assessment,"retrieval_records":{"index_preflight":index_preflight,"retrieval_records":retrieval_records},"dspace_portfolio_assessment":{"assessed_dspace_portfolio_items":assessed},"applicability_mappings":{"mappings":mappings},"final_assessment":final}
        for name,value in artifacts.items(): atomic_json(out/f"{slug}_{stamp}_{name}.json",value)
        if deterministic_persisted_callback is not None:
            deterministic_persisted_callback(out, final)
        self._progress("Stage 7/8 - Attempting the optional local Gemma narrative.")
        context_artifact=self._summary_attempt(out,slug,stamp,final,context_artifact,model_cfg["models"]["final_report"],prompt_bundle,model_cfg["llm_context"])
        atomic_json(out/f"{slug}_{stamp}_llm_summary_context.json",context_artifact)
        final_flags=list(final.get("degradation_flags",[]))+discovery["report"].get("degradation_flags",[])
        if discovery["report"]["provider_errors"]: final_flags.append("provider_errors")
        final["degradation_flags"]=sorted(set(final_flags))
        final["execution_status"]="completed"
        final["quality_status"]="degraded" if final["degradation_flags"] else "clean"
        report_generated_at=datetime.now(timezone.utc).replace(microsecond=0)
        final["report_data"].update(report_identity(company,report_generated_at))
        atomic_json(out/f"{slug}_{stamp}_final_assessment.json",final)
        self._progress("Stage 8/8 - Rendering final Markdown/PDF reports and manifests.")
        report_path=render_reports(out, slug, stamp, final, relevant,report_generated_at)
        flags=list(final.get("degradation_flags",[]))
        if discovery["report"]["provider_errors"]: flags.append("provider_errors")
        flags.extend(discovery["report"].get("degradation_flags",[]))
        manifest={"run_id":final["run_id"],"cycle_id":cycle_id,"status":discovery["report"]["status"],"execution_status":"completed","quality_status":"degraded" if flags else "clean","degradation_flags":sorted(set(flags)),"application_version":"2.0.0","specification_version":SPECIFICATION_VERSION,"design_document_version":DESIGN_DOCUMENT_VERSION,"domain_id":"tiny_edge_ai","portfolio_item_id":"neural_net_coder","created_at":utc_now(),"accepted_evidence_count":len(accepted),"rejected_evidence_count":len(rejected),"background_evidence_count":len(background),"company_background_evidence_count":relevant["background_source_count"],"established_company_source_count":sum(a["company_attribution_status"]=="established" for a in attributions),"passed_context_bundle_count":len(context_bundles),"relevant_evidence_count":relevant["source_count"],"applicability_mapping_count":len(mappings),"cycle_source_counts":final["cycle_source_counts"],"report_filename":report_path.name,"report_generated_at":final["report_data"]["report_generated_at"],"prompt_bundle_id":effective_prompt_manifest.get("prompt_bundle_id"),"prompt_assets":effective_prompt_manifest.get("assets",{}),"llm_context_metrics":context_artifact["metrics"],"search_execution_summary":discovery["report"]["metrics"],"search_provider_errors":discovery["report"]["provider_errors"],"previous_score":previous_score,"newly_calculated_score":rating,"score_change":rating-previous_score if previous_score is not None else None,"overall_opportunity_score":rating,"embedding_provider":"ollama","embedding_model":EMBEDDING_MODEL,"llm_provider":"ollama","llm_model":FINAL_REPORT_MODEL,"llm_summary_status":final["llm_summary_status"],"narrative_source":final["narrative_source"],"llm_fallback_used":final["llm_fallback_used"],"llm_failure_code":final.get("llm_failure_code"),"run_directory":str(out)}
        atomic_json(out/f"{slug}_{stamp}_run_manifest.json",manifest)
        with (self.root/"output/run_registry.jsonl").open("a",encoding="utf-8") as f: f.write(json.dumps(manifest,separators=(",",":"))+"\n")
        self._progress(f"Completed {company}. Report: {report_path.name}")
        return out

    def _summary_attempt(self, out: Path, slug: str, stamp: str, final: dict, context_artifact:dict, cfg:dict, prompt_bundle:dict|None=None, context_limits:dict|None=None) -> dict:
        status="failed_unavailable"; summary=None; raw_response=""; runtime_metadata={}
        prewarm_status="not_attempted"
        narrative_validation={"overall_status":"fallback_used","structural_validation":{"status":"not_run","failure_code":None},"truncation_validation":{"status":"not_confirmed","failure_code":None},"ownership_validation":{"status":"not_run","failure_code":None,"violations":[]},"fallback_used":True,"narrative_source":"deterministic_template"}
        product_match=final.get("overall_product_match",{})
        scored_use_cases=product_match.get("use_case_scores",[])
        use_case_scoring_present="use_case_scores" in product_match
        relevant_count=int(final.get("report_data",{}).get("relevant_evidence_count",0))
        if relevant_count==0 or (use_case_scoring_present and not scored_use_cases):
            status="skipped_no_scored_evidence"; failure_code="no_scored_use_case_evidence"
            summary={"executive_summary":f"The deterministic assessment found no scored Neural Net Coder use cases for {final['company_name']}. No company-specific Relevant Evidence passed all attribution and technical decision gates, so no product-fit narrative or unsupported application claim is generated.",
                "overall_assessment":f"The deterministic assessment found no scored Neural Net Coder use cases for {final['company_name']}. No company-specific Relevant Evidence passed all attribution and technical decision gates, so no product-fit narrative or unsupported application claim is generated.",
                "key_information_gaps":["No qualified company-specific neural application evidence passed the complete decision pipeline."],
                "recommended_next_actions":["Review patent retrieval and attribution failures before reassessing product fit."],
                "next_actions":["Review patent retrieval and attribution failures before reassessing product fit."]}
            narrative_validation={"overall_status":"skipped_no_scored_evidence","structural_validation":{"status":"deterministic_guard","failure_code":failure_code},"truncation_validation":{"status":"not_applicable","failure_code":None},"ownership_validation":{"status":"not_run","failure_code":None,"violations":[]},"fallback_used":True,"narrative_source":"deterministic_template"}
            (out/f"{slug}_{stamp}_llm_raw_response.txt").write_text("",encoding="utf-8")
            atomic_json(out/f"{slug}_{stamp}_llm_response_metadata.json",{"configured_max_output_tokens":cfg["max_output_tokens"],"response_characters":0,"skip_reason":failure_code})
            final.update({"llm_summary_status":status,"llm_prewarm_status":"not_attempted","narrative_source":"deterministic_template","llm_fallback_used":True,"llm_failure_code":failure_code,"degradation_flags":["llm_fallback_used",failure_code],"narrative":summary})
            atomic_json(out/f"{slug}_{stamp}_narrative_validation.json",narrative_validation)
            atomic_json(out/f"{slug}_{stamp}_final_assessment.json",final)
            return context_artifact
        try:
            if not prompt_bundle or prompt_bundle.get("error"):
                raise PromptBundleError("llm_prompt_bundle_invalid")
            if context_limits is not None:
                try:
                    context_artifact=fit_complete_prompt(context_artifact,prompt_bundle,context_limits)
                except ValueError as exc:
                    context_artifact.setdefault("metrics",{}).update({"prompt_budget_satisfied":False,"prompt_budget_failure":str(exc)})
                    raise RuntimeError("llm_prompt_budget_exceeded") from exc
            if cfg.get("prewarm_model"):
                try:
                    warm=local_model_post("http://127.0.0.1:11434/api/generate",json={"model":FINAL_REPORT_MODEL,"prompt":"","stream":False,"keep_alive":cfg["keep_alive"],"options":{"num_predict":1,"num_ctx":cfg.get("num_ctx",8192)}},timeout=90); warm.raise_for_status(); prewarm_status="completed"
                except Exception as exc: prewarm_status=f"failed:{type(exc).__name__}"
            timer=threading.Timer(cfg["soft_timeout_warning_seconds"],lambda:log.warning("gemma2:9b summary exceeded soft timeout of %s seconds; continuing to hard timeout",cfg["soft_timeout_warning_seconds"]))
            timer.daemon=True; timer.start()
            try:
                prompt=build_effective_prompt(prompt_bundle,context_artifact["context"])
                if "num_ctx" in cfg and context_artifact.get("metrics",{}).get("prompt_budget_satisfied") is not True:
                    raise ValueError("llm_prompt_budget_not_validated")
                payload={"model":FINAL_REPORT_MODEL,"stream":False,"format":"json","keep_alive":cfg["keep_alive"],"options":{"temperature":cfg["temperature"],"num_predict":cfg["max_output_tokens"],"num_ctx":cfg.get("num_ctx",8192)},"prompt":prompt}
                r=local_model_post("http://127.0.0.1:11434/api/generate",json=payload,timeout=cfg["timeout_seconds"]); r.raise_for_status()
            finally: timer.cancel()
            response_body=r.json(); raw_response=str(response_body.get("response",""))
            runtime_metadata={key:response_body.get(key) for key in ("model","created_at","done","done_reason","total_duration","load_duration","prompt_eval_count","prompt_eval_duration","eval_count","eval_duration")}
            runtime_metadata.update({"configured_max_output_tokens":cfg["max_output_tokens"],"response_characters":len(raw_response)})
            (out/f"{slug}_{stamp}_llm_raw_response.txt").write_text(raw_response,encoding="utf-8")
            atomic_json(out/f"{slug}_{stamp}_llm_response_metadata.json",runtime_metadata)
            truncation=detect_truncation(raw_response,runtime_metadata,cfg["max_output_tokens"])
            if truncation["status"]=="truncated":
                narrative_validation.update({"structural_validation":{"status":"not_run_due_to_truncation","failure_code":None},"truncation_validation":truncation,"ownership_validation":{"status":"not_run_due_to_truncation","failure_code":None,"violations":[]}})
                raise ValueError("llm_output_truncated")
            try:
                summary=parse_json_without_repair(raw_response)
            except json.JSONDecodeError as exc:
                narrative_validation.update({"structural_validation":{"status":"invalid_json","failure_code":"llm_invalid_json","parse_error":str(exc)},"ownership_validation":{"status":"not_run_due_to_invalid_json","failure_code":None,"violations":[]}})
                raise
            summary,normalization=normalize_llm_list_fields(summary)
            try:
                jsonschema.validate(summary,prompt_bundle["output_schema"])
                if len(raw_response)>cfg["maximum_serialized_response_characters"]:
                    raise jsonschema.ValidationError("serialized response exceeds configured character limit")
                if not 100<=len(summary["overall_assessment"].split())<=300:
                    raise jsonschema.ValidationError("overall_assessment must contain 100 to 300 words")
                if any(len(item.split())>25 for item in summary["key_information_gaps"]):
                    raise jsonschema.ValidationError("information gaps must contain at most 25 words")
                if any(len(item.split())>30 for item in summary["recommended_next_actions"]):
                    raise jsonschema.ValidationError("actions must contain at most 30 words")
            except jsonschema.ValidationError as exc:
                narrative_validation.update({"structural_validation":{"status":"invalid_schema","failure_code":"llm_invalid_schema","schema_error":exc.message},"ownership_validation":{"status":"not_run_due_to_invalid_schema","failure_code":None,"violations":[]},"response_normalization":normalization})
                raise
            portfolio_items=[item for item in final["semantic_scopes"]["dspace_portfolio"] if item.get("hard_rule_passed")]
            ownership=validate_narrative_ownership(summary,final["company_name"],[],portfolio_items,cfg["ownership_validation"]["first_mention_attribution_window_characters"])
            narrative_validation={"overall_status":"valid","structural_validation":{"status":"valid","failure_code":None},"truncation_validation":truncation,"ownership_validation":ownership,"response_normalization":normalization,"fallback_used":False,"narrative_source":FINAL_REPORT_MODEL}
            if ownership["status"]!="valid":
                narrative_validation.update({"overall_status":"fallback_used","fallback_used":True,"narrative_source":"deterministic_template"})
                raise ValueError(ownership["failure_code"])
            summary["executive_summary"]=summary["overall_assessment"]
            summary["next_actions"]=list(summary.get("recommended_next_actions",[]))
            status="valid"
        except Exception as exc:
            status="skipped_prompt_budget" if str(exc)=="llm_prompt_budget_exceeded" else "timeout" if isinstance(exc,httpx.ReadTimeout) else "http_error" if isinstance(exc,httpx.HTTPStatusError) else "unavailable" if isinstance(exc,httpx.RequestError) else "invalid_response"
            if str(exc)=="llm_prompt_budget_exceeded": failure_code="llm_prompt_budget_exceeded"
            elif str(exc)=="llm_output_truncated": failure_code="llm_output_truncated"
            elif isinstance(exc,json.JSONDecodeError): failure_code="llm_invalid_json"
            elif isinstance(exc,jsonschema.ValidationError): failure_code="llm_invalid_schema"
            elif isinstance(exc,PromptBundleError): failure_code="llm_prompt_bundle_invalid"
            else: failure_code=narrative_validation.get("ownership_validation",{}).get("failure_code")
            failure={"type":type(exc).__name__,"message":str(exc),"failure_code":failure_code}
            if isinstance(exc,httpx.HTTPStatusError): failure.update({"http_status":exc.response.status_code,"response_body":exc.response.text[:1000]})
            grounded=list(dict.fromkeys(mapping["dspace_commercial_name"] for mapping in final["applicability_mappings"]))
            summary={"executive_summary":f"Deterministic assessment completed with applicability rating {final['overall_dspace_portfolio_applicability']}/100. Grounded dSPACE recommendations: {', '.join(name+' from dSPACE' for name in grounded)}. These dSPACE offerings are applicable to {final['company_name']}'s engineering needs. The assessment used {final['report_data']['relevant_evidence_count']} relevant target-company sources and {final['report_data']['applicability_mapping_count']} grounded applicability mappings. The optional {FINAL_REPORT_MODEL} narrative status was {status}; deterministic scoring, BGE-Large retrieval, dSPACE grounding, and report generation completed independently of the Local LLM.","next_actions":["Review evidence and qualification questions before outreach."],"failure":failure}
            if narrative_validation["structural_validation"]["status"]=="not_run":
                narrative_validation["structural_validation"]={"status":"skipped_prompt_budget" if failure_code=="llm_prompt_budget_exceeded" else "not_run_due_to_runtime_failure","failure_code":failure_code}
            if failure_code=="llm_prompt_budget_exceeded":
                narrative_validation["overall_status"]="skipped_prompt_budget"
        if not (out/f"{slug}_{stamp}_llm_raw_response.txt").exists():
            (out/f"{slug}_{stamp}_llm_raw_response.txt").write_text(raw_response,encoding="utf-8")
            metadata=runtime_metadata|{"configured_max_output_tokens":cfg["max_output_tokens"],"response_characters":len(raw_response)}
            if failure_code=="llm_prompt_budget_exceeded": metadata["skip_reason"]=failure_code
            atomic_json(out/f"{slug}_{stamp}_llm_response_metadata.json",metadata)
        final["llm_summary_status"]=status; final["llm_prewarm_status"]=prewarm_status; final["narrative_source"]=FINAL_REPORT_MODEL if status=="valid" else "deterministic_template"; final["llm_fallback_used"]=status!="valid"; final["llm_failure_code"]=None if status=="valid" else failure_code; final["degradation_flags"]=[] if status=="valid" else ["llm_fallback_used",failure_code] if failure_code else ["llm_fallback_used"]; final["narrative"]=summary
        atomic_json(out/f"{slug}_{stamp}_narrative_validation.json",narrative_validation)
        atomic_json(out/f"{slug}_{stamp}_final_assessment.json",final)
        return context_artifact

