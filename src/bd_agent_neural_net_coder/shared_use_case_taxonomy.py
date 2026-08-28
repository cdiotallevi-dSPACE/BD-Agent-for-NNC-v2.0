"""Single source of truth for cross-channel NNC use-case vocabulary."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=1)
def load_shared_use_case_taxonomy() -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "config/domains/tiny_edge_ai/shared_use_case_taxonomy.yaml"
    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def families_for_industry(industry: str) -> dict[str, dict]:
    taxonomy = load_shared_use_case_taxonomy()
    normalized = str(industry or "").casefold()
    return {family_id: definition for family_id, definition in taxonomy["use_case_families"].items()
            if normalized in {str(value).casefold() for value in definition.get("industries", [])}}


def family_terms(family_id: str, include_context: bool = False) -> tuple[str, ...]:
    definition = load_shared_use_case_taxonomy()["use_case_families"][family_id]
    fields = ["core_discovery_terms", "extended_matching_terms"]
    if include_context:
        fields.append("context_terms")
    return tuple(dict.fromkeys(term for field in fields for term in definition.get(field, [])))


def all_matching_terms(include_context: bool = False) -> tuple[str, ...]:
    taxonomy = load_shared_use_case_taxonomy()
    terms = []
    terms.extend(taxonomy.get("public_oem_application_vocabulary", []))
    terms.extend(taxonomy.get("generic_neural_terms", {}).get("core_discovery_terms", []))
    terms.extend(taxonomy.get("generic_neural_terms", {}).get("extended_matching_terms", []))
    for family_id in taxonomy["use_case_families"]:
        terms.extend(family_terms(family_id, include_context=include_context))
    return tuple(dict.fromkeys(terms))


def match_use_case_families(text: str, include_context: bool = False) -> dict[str, list[str]]:
    folded = " ".join(str(text or "").casefold().replace("-", " ").split())
    matches = {}
    for family_id in load_shared_use_case_taxonomy()["use_case_families"]:
        hits = []
        for term in family_terms(family_id, include_context=include_context):
            normalized = " ".join(term.casefold().replace("-", " ").split())
            # Patent prose commonly pluralizes the final noun (temperature(s),
            # model(s), sensor(s)); tolerate that morphology deterministically.
            if normalized in folded or (not normalized.endswith("s") and normalized + "s" in folded):
                hits.append(term)
        if hits:
            matches[family_id] = hits
    return matches


def patent_cpc_family_matches(codes: list[str] | tuple[str, ...]) -> dict[str, list[str]]:
    normalized = [str(code).upper().replace(" ", "") for code in codes]
    matches = {}
    for family_id, definition in load_shared_use_case_taxonomy()["use_case_families"].items():
        hits = [configured for configured in definition.get("patent_cpc_codes", [])
                if any(code.startswith(str(configured).upper().replace(" ", "")) for code in normalized)]
        if hits:
            matches[family_id] = hits
    return matches


def neural_cpc_match(codes: list[str] | tuple[str, ...]) -> bool:
    configured = load_shared_use_case_taxonomy().get("generic_neural_terms", {}).get("patent_cpc_codes", [])
    normalized = [str(code).upper().replace(" ", "") for code in codes]
    return any(any(code.startswith(str(prefix).upper().replace(" ", "")) for code in normalized)
               for prefix in configured)
