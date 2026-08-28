from __future__ import annotations

import re


NARRATIVE_KEYS = {
    "executive_summary", "overall_assessment", "overall_opportunity", "technology_and_engineering_context",
    "explanation", "assessment", "closing_assessment", "action", "objective",
}


def _narrative_fields(value, path="response"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in NARRATIVE_KEYS and isinstance(child, str):
                found.append((child_path, child))
            else:
                found.extend(_narrative_fields(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_narrative_fields(child, f"{path}[{index}]"))
    return found


def validate_narrative_ownership(
    response: dict, target_company_name: str, target_company_aliases: list[str],
    portfolio_items: list[dict], attribution_window: int = 100,
) -> dict:
    violations = []
    fields = _narrative_fields(response)
    joined = "\n".join(text for _, text in fields)
    companies = sorted({target_company_name, *target_company_aliases}, key=len, reverse=True)
    supplier_verbs = r"(?:owns|offers|provides|supplies|sells)"
    for item in portfolio_items:
        if item.get("owner") != "dSPACE GmbH" or item.get("supplier") != "dSPACE GmbH":
            violations.append({"rule_id":"owner_supplier_metadata_mismatch","dspace_portfolio_item_id":item["dspace_portfolio_item_id"]})
            continue
        aliases = sorted({item["dspace_commercial_name"], *item.get("aliases", [])}, key=len, reverse=True)
        alias_union = "|".join(re.escape(alias) for alias in aliases)
        company_union = "|".join(re.escape(company) for company in companies)
        for field, text in fields:
            patterns = [
                ("target_company_possessive_dspace_product", rf"(?:{company_union})['\u2019]s\s+(?:{alias_union})"),
                ("their_dspace_product", rf"\btheir\s+(?:{alias_union})"),
                ("target_company_supplier_verb", rf"(?:{company_union})\s+{supplier_verbs}\s+(?:the\s+)?(?:{alias_union})"),
            ]
            for rule_id, pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    violations.append({"rule_id":rule_id,"dspace_portfolio_item_id":item["dspace_portfolio_item_id"],"product_alias":match.group(0),"matched_text":match.group(0),"narrative_field":field})
        mentions = [(match.start(), match.group(0)) for match in re.finditer(alias_union, joined, re.IGNORECASE)]
        if not mentions:
            violations.append({"rule_id":"missing_recommended_product_mention","dspace_portfolio_item_id":item["dspace_portfolio_item_id"]})
            continue
        start, mention = mentions[0]
        before = joined[max(0,start-attribution_window):start]
        sentence_start = max(joined.rfind(mark, max(0,start-500), start) for mark in ".!?\n")
        same_sentence_before = joined[sentence_start+1:start]
        after = joined[start:min(len(joined),start+len(mention)+attribution_window)]
        mention_pattern = re.escape(mention)
        direct_prefix = re.search(
            rf"(?:the\s+|an?\s+)?dSPACE(?: GmbH)?(?:['\u2019]s)?\s+"
            rf"(?:(?:product|service|solution|platform|system|tool|package|offering)\s+"
            rf"(?:(?:called|named|like|such\s+as)\s+)?(?:the\s+)?)?$",
            before,
            re.IGNORECASE,
        )
        supplier_lead = re.search(
            rf"dSPACE(?: GmbH)?(?:['\u2019]s)?\s+"
            rf"(?:(?:portfolio|products?|services?|solutions?|offerings?)\b[\s\S]{{0,500}}"
            rf"|(?:offers?|provides?|supplies?|delivers?|develops?)\b[\s\S]{{0,500}})$",
            same_sentence_before,
            re.IGNORECASE,
        )
        direct_suffix = re.match(
            rf"{mention_pattern}(?:\s+(?:product|service|solution|platform|system|tool|package|offering))?"
            rf"\s+(?:from|by|offered\s+by|provided\s+by|supplied\s+by)\s+dSPACE(?: GmbH)?\b"
            rf"|{mention_pattern}\s*,?\s+(?:an?\s+)?dSPACE\s+(?:product|service|solution|platform|system|tool|package|offering)\b",
            after,
            re.IGNORECASE,
        )
        attributed = bool(direct_prefix or supplier_lead or direct_suffix)
        if not attributed:
            violations.append({"rule_id":"missing_first_mention_dspace_attribution","dspace_portfolio_item_id":item["dspace_portfolio_item_id"],"product_alias":mention})
    failure_code = None
    if any(v["rule_id"]=="owner_supplier_metadata_mismatch" for v in violations):
        failure_code = "llm_owner_supplier_metadata_mismatch"
    elif any(v["rule_id"] in {"target_company_possessive_dspace_product","their_dspace_product","target_company_supplier_verb"} for v in violations):
        failure_code = "llm_product_ownership_violation"
    elif violations:
        failure_code = "llm_missing_dspace_product_attribution"
    return {"status":"valid" if not violations else "invalid_response","failure_code":failure_code,"target_company":target_company_name,"violations":violations,"fallback_used":bool(violations)}
