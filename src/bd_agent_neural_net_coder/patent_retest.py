"""Fast patent-only company retest: no ordinary web discovery, LLM, or report."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .company_attribution import establish_document_company_attribution
from .config_manager import load_yaml
from .core import atomic_json, normalize_url, run_timestamp, slugify, utc_now
from .evidence_context import extract_document_evidence
from .patent_native_discovery import PatentNativeDiscovery
from .pipeline import Pipeline
from .relevant_evidence_builder import build_relevant_evidence
from .nnc_scoring import aggregate_company_scores
from .search_orchestrator import load_company_profile


def run_patent_retest(root: Path, company_record: dict) -> Path:
    company = company_record["company_name"]
    domain = company_record["company_domain"]
    aliases = company_record.get("other_names", [])
    out = root / "output/patent_retests" / slugify(company) / run_timestamp()
    out.mkdir(parents=True, exist_ok=False)
    config = load_yaml(root / "config/search_providers.yaml")
    profile = load_company_profile(root, company, domain, company_aliases=aliases,
        validated_source_assignees=company_record.get("validated_source_assignees",[]))
    print(f"[BDA] Patent retest 1/5 - Enumerating native patent metadata for {company}.", flush=True)
    native = asyncio.run(PatentNativeDiscovery(config).run(profile, out))
    selected = native["selected"]
    print(f"[BDA] Patent retest 2/5 - Ranked {len(native['ranked'])} records; selected {len(selected)} full patents.", flush=True)
    urls = [record["patent_url"] for record in selected]
    print("[BDA] Patent retest 3/5 - Retrieving selected patent full text.", flush=True)
    docs = asyncio.run(Pipeline(root)._retrieve(urls))
    docs_by_url = {doc["requested_url"]: doc for doc in docs}
    manifest_path = out / "patent_full_text_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest.get("selected", []):
        doc = docs_by_url.get(normalize_url(item["patent_url"]))
        item["retrieval_status"] = doc["parse_status"] if doc else "not_attempted"
        item["retrieval_error"] = doc.get("error") if doc else None
        item["full_text_retrieved"] = bool(doc and not doc.get("error") and doc.get("text"))
    manifest.update({"status": "completed", "completed_at": utc_now()})
    atomic_json(manifest_path, manifest)
    print("[BDA] Patent retest 4/5 - Applying company attribution and evidence classification.", flush=True)
    taxonomy = load_yaml(root / "config/domains/tiny_edge_ai/company_domain_taxonomy.yaml")
    selected_by_url = {normalize_url(record["patent_url"]): record for record in selected}
    attributions = []; accepted = []; rejected = []; background = []; sources = []; next_id = 1
    for index, doc in enumerate(docs, 1):
        source_id = f"SRC-{index:04d}"; doc["source_id"] = source_id
        metadata = selected_by_url.get(doc["requested_url"], {})
        candidate = {"source_domain_class": "specialist_patent_source", "source_category_hint": "target_company_patent",
                     "normalized_publication_number": metadata.get("publication_number"),
                     "official_patent_assignees": metadata.get("current_assignees", [])}
        # Preserve patent-native identity after the USPTO API redirects to a
        # signed data.uspto.gov XML URL. Evidence classification must not infer
        # source type solely from the final transport URL.
        doc.update({
            "source_category_hint": candidate["source_category_hint"],
            "normalized_publication_number": candidate["normalized_publication_number"],
            "official_patent_assignees": candidate["official_patent_assignees"],
            "retrieved_url": doc.get("url"),
            "url": normalize_url(metadata.get("patent_url") or doc.get("requested_url") or doc.get("url", "")),
            "title": metadata.get("title") or doc.get("title", ""),
        })
        attribution = establish_document_company_attribution(doc, company=company, official_domain=domain,
            company_aliases=aliases, validated_source_assignees=profile.get("validated_source_assignees", []), candidate=candidate)
        attributions.append(attribution)
        sources.append({"source_id": source_id, "url": doc["url"], "title": doc.get("title", ""),
            "source_type": doc["source_type"], "retrieved_at": utc_now(), "content_hash": doc.get("content_hash", ""),
            "source_domain_class": "specialist_patent_source", "retrieval_status": doc["parse_status"],
            "retrieval_error": doc.get("error"), "normalized_publication_number": metadata.get("publication_number"),
            "patent_application_number":metadata.get("application_number"),
            "patent_title":metadata.get("title", ""), "patent_abstract":metadata.get("abstract", "")})
        if doc.get("error"): continue
        extracted = extract_document_evidence(doc, taxonomy, attribution, next_id)
        accepted.extend(extracted["accepted"]); rejected.extend(extracted["rejected"])
        background.extend(extracted["background"]); next_id = extracted["next_evidence_id"]
    relevant = build_relevant_evidence(accepted, sources, [])
    company_scoring = aggregate_company_scores(accepted)
    relevant_source_ids = {item["source_id"] for item in relevant["relevant_evidence"]}
    outcomes = []
    for record in selected:
        url = normalize_url(record["patent_url"]); doc = docs_by_url.get(url)
        attr = next((a for a in attributions if normalize_url(a.get("source_url", "")) == normalize_url(doc.get("url", ""))), None) if doc else None
        outcomes.append({"publication_number": record.get("publication_number"), "patent_url": url,
            "use_case_families": record.get("matched_use_case_families", []), "local_rank_score": record.get("local_rank_score"),
            "retrieval_status": doc.get("parse_status") if doc else "not_attempted",
            "company_attribution_status": attr.get("company_attribution_status") if attr else "not_evaluated",
            "relevant_evidence": bool(doc and doc.get("source_id") in relevant_source_ids),
            "mapping_eligible": bool((best := max((e for e in accepted if e.get("source_id") == (doc or {}).get("source_id") and e.get("nnc_use_case_scoring")), key=lambda e: e["nnc_use_case_scoring"]["use_case_score"], default={})).get("nnc_use_case_scoring", {}).get("mapping_eligible", False)),
            "mapping_class": best.get("nnc_use_case_scoring", {}).get("mapping_class"),
            "score_contribution": best.get("nnc_use_case_scoring", {}).get("use_case_score", 0),
            "relevance_band": best.get("nnc_use_case_scoring", {}).get("relevance_band")})
    atomic_json(out / "patent_company_attribution.json", {"records": attributions})
    atomic_json(out / "patent_evidence_records.json", {"accepted": accepted, "rejected": rejected, "background": background})
    atomic_json(out / "patent_relevant_evidence.json", relevant)
    summary = {"status": "completed" if native["status"] == "completed" else "completed_degraded",
        "company": company, "started_from_validated_assignees": profile.get("validated_patent_assignees", []),
        "metadata_record_count": len(native["records"]), "ranked_record_count": len(native["ranked"]),
        "selected_full_patent_count": len(selected), "retrieved_full_patent_count": sum(not doc.get("error") for doc in docs),
        "relevant_evidence_count": relevant["source_count"], "outcomes": outcomes,
        "company_scoring": company_scoring, "overall_product_match": company_scoring["overall_product_match"],
        "overall_rating": company_scoring["rating"], "completed_at": utc_now(),
        "run_directory": str(out)}
    atomic_json(out / "patent_retest_summary.json", summary)
    print(f"[BDA] Patent retest 5/5 - Completed with {relevant['source_count']} Relevant Evidence patents.", flush=True)
    return out
