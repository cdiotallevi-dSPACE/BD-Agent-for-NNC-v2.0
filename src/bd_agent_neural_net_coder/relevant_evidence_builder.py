from __future__ import annotations

import re
from collections import defaultdict

from .core import normalize_url

DOMAIN_ORDER = {"official_company": 0, "official_company_asset": 1, "related_corporate": 2,
                "partner_hosted": 3, "specialist_patent_source": 4, "third_party_analytics": 5}


def _stable_report_url(source: dict, patent: bool) -> str:
    url=str(source.get("url") or "")
    if not patent:
        return normalize_url(url)
    application=re.sub(r"\D","",str(source.get("patent_application_number") or ""))
    publication=re.sub(r"[^A-Za-z0-9]","",str(source.get("normalized_publication_number") or "")).upper()
    if application:
        return f"https://data.uspto.gov/patent-file-wrapper/search/details/{application}/application-data"
    if publication:
        return f"https://patents.google.com/patent/{publication}/en"
    # Never expose expiring transport credentials in a published report.
    if any(token in url.casefold() for token in ("signature=","key-pair-id=","expires=")):
        return "https://data.uspto.gov/patent-file-wrapper/search"
    return normalize_url(url)


def _sentence_excerpt(value: str, limit: int = 360) -> str:
    """Return a readable excerpt without leading or trailing sentence fragments."""
    text = re.sub(r"\s+", " ", value).strip()
    if not text:
        return ""
    if text[0].islower():
        boundary=re.search(r"[.!?](?:[\"')\]]*)\s+(?=[A-Z0-9\"'(])",text[:200])
        if boundary:
            text=text[boundary.end():].strip()
        else:
            return ""
    if len(text)<=limit:
        return text
    bounded=text[:limit]
    endings=list(re.finditer(r"[.!?](?:[\"')\]]*)(?=\s|$)",bounded))
    if endings:
        return bounded[:endings[-1].end()].strip()
    # If no sentence boundary is available, preserve the complete statement;
    # a long cell is preferable to a misleading mid-claim ellipsis.
    return text


def _patent_description(source: dict, items: list[dict], suffix: str) -> str:
    publication=(source.get("normalized_publication_number") or "").strip()
    title=(source.get("patent_title") or source.get("title") or "Untitled patent").strip()
    title=re.sub(r"\s+-\s+Google Patents\s*$","",title,flags=re.I)
    abstract=_sentence_excerpt(source.get("patent_abstract") or "")
    claims_context=_sentence_excerpt(" ".join(item.get("passage","") for item in items))
    summary=abstract or claims_context or "The qualified patent evidence passed the company-attribution and NNC relevance gates."
    identity="Patent"+(f" {publication}" if publication else "")+f" — {title.rstrip('.')}"
    return f"{identity}. {summary}{suffix}".strip()


def build_relevant_evidence(accepted: list[dict], sources: list[dict], mappings: list[dict]) -> dict:
    applicable_ids = {evidence_id for mapping in mappings for evidence_id in mapping.get("supporting_company_evidence_ids", [])}
    qualified = [e for e in accepted
                if (e.get("evidence_id") in applicable_ids or e.get("relevance_class") in {"nnc_applicability_evidence", "nnc_opportunity_evidence"})
                and e.get("assessment") == "accepted"
                and e.get("company_attribution_status", "established") == "established"
                and ("scan_target_company_id" not in e or e.get("attributed_company_id") == e.get("scan_target_company_id"))
                and (e.get("mapping_eligibility", {"eligible": True}).get("eligible") is True or
                     (e.get("relevance_class") == "nnc_opportunity_evidence" and e.get("opportunity_evidence_gate_status") == "pass"))
                and (e.get("context_bundle_gate_status", "pass") == "pass" or e.get("relevance_class") == "nnc_opportunity_evidence")
                and e.get("relevant_evidence_eligible", True) is True]
    source_by_id = {source["source_id"]: source for source in sources}
    qualified_ids={e["evidence_id"] for e in qualified}
    attributed = [e for e in accepted
                  if e.get("assessment") == "accepted"
                  and e.get("company_attribution_status", "established") == "established"
                  and ("scan_target_company_id" not in e or e.get("attributed_company_id") == e.get("scan_target_company_id"))]
    grouped = defaultdict(list)
    for evidence in attributed:
        source = source_by_id.get(evidence.get("source_id"))
        if source and source.get("source_type") in {"html", "pdf"} and source.get("url"):
            report_url=_stable_report_url(source,bool(evidence.get("patent_analysis")))
            grouped[(report_url, source.get("content_hash") if source.get("source_type") == "pdf" else None)].append(evidence)
    records = []
    for (url, document_hash), items in grouped.items():
        qualified_items=[item for item in items if item.get("evidence_id") in qualified_ids]
        source_is_qualified=bool(qualified_items)
        items=qualified_items or items
        source = source_by_id[items[0]["source_id"]]
        pages = sorted({item.get("source_page") for item in items if item.get("source_page") is not None})
        title = (source.get("title") or "").strip()
        page_text = (("; pages " if title else "pages ") + ", ".join(map(str, pages))) if pages else ""
        excerpt = _sentence_excerpt(" ".join(item.get("passage", "") for item in items))
        opportunity = all(item.get("relevance_class") == "nnc_opportunity_evidence" for item in items)
        patent_items = [item for item in items if item.get("patent_analysis")]
        patent_analysis = (max(patent_items, key=lambda x: int((x.get("nnc_use_case_scoring") or {}).get("use_case_score", 0))).get("patent_analysis")
                           if patent_items else None)
        scoring_items = [item for item in items if item.get("nnc_use_case_scoring")]
        use_case_scoring = (max(scoring_items, key=lambda x: int(x["nnc_use_case_scoring"]["use_case_score"]))["nnc_use_case_scoring"]
                            if scoring_items else None)
        prefix = "Opportunity evidence — " if opportunity else ""
        suffix = (" Neural/embedded details are patent embodiments; ONNX and generated-code workflow are unconfirmed."
                  if opportunity and patent_analysis else (" Neural architecture and embedded execution are not disclosed." if opportunity else ""))
        if patent_analysis:
            description=(prefix+_patent_description(source,items,suffix)).strip()
            title=(source.get("patent_title") or title or "Untitled patent").strip()
        else:
            description=(prefix+title+page_text+(": " if title or pages else "")+excerpt+suffix).strip()
        linked = [mapping for mapping in mappings if set(mapping.get("supporting_company_evidence_ids", [])) & {item["evidence_id"] for item in items}]
        records.append({
            "source_id": source["source_id"], "canonical_url": url, "source_type": source["source_type"],
            "source_title": title, "description": description,
            "relevance_class": "nnc_opportunity_evidence" if opportunity else "nnc_applicability_evidence",
            "source_category": next((item.get("source_category") for item in items if item.get("source_category") != "unclassified"), "unclassified"),
            "use_case_classes": sorted({value for item in items for value in item.get("use_case_classes", [])}),
            "patent_neural_evidence_strength": patent_analysis.get("patent_neural_evidence_strength") if patent_analysis else None,
            "patent_analysis": patent_analysis, "mapping_eligible": bool(use_case_scoring and use_case_scoring.get("mapping_eligible")) or not opportunity,
            "mapping_class": use_case_scoring.get("mapping_class") if use_case_scoring else None,
            "nnc_use_case_scoring": use_case_scoring,
            "product_fit_score_contribution": use_case_scoring.get("use_case_score", 0) if use_case_scoring else (0 if opportunity else "eligible"),
            "uncertainty_disclosure": {"neural_model_status": patent_analysis.get("neural_model_status", "unconfirmed") if patent_analysis else "unconfirmed", "embedded_execution_status": patent_analysis.get("onboard_context", "unconfirmed") if patent_analysis else "unconfirmed", "onnx_status": "unconfirmed"} if opportunity else None,
            "accepted_evidence_ids": sorted(item["evidence_id"] for item in items),
            "linked_company_entity_ids": sorted({item["taxonomy_term_id"] for item in items}),
            "linked_engineering_need_ids": sorted({mapping["engineering_need_id"] for mapping in linked}),
            "linked_applicability_mapping_ids": sorted(mapping["mapping_id"] for mapping in linked),
            "document_hash": document_hash, "source_domain_class": source.get("source_domain_class", "third_party_analytics"),
            "_source_is_qualified": source_is_qualified,
        })
    records.sort(key=lambda item: (DOMAIN_ORDER.get(item["source_domain_class"], 99), item["canonical_url"]))
    relevant_records=[]; background_records=[]
    for item in records:
        scoring=item.get("nnc_use_case_scoring") or {}
        score_eligible=scoring.get("score_eligible",int(scoring.get("use_case_score",0)) > 0)
        source_is_qualified=bool(item.pop("_source_is_qualified",False))
        has_scored_use_case=bool(score_eligible is True and int(scoring.get("use_case_score",0)) > 0)
        # Legacy accepted mappings may predate v1.10 scoring metadata. Keep those
        # traceable as Relevant Evidence; the final report source-set invariant
        # still prevents an unscored source from leaking into a published run.
        has_legacy_mapping=bool(item.get("linked_applicability_mapping_ids") and not scoring)
        precise_use_case=bool(source_is_qualified and (has_scored_use_case or has_legacy_mapping))
        (relevant_records if precise_use_case else background_records).append(item)
    for number, item in enumerate(relevant_records, 1):
        item["display_number"] = number
    for number, item in enumerate(background_records, 1):
        item["display_number"] = number
        scoring=item.get("nnc_use_case_scoring") or {}
        item["background_reason_code"]=(scoring.get("score_exclusion_reason") or "no_precise_scored_use_case_link")
    return {"schema_version": "1.10.0", "relevant_evidence": relevant_records,
            "company_background_evidence": background_records,
            "source_count": len(relevant_records), "background_source_count": len(background_records),
            "approved_source_count": len(records)}
