"""Deterministic document-to-company attribution for specification v1.7."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from .core import slugify


REFERENCE_HEADING = re.compile(r"(?im)^\s*(references|bibliography|works cited)\s*$")
UNIT_PATTERNS = ("research valley", "research centre", "research center", "research and development",
                 "r&d", "advanced research", "technology centre", "technology center", "technical centre",
                 "technical center", "engineering centre", "engineering center", "innovation centre",
                 "innovation center", "design studio", "design center", "design centre",
                 "software defined vehicle centre", "software defined vehicle center", "laboratory", "labs")
GENERIC_BRAND_WORDS = {"general", "global", "international", "company", "corporation", "limited", "ltd",
                       "inc", "group", "holding", "holdings", "automotive", "motors", "industries"}


def classify_alias(alias: str, company: str) -> str:
    value = alias.strip()
    if value.casefold() == company.strip().casefold():
        return "canonical_name"
    compact = re.sub(r"[^A-Za-z0-9]", "", value)
    if len(compact) <= 4 and compact.upper() == compact:
        return "ambiguous_short_acronym"
    if len(value.split()) >= 2:
        return "long_unambiguous_alias"
    return "brand_name"


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?i)(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _initials_pattern(alias: str) -> re.Pattern[str]:
    letters = [c for c in alias if c.isalpha()]
    return re.compile(r"(?i)(?<!\w)" + r"\.\s*".join(map(re.escape, letters)) + r"\.(?!\w)")


def establish_document_company_attribution(
    doc: dict,
    *,
    company: str,
    official_domain: str,
    company_aliases: list[str] | None = None,
    validated_source_assignees: list[dict | str] | None = None,
    validated_patent_assignees: list[dict | str] | None = None,
    candidate: dict | None = None,
) -> dict:
    """Establish attribution independently from search/query provenance."""
    candidate = candidate or {}
    scan_id = slugify(company).replace("-", "_")
    source_class = candidate.get("source_domain_class", "third_party_analytics")
    url = doc.get("url") or doc.get("requested_url") or ""
    host = (urlparse(url).hostname or "").lower()
    official = official_domain.lower().strip().removeprefix("www.")
    text = "\n".join(str(page.get("text", "")) for page in doc.get("pages", [])) or str(doc.get("text", ""))
    reference_match = REFERENCE_HEADING.search(text)
    body = text[: reference_match.start()] if reference_match else text
    references = text[reference_match.start():] if reference_match else ""
    anchors: list[dict] = []
    reason_codes: list[str] = []
    configured_assignees=validated_source_assignees if validated_source_assignees is not None else (validated_patent_assignees or [])

    approved_domain = bool(host and (host == official or host.endswith("." + official))) or source_class in {
        "official_company", "official_company_asset", "related_corporate"
    }
    if approved_domain:
        anchors.append({"anchor_type": "official_domain_ownership", "strength": "strong", "value": host})

    if host in {"patents.google.com", "patents.justia.com", "data.uspto.gov", "api.uspto.gov"}:
        # Official native metadata is propagated to duplicate Google/Justia/web
        # candidates by publication number. Its authority does not disappear
        # merely because the retrieved full text uses a different host.
        official_metadata_assignees = candidate.get("official_patent_assignees", [])
        provenance_assignee = (candidate.get("provenance") or {}).get("enumeration_assignee")
        if provenance_assignee:
            official_metadata_assignees = [*official_metadata_assignees, provenance_assignee]
        for configured in configured_assignees:
            if isinstance(configured, dict):
                assignee = str(configured.get("assignee_name", ""))
                validated = configured.get("validation_status") == "established"
            else:
                assignee, validated = str(configured), True
            metadata_match = any(_contains_phrase(value, assignee) or _contains_phrase(assignee, value)
                                 for value in official_metadata_assignees if value)
            if validated and assignee and (_contains_phrase(body, assignee) or metadata_match):
                anchors.append({"anchor_type": "validated_source_assignee", "strength": "strong", "value": assignee})
                break

    # The same operator-validated legal identity may establish attribution in
    # authoritative non-patent evidence when it appears substantively in body text.
    if not anchors:
        for configured in configured_assignees:
            assignee=str(configured.get("assignee_name", "")) if isinstance(configured,dict) else str(configured)
            validated=(configured.get("validation_status")=="established") if isinstance(configured,dict) else True
            if validated and assignee and _contains_phrase(body,assignee):
                anchors.append({"anchor_type":"validated_source_assignee","strength":"strong","value":assignee})
                break

    names = [(company, "canonical_name"), *((a, classify_alias(a, company)) for a in (company_aliases or []))]
    for value, alias_class in names:
        if alias_class in {"canonical_name", "legal_name", "long_unambiguous_alias"} and _contains_phrase(body, value):
            anchors.append({"anchor_type": "canonical_full_name" if alias_class == "canonical_name" else alias_class,
                            "strength": "strong", "value": value})

    # v1.3: resolve corporate R&D-unit affiliations generically. Short/ambiguous
    # acronyms are deliberately excluded from this shortcut.
    brand_values = [company, *(company_aliases or [])]
    brand_tokens = []
    for value in brand_values:
        if classify_alias(value, company) == "ambiguous_short_acronym":
            continue
        brand_tokens.extend(token for token in re.findall(r"[A-Za-z][A-Za-z0-9&-]+", value)
                            if len(token) >= 5 and token.casefold() not in GENERIC_BRAND_WORDS)
    body_fold = body.casefold()
    for token in dict.fromkeys(brand_tokens):
        if _contains_phrase(body, token) and any(pattern in body_fold for pattern in UNIT_PATTERNS):
            anchors.append({"anchor_type": "corporate_organizational_unit_affiliation", "strength": "strong",
                            "value": token})
            break

    ambiguous = [(value, kind) for value, kind in names if kind in {"short_acronym", "ambiguous_short_acronym"}]
    ambiguous_body = [value for value, _ in ambiguous if _contains_phrase(body, value)]
    bibliography_initials = [value for value, _ in ambiguous if references and _initials_pattern(value).search(references)]
    if bibliography_initials:
        reason_codes.append("bibliography_initials_alias_collision")
    if (ambiguous_body or bibliography_initials) and not anchors:
        reason_codes.append("ambiguous_company_alias_only")

    established = bool(anchors)
    if not established:
        reason_codes.insert(0, "target_company_not_established")
    return {
        "source_id": doc.get("source_id"),
        "source_url": url,
        "scan_target_company_id": scan_id,
        "attributed_company_id": scan_id if established else None,
        "company_attribution_status": "established" if established else "not_established",
        "source_attribution_scope": "target_company_or_explicitly_related_partner" if established else "general_industry_background",
        "mapping_eligible": established,
        "score_contribution": "eligible" if established else 0,
        "relevant_evidence_eligible": established,
        "strong_company_anchor_present": bool(anchors),
        "identity_anchors": anchors,
        "ambiguous_alias_matches": ambiguous_body,
        "bibliography_initials_matches": bibliography_initials,
        "reason_codes": list(dict.fromkeys(reason_codes)),
    }
