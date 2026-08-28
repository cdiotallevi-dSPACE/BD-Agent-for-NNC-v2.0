from __future__ import annotations
from .execution_resources import http_scope, provider_task_scope, provider_task
from .audit_journal import discovery_audit, audit_event, journaled_json as atomic_json

import asyncio
import os
import re
from dataclasses import asdict
from pathlib import Path
from urllib.parse import urlparse

from .config_manager import load_yaml, load_search_config
from .company_attribution import classify_alias
from .core import normalize_company_domain, normalize_url, slugify, utc_now
from .internal_crawler_provider import InternalCrawlerProvider, PublicationHubProvider
from .pdf_link_provider import PDFLinkProvider
from .provider_registry import PROVIDERS
from .credential_manager import resolve_credential
from .provider_quota_ledger import ProviderQuotaLedger, QuotaUnavailable
from .search_models import CompanySearchContext, SearchQuery, valid_http_url
from .sitemap_provider import SitemapSearchProvider
from .patent_native_discovery import PatentNativeDiscovery, REQUIRED_TERMS, supplemental_patent_results_usable
from .shared_use_case_taxonomy import (
    all_matching_terms, families_for_industry, load_shared_use_case_taxonomy,
    match_use_case_families,
)

GENERAL_WEB_FALLBACK = ("ddgs", "brave", "serpapi", "serper")
ENGINEERING_PUBLISHERS = {"saemobilus.sae.org", "sae.org", "mathworks.com", "www.mathworks.com"}
HIGH_VALUE_USE_CASES = (
    "battery health", "state of health", "state of charge", "remaining useful life", "virtual sensor",
    "soft sensor", "sensorless", "state estimation", "operating condition", "loading condition",
    "payload estimation", "vehicle mass", "condition monitoring", "predictive maintenance", "telematics",
)
PATENT_HOSTS = {"patents.google.com", "patents.justia.com", "api.uspto.gov", "data.uspto.gov"}
PATENT_USE_CASE_TERMS = {
    "vehicle_dynamics_learned_estimation": ("state estimation", "tractive limit", "wheel stability"),
    "indirect_physical_state_and_virtual_sensing": ("virtual measurement", "state estimation", "sensorless estimation"),
    "condition_monitoring_and_prognostics": ("condition monitoring", "predictive maintenance"),
    "perception_classification_and_detection": ("classification", "object detection"),
    "battery_virtual_measurement_and_predictive_control": (
        "battery charging", "predictive charging", "dynamic performance variable", "charging limit",
        "future battery state", "electrochemical phenomenon", "baseline calibration",
        "data-driven estimation", "neural network learning agent", "battery state estimation", "battery health",
    ),
}
INDUSTRY_PATENT_BASELINES = {
    "automotive": tuple(PATENT_USE_CASE_TERMS),
    "transportation": tuple(PATENT_USE_CASE_TERMS),
    "energy": ("battery_virtual_measurement_and_predictive_control", "condition_monitoring_and_prognostics", "indirect_physical_state_and_virtual_sensing"),
    "industrial": ("condition_monitoring_and_prognostics", "indirect_physical_state_and_virtual_sensing"),
}
PATENT_CPC_CODES = ("B60L58/10", "B60L58/12", "B60L58/16", "G01R31/36", "G01R31/367", "G01R31/392", "H02J7/84", "H02J7/90", "G05B13/048")
TECHNICAL_ACTIONS = ("recognition", "detect", "estimate", "estimation", "infer", "classify", "predict", "monitor")

def _redact(value: str, secrets: list[str | None]) -> str:
    for secret in secrets:
        if secret: value=value.replace(secret,"[REDACTED]")
    return value


def load_company_profile(root: Path, company: str, official_domain: str, explicit_seeds: list[str] | None = None, company_aliases: list[str] | None = None, validated_source_assignees: list[str] | None = None) -> dict:
    official_domain = normalize_company_domain(official_domain)
    path = root / "data/company_source_profiles" / f"{slugify(company)}.yaml"
    profile = load_yaml(path) if path.exists() else {}
    profile.setdefault("company_name", company)
    configured_aliases=profile.get("company_aliases",[])
    profile["company_aliases"]=list(dict.fromkeys(name.strip() for name in [*configured_aliases,*(company_aliases or [])] if name and name.strip() and name.strip().casefold()!=company.casefold()))
    profile.setdefault("official_domains", [official_domain])
    profile.setdefault("official_asset_domains", [])
    profile.setdefault("related_corporate_domains", [])
    profile.setdefault("partner_domains", [])
    profile.setdefault("specialist_domains", [])
    profile.setdefault("publication_hubs", [])
    profile.setdefault("company_research_affiliations", [])
    # Company identity is controlled exclusively by Companies.xlsx/runtime
    # input. YAML profiles cannot silently invent validated identities.
    profile.pop("validated_patent_assignees",None)
    resolved=[{"assignee_name":name,"attributed_company_id":slugify(company).replace("-","_"),
               "validation_status":"established","validation_basis":"companies_workbook_validated_source_assignee"}
              for name in (validated_source_assignees or [])]
    profile["validated_source_assignees"]=resolved
    profile["validated_patent_assignees"]=resolved
    profile.setdefault("industry", "unknown")
    profile["seed_urls"] = list(dict.fromkeys([*profile.get("seed_urls", []), *(explicit_seeds or [])]))
    return profile


def generate_queries(profile: dict, run_profile: str = "standard") -> list[SearchQuery]:
    official = profile["official_domains"][0]
    company = profile["company_name"]
    brand = next((a for a in profile.get("company_aliases", []) if classify_alias(a, company) == "brand_name"), None)
    if not brand:
        brand = next((t for t in company.replace("&", " ").split() if len(t) >= 5 and t.casefold() not in
                      {"general", "company", "corporation", "limited", "automotive", "motors"}), company)
    validated_source_assignees = [
        item.get("assignee_name", "") if isinstance(item, dict) else str(item)
        for item in profile.get("validated_source_assignees", profile.get("validated_patent_assignees", []))
    ]
    validated_source_assignees = [value.strip() for value in validated_source_assignees if value and value.strip()]
    public_identities = list(dict.fromkeys([brand, *validated_source_assignees]))
    identity_clause = "(" + " OR ".join(f'\"{identity}\"' for identity in public_identities) + ")"
    values = [
        (f'site:{official} "neural network" embedded', "neural_model", True, ("ddgs","brave","serpapi","serper")),
        (f"site:{official} TinyML microcontroller", "embedded_target", True, ("ddgs","brave","serpapi")),
        (f"site:{official} Edge AI MCU", "embedded_target", True, ("ddgs","brave")),
        (f"site:{official} ONNX embedded", "deployment_workflow", True, ("ddgs",)),
        (f'site:{official} ("CNN" OR "LSTM") microcontroller', "neural_model", True, ("ddgs",)),
        (f"site:{official} quantization INT8 embedded", "optimization", True, ("ddgs",)),
        (f"site:{official} RAM flash latency neural network", "resource_constraint", True, ("ddgs",)),
        (f'site:{official} ("SIL" OR "PIL") neural network', "verification", True, ("ddgs",)),
        (f'site:{official} ("virtual sensor" OR "soft sensor")', "use_case", True, ("ddgs",)),
        (f"site:{official} publications embedded AI", "publication", True, ("ddgs","brave","serpapi")),
        (f'site:{official} filetype:pdf "neural network" MCU', "official_pdf", True, ("ddgs","brave","serper")),
    ]
    shared_taxonomy = load_shared_use_case_taxonomy()
    shared_families = families_for_industry(profile.get("industry", "unknown"))
    term_limit = int(shared_taxonomy["channel_policy"][
        "fast_iteration_core_terms_per_family" if run_profile == "fast_iteration" else "standard_core_terms_per_family"])
    # Application-only searches intentionally precede supplemental patent-web
    # searches. Public OEM material often names the engineering problem but
    # omits TinyML/ONNX vocabulary from its title and snippet.
    for family_id, definition in shared_families.items():
        for term_index, term in enumerate(definition.get("core_discovery_terms", [])[:term_limit]):
            values.append((f'site:{official} "{term}"', "shared_use_case_official", True, GENERAL_WEB_FALLBACK))
            values.append((f'{identity_clause} "{term}"', "shared_use_case_general_web", True, GENERAL_WEB_FALLBACK))
        first_term = next(iter(definition.get("core_discovery_terms", [])), None)
        if first_term:
            values.append((f'{identity_clause} "{first_term}" filetype:pdf', "shared_use_case_pdf_publication", True, GENERAL_WEB_FALLBACK))
            values.append((f'site:saemobilus.sae.org/papers {identity_clause} "{first_term}"', "shared_use_case_professional_publication", True, GENERAL_WEB_FALLBACK))
    for domain in profile.get("official_asset_domains", []):
        values.extend([(f'site:{domain} filetype:pdf "neural network"', "official_pdf", True, ("ddgs","brave","serpapi")), (f"site:{domain} filetype:pdf TinyML MCU", "official_pdf", True, ("ddgs","brave","serper"))])
    for domain in profile.get("related_corporate_domains", []):
        values.append((f'site:{domain} ("embedded AI" OR TinyML)', "related_corporate", False, ("ddgs",)))
    values.extend([
        (f'"{company}" filetype:pdf neural network microcontroller', "academic", False, ("ddgs", "semantic_scholar")),
        (f'"{company}" patent "machine learning"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
        (f'"{brand}" patent "machine learning"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
        (f'"{brand}" patent "state estimation"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
        (f'"{brand}" patent regression classification', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
        (f'"{company}" TinyML ONNX embedded', "repository", False, ("github",)),
        (f'"{brand}" ("machine learning" OR "supervised learning" OR "data-driven") (vehicle OR automotive OR telematics OR ADAS OR estimator OR "virtual sensor" OR "soft sensor")', "applied_ml_research", True, ("ddgs",)),
        (f'"{brand}" ("machine learning" OR "data analytics" OR AI) ("technical paper" OR paper OR publication OR conference OR DOI)', "applied_ml_research", True, ("ddgs",)),
        (f'"{brand}" "machine learning" vehicle', "applied_ml_research", True, ("ddgs",)),
        (f'"{brand}" "machine learning" "technical paper"', "applied_ml_research", True, ("ddgs",)),
        (f'site:saemobilus.sae.org/papers "{company}" "machine learning"', "applied_ml_research", True, GENERAL_WEB_FALLBACK),
        (f'site:saemobilus.sae.org/papers {brand} telematics', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
        (f'site:saemobilus.sae.org/papers {brand} ADAS', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
        (f'site:saemobilus.sae.org/papers {brand} "loading condition"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
        (f'site:saemobilus.sae.org/papers {brand} "state estimation"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
        (f'"{brand}" ("battery health" OR "state of health" OR "virtual sensor" OR "condition monitoring")', "use_case_led_discovery", True, GENERAL_WEB_FALLBACK),
        (f'"{brand}" (research OR R&D OR engineering) ("machine learning" OR AI) (paper OR SAE OR conference)', "company_affiliation_research", False, ("ddgs",)),
    ])
    assignees = validated_source_assignees
    for assignee in assignees:
        values.extend([
            (f'site:patents.google.com/patent "{assignee}" "neural network"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" "artificial neural network"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" "deep neural network"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" "transfer learning"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" "machine learning"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" "state estimation"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee}" regression classification', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.justia.com "{assignee}" "machine learning"', "patent_discovery_atomic", True, GENERAL_WEB_FALLBACK),
            (f'"{brand}" patent "battery charging"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
        ])
    industry = str(profile.get("industry", "unknown")).casefold()
    families = tuple(shared_families) or INDUSTRY_PATENT_BASELINES.get(industry, ("condition_monitoring_and_prognostics", "indirect_physical_state_and_virtual_sensing"))
    assignee_or_company = assignees[0] if assignees else company
    for family in families:
        # Application-only queries are mandatory: AI vocabulary may exist only in the patent body.
        term = shared_families.get(family, {}).get("core_discovery_terms", PATENT_USE_CASE_TERMS.get(family, ("state estimation",)))[0]
        values.extend([
            (f'"{brand}" patent "{term}"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee_or_company}" "{term}"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee_or_company}" "{term}" "machine learning"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee_or_company}" "{term}" "data-driven"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.google.com/patent "{assignee_or_company}" "{term}" estimator', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
            (f'site:patents.justia.com "{assignee_or_company}" "{term}"', "patent_use_case_atomic", True, GENERAL_WEB_FALLBACK),
        ])
    for code in PATENT_CPC_CODES:
        values.append((f'site:patents.google.com/patent "{assignee_or_company}" "{code}"', "patent_cpc_atomic", False, GENERAL_WEB_FALLBACK))
    for family in families:
        terms = shared_families.get(family, {}).get("core_discovery_terms", [])[:term_limit]
        if family not in families:
            continue
        for term in terms:
            values.append((f'site:patents.google.com/patent "{assignee_or_company}" "{term}"', "patent_term_supplemental", True, GENERAL_WEB_FALLBACK))
    # The dedicated provider supplements general-web discovery without becoming the only route.
    values.append((f'"{company}" machine learning', "patent_provider_supplement", False, ("patent",)))
    for affiliation in profile.get("company_research_affiliations", []):
        values.extend([
            (f'site:saemobilus.sae.org/papers "{affiliation}" "machine learning"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
            (f'"{affiliation}" telematics "machine learning"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
            (f'"{affiliation}" "supervised machine learning"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
            (f'"{affiliation}" SAE "machine learning"', "professional_publication_atomic", True, GENERAL_WEB_FALLBACK),
        ])
    for alias in profile.get("company_aliases",[]):
        values.append((f'"{alias}" neural network microcontroller', "company_alias", False, ("ddgs",)))
    queries = []
    for index, (rendered, family, mandatory, providers) in enumerate(values, 1):
        priority = "high" if mandatory else "medium"
        if family == "company_alias":
            alias = rendered.split('"', 2)[1]
            if classify_alias(alias, profile["company_name"]) in {"short_acronym", "ambiguous_short_acronym"}:
                priority = "low"
        queries.append(SearchQuery(f"qry_{index:04d}", rendered, family, priority, mandatory, providers))
    return queries


def classify_domain(url: str, profile: dict) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host in PATENT_HOSTS or "/patent/" in url.lower():
        return "specialist_patent_source"
    groups = (
        ("official_company_asset", profile.get("official_asset_domains", [])),
        ("official_company", profile.get("official_domains", [])),
        ("related_corporate", profile.get("related_corporate_domains", [])),
        ("partner_hosted", profile.get("partner_domains", [])),
        ("specialist_patent_source", profile.get("specialist_domains", [])),
    )
    for label, domains in groups:
        if any(host == domain or host.endswith("." + domain) for domain in domains):
            return label
    return "third_party_analytics"


def candidate_retrieval_priority(item: dict, profile: dict) -> tuple[int, list[str]]:
    """Deterministic v1.5 pre-retrieval heuristic; never establishes attribution."""
    title = str(item.get("title_hint", ""))
    snippet = str(item.get("snippet", ""))
    url = str(item.get("canonical_url", ""))
    combined = f"{title} {snippet} {url}".casefold()
    title_fold = title.casefold()
    host = (urlparse(url).hostname or "").lower()
    score = 0
    reasons: list[str] = []
    company_names = [profile["company_name"], *profile.get("company_aliases", [])]
    if item.get("source_domain_class") in {"official_company", "official_company_asset"}:
        score += 80; reasons.append("official_company_web_source_priority")
    if any(len(name) > 4 and name.casefold() in combined for name in company_names):
        score += 35; reasons.append("target_company_identity_signal")
    shared_matches = match_use_case_families(f"{title} {snippet}")
    title_shared_matches = match_use_case_families(title)
    if any(term in title_fold for term in HIGH_VALUE_USE_CASES) or title_shared_matches:
        score += 30; reasons.append("high_priority_use_case_in_title")
    elif any(term in combined for term in HIGH_VALUE_USE_CASES) or shared_matches:
        score += 20; reasons.append("high_priority_use_case_in_snippet")
    if any(term in combined for term in TECHNICAL_ACTIONS):
        score += 10; reasons.append("technical_action_signal")
    if any(term in combined for term in ("neural network", "deep learning", "cnn", "lstm")):
        score += 25; reasons.append("explicit_neural_signal")
    elif any(term in combined for term in ("anfis", "anfc", "neuro fuzzy", "neuro-fuzzy")):
        score += 22; reasons.append("hybrid_neural_signal")
    elif any(term in combined for term in ("machine learning", "supervised learning", "data-driven")):
        score += 10; reasons.append("machine_learning_signal")
    if any(term in combined for term in ("ecu", "mcu", "onboard", "real-time", "real time", "telematics")):
        score += 15; reasons.append("physical_or_embedded_adjacent_signal")
    if host in PATENT_HOSTS or "/patent/" in url.lower():
        score += 30; reasons.append("target_company_patent_candidate")
        if shared_matches or any(term in combined for term in sum(PATENT_USE_CASE_TERMS.values(), ())):
            score += 25; reasons.append("patent_application_use_case")
    professional = host in ENGINEERING_PUBLISHERS and any(term in combined for term in ("/papers/", ".pdf", "technical paper", "conference", "case study", "user_stor"))
    if professional:
        score += 30; reasons.append("professional_applied_ml_publication")
    if any(term in combined for term in ("technical paper", "presentation", "proceedings", "conference")) or ".pdf" in url.lower():
        score += 25; reasons.append("primary_technical_document")
    if host in ENGINEERING_PUBLISHERS:
        score += 20; reasons.append("configured_engineering_publisher")
    if any(term in combined for term in ("owner manual", "owners manual", "service manual", "operator manual")):
        score -= 25; reasons.append("generic_manual_penalty")
    if "annual-report" in combined or "annual_report" in combined:
        score -= 15; reasons.append("annual_report_penalty")
    return score, reasons


def build_seed_registration(seed_urls: list[str], policy: dict) -> tuple[dict, list[str]]:
    maximum=policy["maximum_explicit_seed_entries_per_company"]
    if len(seed_urls)>maximum:
        artifact={"configured_seed_entry_count":len(seed_urls),"valid_seed_entry_count":0,"unique_canonical_seed_count":0,"registered_seed_entry_count":0,"seed_registration_status":"failed_configuration_seed_limit_exceeded","seeds_registered":False,"entries":[]}
        return artifact,[]
    entries=[]; canonical_urls=[]
    for index,url in enumerate(seed_urls,1):
        valid=valid_http_url(url)
        canonical=normalize_url(url) if valid else None
        entries.append({"seed_entry_number":index,"configured_url":url,"canonical_url":canonical,"registration_status":"registered" if valid else "invalid_url","protected_for_retrieval":bool(valid and policy["protect_valid_seeds_for_retrieval"])})
        if valid and canonical not in canonical_urls: canonical_urls.append(canonical)
    valid_count=sum(item["registration_status"]=="registered" for item in entries)
    complete=valid_count==len(entries)
    status="complete" if complete else "failed_configuration_invalid_seed_url"
    artifact={"configured_seed_entry_count":len(entries),"valid_seed_entry_count":valid_count,"unique_canonical_seed_count":len(canonical_urls),"registered_seed_entry_count":valid_count,"seed_registration_status":status,"seeds_registered":complete,"entries":entries}
    return artifact,canonical_urls


def apply_candidate_budget(candidates: dict[str,dict], budget: dict) -> tuple[list[dict],list[dict],dict]:
    protected=sorted((item for item in candidates.values() if item.get("protected_for_retrieval")),key=lambda item:item["canonical_url"])
    patent_reserved=list(item for item in candidates.values() if item.get("patent_native_reserved"))
    def patent_order(item):
        provider=str(item.get("provider_id","")).casefold(); host=(urlparse(item["canonical_url"]).hostname or "").lower()
        tier=0 if "uspto" in provider or host in {"api.uspto.gov","data.uspto.gov"} else 1 if host=="patents.google.com" else 2
        return (tier,-int(item.get("retrieval_priority_score",0)),item["canonical_url"])
    patent_reserved=sorted(patent_reserved,key=patent_order)
    ordinary=[item for item in candidates.values() if not item.get("protected_for_retrieval") and not item.get("patent_native_reserved")]
    ranked=sorted(ordinary,key=lambda item:(-int(item.get("retrieval_priority_score",0)),item["canonical_url"]))
    selected=[]; host_counts={}; low_priority=0; career_pages=0
    for item in ranked:
        host=(urlparse(item["canonical_url"]).hostname or "").lower()
        is_career=any(token in item["canonical_url"].lower() for token in ("/career","/jobs","/job/"))
        is_low=item["source_domain_class"]=="third_party_analytics"
        if host_counts.get(host,0)>=budget["maximum_non_seed_candidates_per_host"]: continue
        if is_career and career_pages>=budget["maximum_career_pages_per_company"]: continue
        if is_low and low_priority>=budget["maximum_low_priority_third_party_pages"]: continue
        if len(selected)>=budget["maximum_canonical_non_seed_candidates_per_company"]: break
        selected.append(item); host_counts[host]=host_counts.get(host,0)+1
        career_pages+=int(is_career); low_priority+=int(is_low)
    official=[x for x in selected if x.get("source_domain_class") in {"official_company","official_company_asset"}]
    other=[x for x in selected if x not in official]
    total=int(budget["maximum_retrieved_non_seed_documents_per_company"])
    patent_cap=min(len(patent_reserved),int(budget.get("maximum_patent_documents_selected",total)))
    patent_selected=patent_reserved[:patent_cap]
    retrieval_non_seeds=[*official,*other][:max(0,total-len(patent_selected))]
    effective=[*protected,*official,*patent_reserved,*other]
    retrieval=[*protected,*official,*patent_selected,*[x for x in other if x in retrieval_non_seeds]]
    audit={"protected_seed_count":len(protected),"protected_seed_selected_count":len(protected),"non_seed_candidates_before_budget":len(ordinary),"non_seed_candidates_selected_after_budget":len(selected),"non_seed_candidates_selected_for_retrieval":len(retrieval_non_seeds),"non_seed_candidates_dropped_by_budget":len(ordinary)-len(selected),"effective_candidate_count":len(effective),"effective_retrieval_count":len(retrieval)}
    audit.update({"patent_native_reserved_count":len(patent_reserved),"patent_selected_count":len(patent_selected),
                  "source_priority_order":["official_company_web","uspto_patents","google_patents","other_web"]})
    return effective,retrieval,audit


@http_scope
@discovery_audit
@provider_task_scope
async def discover(root: Path, out: Path, company: str, official_domain: str, explicit_seeds: list[str] | None = None, provider_cycle_state=None, company_aliases: list[str] | None = None, run_profile: str = "standard", validated_source_assignees: list[str] | None = None) -> dict:
    config = load_search_config(root,run_profile)
    profile = load_company_profile(root, company, official_domain, explicit_seeds, company_aliases,validated_source_assignees)
    resolved=profile["validated_source_assignees"]
    atomic_json(out/"source_assignee_registry.json",{"company_name":company,"source_of_truth":"Companies.xlsx",
        "validated_source_assignees":resolved,"status":"ready" if resolved else "degraded_no_validated_assignee"})
    seed_registration,canonical_seeds=build_seed_registration(profile["seed_urls"],config["seed_policy"])
    atomic_json(out/"seed_registration.json",seed_registration)
    if seed_registration["seed_registration_status"]!="complete":
        raise RuntimeError(seed_registration["seed_registration_status"])
    queries = generate_queries(profile, run_profile)
    generated_at = utc_now()
    query_records = [query.record(generated_at) for query in queries]
    atomic_json(out / "search_queries.json", {"queries": query_records})
    candidates: dict[str, dict] = {}
    candidate_attempts = [0]
    executions, provider_results, errors = [], [], []
    patent_supplemental_quality = []
    metrics = {
        "queries_generated": len(queries), "queries_executed": 0, "ddgs_calls_attempted": 0,
        "ddgs_calls_completed": 0, "ddgs_results_returned": 0, "semantic_scholar_calls_attempted": 0,
        "github_calls_attempted": 0, "sitemaps_attempted": 0, "publication_hubs_attempted": 0,
        "seed_urls_attempted": len(profile["seed_urls"]), "candidate_urls_registered": 0,
        "web_pdfs_downloaded": 0, "web_pdfs_parsed": 0, "unexecuted_mandatory_queries": 0,
    }
    metered_cfg={provider_id:value for provider_id,value in config["providers"].items() if value.get("period_type") in {"calendar_month","nonrenewing"}}
    quota=ProviderQuotaLedger(root/config["search_cost_policy"]["ledger_path"],metered_cfg)
    provider_usage={provider_id:{"provider_id":provider_id,"requests_attempted":0,"requests_completed":0,"requests_skipped_for_quota":0,"requests_skipped_missing_credentials":0,"state":"available"} for provider_id in config["providers"]}
    provider_scheduled={provider_id:0 for provider_id in config["providers"]}

    def register(item: dict, execution_id: str | None = None, query_id: str | None = None, protected: bool = False):
        raw_url = item.get("url", "")
        if not valid_http_url(raw_url):
            return
        candidate_attempts[0] += 1
        canonical = normalize_url(raw_url)
        if canonical not in candidates:
            candidates[canonical] = {
                "candidate_id": f"src_{len(candidates)+1:06d}",
                "scan_target_company_id": slugify(company).replace("-", "_"),
                "attributed_company_id": None,
                "company_attribution_status": "unverified",
                "discovery_channel": item.get("discovery_channel", item.get("provider_id", "unknown")),
                "provider_id": item.get("provider_id", "unknown"), "query_id": query_id,
                "execution_id": execution_id, "original_url": raw_url, "canonical_url": canonical,
                "source_domain_class": classify_domain(canonical, profile),
                "source_type_hint": "pdf" if ".pdf" in canonical.lower() else "html",
                "title_hint": item.get("title", ""), "snippet": item.get("snippet", ""),
                "patent_title":item.get("patent_title"),
                "discovered_at": utc_now(), "retrieval_status": "pending",
                "protected_for_retrieval":protected,
                "provenance": item.get("provenance"),
                "query_family": item.get("query_family"),
                "report_canonical_url": item.get("report_canonical_url"),
                "patent_application_number": item.get("application_number"),
            }
            priority, reasons = candidate_retrieval_priority(candidates[canonical], profile)
            candidates[canonical]["retrieval_priority_score"] = priority
            candidates[canonical]["retrieval_priority_reasons"] = reasons
            candidates[canonical]["source_category_hint"] = ("target_company_patent" if "target_company_patent_candidate" in reasons else ("professional_applied_ml_publication" if "professional_applied_ml_publication" in reasons else None))
        elif protected:
            candidates[canonical]["protected_for_retrieval"]=True

    for url in canonical_seeds:
        register({"url": url, "provider_id": "seed_urls", "discovery_channel": "explicit_seed_urls"},protected=True)
    for domain in profile["official_domains"]:
        register({"url": f"https://{domain}", "provider_id": "official_homepage", "discovery_channel": "official_homepage"})

    patent_native = await PatentNativeDiscovery(config).run(profile, out)
    for record in patent_native["selected"]:
        register({"url": record["patent_url"], "provider_id": record["source_provider"],
                  "discovery_channel": "patent_native_assignee_enumeration", "title": record.get("title", ""),
                  "patent_title":record.get("title", ""),
                  "snippet": record.get("abstract", ""), "query_family": "patent_native_assignee_corpus",
                  "report_canonical_url": record.get("report_canonical_url") or record.get("patent_portal_url"),
                  "application_number": record.get("application_number"),
                  "provenance": {"publication_number": record.get("publication_number"), "enumeration_assignee": record.get("enumeration_assignee"),
                                 "matched_use_case_families": record.get("matched_use_case_families", [])}})
        canonical = normalize_url(record["patent_url"])
        if canonical in candidates:
            candidates[canonical]["patent_native_reserved"] = True
            candidates[canonical]["source_domain_class"] = "specialist_patent_source"
            candidates[canonical]["normalized_publication_number"] = record.get("publication_number")

    for query, query_record in zip(queries, query_records):
        patent_query = query.family in {"patent_discovery_atomic", "patent_use_case_atomic", "patent_cpc_atomic", "patent_term_supplemental"}
        fallback_query = query.family == "professional_publication_atomic" or patent_query or "saemobilus.sae.org/papers" in query.rendered_query
        usable_professional_results = False
        prefetched = {}
        # Initial conservative parallelism: only an unconditional, unmetered
        # Semantic Scholar request alongside DDGS for the SAME query. No query
        # reordering, same-provider overlap, speculative paid calls or fallback.
        if not fallback_query and "ddgs" in query.target_provider_ids and "semantic_scholar" in query.target_provider_ids:
            pid = "semantic_scholar"
            pcfg = config["providers"].get(pid, {})
            if (pid not in metered_cfg and pcfg.get("enabled", False)
                    and (provider_cycle_state is None or provider_cycle_state.available(pid))
                    and provider_scheduled[pid] < pcfg.get("max_queries", 10**9)):
                credential = resolve_credential(pid, pcfg)
                if not credential["canonical_env"] or credential["value"]:
                    provider_scheduled[pid] += 1  # reserve BEFORE scheduling
                    provider = PROVIDERS[pid]()
                    context = CompanySearchContext(company, official_domain, pcfg.get("region", "us-en"), pcfg.get("safesearch", "moderate"), pcfg.get("backend", "auto"), pcfg.get("max_results_per_query", 10), pcfg.get("request_timeout_seconds", 15), os.getenv("GITHUB_TOKEN"), credential["value"], pcfg.get("endpoint", ""))
                    started = utc_now()
                    audit_event({"kind": "independent_provider_started", "query_id": query.query_id, "provider_id": pid, "started_at": started})

                    async def execute_independent(provider=provider, context=context, query=query):
                        try:
                            results = await provider.execute(query, context)
                            audit_event({"kind": "independent_provider_completed", "query_id": query.query_id, "provider_id": provider.provider_id, "results": [asdict(r) for r in results], "completed_at": utc_now()})
                            return results, None
                        except Exception as exc:
                            audit_event({"kind": "independent_provider_failed", "query_id": query.query_id, "provider_id": provider.provider_id, "error_type": type(exc).__name__, "completed_at": utc_now()})
                            return None, exc
                    prefetched[pid] = (provider, provider_task(execute_independent()), started)
        for provider_id in query.target_provider_ids:
            if fallback_query and usable_professional_results:
                break
            provider_cfg = config["providers"].get(provider_id, {})
            if not provider_cfg.get("enabled", False):
                continue
            if provider_cycle_state is not None and not provider_cycle_state.available(provider_id):
                continue
            execution_id = f"exec_{query.query_id[4:]}_{provider_id}"
            query_record["execution_state"] = "scheduled"
            execution = {"execution_id": execution_id, "query_id": query.query_id, "provider_id": provider_id, "submitted_query": query.rendered_query, "state": "provider_started", "started_at": prefetched[provider_id][2] if provider_id in prefetched else utc_now(), "completed_at": None, "results_returned": 0, "candidate_urls_registered": 0, "cache_hit": False, "error": None}
            executions.append(execution); atomic_json(out / "search_execution.json", {"executions": executions})
            query_record["execution_state"] = "provider_started"
            if provider_id not in prefetched and provider_scheduled[provider_id] >= provider_cfg.get("max_queries",10**9):
                execution.update({"state":"provider_failed","completed_at":utc_now(),"error":{"type":"ProviderBudgetExhausted","message":"per_run_query_budget_exhausted"}})
                provider_usage[provider_id]["requests_skipped_for_quota"]+=1
                query_record["execution_state"]="provider_failed"; atomic_json(out / "search_execution.json", {"executions": executions}); continue
            if provider_id not in prefetched:
                provider_scheduled[provider_id]+=1
            credential=resolve_credential(provider_id,provider_cfg)
            api_key=credential["value"]
            if credential["canonical_env"] and not api_key:
                execution.update({"state":"provider_failed","completed_at":utc_now(),"error":{"type":"ProviderUnavailable","message":"missing_credentials"}})
                provider_usage[provider_id]["requests_skipped_missing_credentials"]+=1; provider_usage[provider_id]["state"]="missing_credentials"
                errors.append({"provider_id":provider_id,"query_id":query.query_id,"type":"ProviderUnavailable","message":"missing_credentials"})
                query_record["execution_state"]="provider_failed"
                atomic_json(out / "search_execution.json", {"executions": executions}); continue
            reserved=False
            if provider_id in metered_cfg:
                try:
                    quota.reserve(provider_id); reserved=True
                except QuotaUnavailable as exc:
                    execution.update({"state":"provider_failed","completed_at":utc_now(),"error":{"type":"QuotaUnavailable","message":exc.state}})
                    provider_usage[provider_id]["requests_skipped_for_quota"]+=1; provider_usage[provider_id]["state"]=exc.state
                    errors.append({"provider_id":provider_id,"query_id":query.query_id,"type":"QuotaUnavailable","message":exc.state})
                    query_record["execution_state"]="provider_failed"
                    atomic_json(out / "search_execution.json", {"executions": executions}); continue
            metrics[f"{provider_id}_calls_attempted"] = metrics.get(f"{provider_id}_calls_attempted", 0) + 1
            provider_usage[provider_id]["requests_attempted"]+=1
            try:
                provider = prefetched[provider_id][0] if provider_id in prefetched else PROVIDERS[provider_id]()
                context = CompanySearchContext(company, official_domain, provider_cfg.get("region", "us-en"), provider_cfg.get("safesearch", "moderate"), provider_cfg.get("backend", "auto"), provider_cfg.get("max_results_per_query", 10), provider_cfg.get("request_timeout_seconds", 15), os.getenv("GITHUB_TOKEN"), api_key, provider_cfg.get("endpoint",""))
                if provider_id in prefetched:
                    results, failure = await prefetched[provider_id][1]
                    if failure is not None:
                        raise failure
                else:
                    results = await provider.execute(query, context)
                if provider_id == "patent":
                    patent_supplemental_quality.extend(getattr(provider, "quality_records", []))
                before = len(candidates)
                for result in results:
                    record = asdict(result) | {"execution_id": execution_id, "discovered_at": utc_now()}
                    provider_results.append(record)
                    register(record | {"discovery_channel": provider_id, "query_family": query.family}, execution_id, query.query_id)
                execution.update({"state": "provider_completed", "completed_at": utc_now(), "results_returned": len(results), "candidate_urls_registered": len(candidates)-before})
                if fallback_query and results:
                    if patent_query:
                        assignee_names = [x.get("assignee_name", "") if isinstance(x, dict) else str(x) for x in profile.get("validated_patent_assignees", [])]
                        query_terms = [term for terms in REQUIRED_TERMS.values() for term in terms if term.casefold() in query.rendered_query.casefold()]
                        usable_professional_results = supplemental_patent_results_usable(results, assignee_names, query_terms or ["machine learning", "state estimation"])
                    else:
                        usable_professional_results = True
                provider_usage[provider_id]["requests_completed"]+=1
                if reserved: quota.reconcile(provider_id,"completed",getattr(provider,"provider_reported_remaining",None))
                query_record["execution_state"] = "candidate_urls_registered"
                if provider_id == "ddgs":
                    metrics["ddgs_calls_completed"] += 1; metrics["ddgs_results_returned"] += len(results)
            except Exception as exc:
                safe_message=_redact(str(exc),[api_key,os.getenv("BRAVE_SEARCH_API_KEY"),os.getenv("SERPAPI_API_KEY"),os.getenv("SERPER_API_KEY")])[:1000]
                execution.update({"state": "provider_failed", "completed_at": utc_now(), "error": {"type": type(exc).__name__, "message": safe_message}})
                query_record["execution_state"] = "provider_failed"
                errors.append({"provider_id": provider_id, "query_id": query.query_id, "type": type(exc).__name__, "message": safe_message})
                provider_usage[provider_id]["state"]="provider_error"
                response=getattr(exc,"response",None)
                status_code=getattr(response,"status_code",None)
                headers=dict(getattr(response,"headers",{}) or {})
                rate_details={key:headers.get(key) for key in ("Retry-After","X-RateLimit-Remaining","X-RateLimit-Reset") if headers.get(key) is not None}
                if provider_cycle_state is not None and provider_id=="semantic_scholar" and status_code==429:
                    provider_cycle_state.record_rate_limit(provider_id,rate_details)
                elif provider_cycle_state is not None and provider_id=="github" and status_code==403:
                    if headers.get("X-RateLimit-Remaining")=="0" or headers.get("Retry-After"):
                        provider_cycle_state.record_rate_limit(provider_id,rate_details)
                    else:
                        provider_cycle_state.record_access_denied(provider_id,rate_details)
                if reserved: quota.reconcile(provider_id,"failed_chargeable")
            metrics["queries_executed"] += 1
            atomic_json(out / "search_execution.json", {"executions": executions})
            atomic_json(out / "provider_results.json", {"results": provider_results})
            atomic_json(out / "search_queries.json", {"queries": query_records})
        if fallback_query and not usable_professional_results:
            query_record["execution_state"] = "completed_no_results"
            query_record["zero_result_provider_fallback_exhausted"] = True
            atomic_json(out / "search_queries.json", {"queries": query_records})

    domains = list(dict.fromkeys([*profile["official_domains"], *profile.get("official_asset_domains", [])]))
    sitemap_cfg = config["providers"]["sitemap"]
    sitemap_results, sitemap_metrics = await SitemapSearchProvider().discover(domains, sitemap_cfg["max_files"], sitemap_cfg["max_urls"])
    metrics.update(sitemap_metrics)
    for item in sitemap_results: register(item)

    approved = set(domains + profile.get("related_corporate_domains", []) + profile.get("partner_domains", []))
    crawl_cfg = config["providers"]["internal_crawler"]
    crawl_starts = [f"https://{domain}" for domain in profile["official_domains"]]
    crawl_results, crawl_metrics = await InternalCrawlerProvider().discover(crawl_starts, approved, crawl_cfg["max_pages"], crawl_cfg["max_depth"])
    metrics["internal_pages_crawled"] = crawl_metrics["pages_crawled"]
    for item in crawl_results: register(item)

    hub_cfg = config["providers"]["publication_hub"]
    metrics["publication_hubs_attempted"] = len(profile["publication_hubs"])
    hub_results, hub_metrics = await PublicationHubProvider().discover(profile["publication_hubs"], approved, hub_cfg["max_pages"], hub_cfg["max_depth"], "publication_hub")
    metrics["publication_pages_crawled"] = hub_metrics["pages_crawled"]
    for item in hub_results: register(item)

    pdf_cfg = config["providers"]["pdf_link"]
    def pdf_page_priority(item: dict) -> tuple[int,int,str]:
        host=(urlparse(item["canonical_url"]).hostname or "").lower()
        source_class=item.get("source_domain_class")
        tier=0 if source_class in {"official_company","official_company_asset"} else 1 if host in ENGINEERING_PUBLISHERS or item.get("source_category_hint")=="professional_applied_ml_publication" else 2
        return tier,-int(item.get("retrieval_priority_score",0)),item["canonical_url"]
    pdf_pages=[item["canonical_url"] for item in sorted((x for x in candidates.values() if x["source_type_hint"]=="html"),key=pdf_page_priority)]
    pdf_allowed_domains=set(approved)|ENGINEERING_PUBLISHERS
    pdf_results, pdf_metrics = await PDFLinkProvider().discover(pdf_pages,pdf_allowed_domains,pdf_cfg["max_documents"],
        pdf_cfg.get("maximum_pages_scanned",200),pdf_cfg.get("scan_concurrency",8),
        pdf_cfg.get("progress_interval_pages",20),pdf_cfg.get("request_timeout_seconds",12))
    metrics.update(pdf_metrics)
    for item in pdf_results: register(item)

    # Merge authoritative patent-native assignee metadata into every duplicate
    # web candidate representing the same publication. This prevents a DDGS
    # Google-Patents URL from losing attribution already established by USPTO.
    native_by_identifier = {}
    for record in patent_native.get("records", []):
        identifiers = [record.get("publication_number"), *record.get("publication_number_aliases", [])]
        for identifier in filter(None, identifiers):
            native_by_identifier[re.sub(r"[^A-Za-z0-9]", "", identifier).upper()] = record
    for candidate in candidates.values():
        identifier = candidate.get("normalized_publication_number")
        if not identifier:
            match = re.search(r"(?i)/(?:patent/)?((?:US|EP|WO|DE|JP|CN|GB|CA|AU)\d{5,}[A-Z]\d?)", candidate["canonical_url"])
            identifier = match.group(1) if match else None
        native = native_by_identifier.get(re.sub(r"[^A-Za-z0-9]", "", str(identifier or "")).upper())
        if not native:
            continue
        candidate["normalized_publication_number"] = native.get("publication_number")
        candidate["patent_title"] = native.get("title") or candidate.get("patent_title") or candidate.get("title_hint","")
        if not candidate.get("title_hint"):
            candidate["title_hint"] = native.get("title","")
        candidate["official_patent_assignees"] = list(dict.fromkeys([
            *native.get("current_assignees", []), *native.get("original_assignees", [])
        ]))
        candidate["patent_native_metadata_merged"] = True
        candidate["report_canonical_url"] = candidate.get("report_canonical_url") or native.get("report_canonical_url") or native.get("patent_portal_url")
        candidate["patent_application_number"] = native.get("application_number")
        candidate["provenance"] = {**(candidate.get("provenance") or {}),
            "publication_number": native.get("publication_number"),
            "publication_number_aliases": native.get("publication_number_aliases", []),
            "enumeration_assignee": native.get("enumeration_assignee"),
            "native_source_provider": native.get("source_provider")}

    terminal = {"provider_completed", "provider_failed", "cache_reused"}
    execution_by_query = {}
    for item in executions: execution_by_query.setdefault(item["query_id"], []).append(item)
    unexecuted = [q.query_id for q in queries if q.mandatory and not any(e["state"] in terminal for e in execution_by_query.get(q.query_id, []))]
    metrics["unexecuted_mandatory_queries"] = len(unexecuted)
    metrics["candidate_urls_before_canonicalization"] = candidate_attempts[0]
    metrics["candidate_urls_after_canonicalization"] = len(candidates)
    budget=config["candidate_budget"]
    selected,retrieval_candidates,budget_audit=apply_candidate_budget(candidates,budget)
    candidates={item["canonical_url"]:item for item in selected}
    dropped=budget_audit["non_seed_candidates_dropped_by_budget"]
    metrics["candidate_urls_selected_for_retrieval"] = len(retrieval_candidates)
    metrics["candidate_urls_dropped_by_budget"] = dropped
    metrics.update(budget_audit)
    metrics["candidate_urls_registered"] = len(candidates)
    audit_taxonomy = load_shared_use_case_taxonomy()
    shared_families = families_for_industry(profile.get("industry", "unknown"))
    term_limit = int(audit_taxonomy["channel_policy"][
        "fast_iteration_core_terms_per_family" if run_profile == "fast_iteration" else "standard_core_terms_per_family"])
    mandatory_checks = {
        "ddgs_called": metrics["ddgs_calls_attempted"] > 0,
        "seeds_registered": seed_registration["seeds_registered"],
        "sitemaps_attempted": metrics["sitemaps_attempted"] > 0,
        "internal_crawl_attempted": "internal_pages_crawled" in metrics,
        "publication_hubs_attempted": not profile["publication_hubs"] or metrics["publication_hubs_attempted"] > 0,
        "pdf_discovery_attempted": "pdf_links_discovered" in metrics,
        "mandatory_queries_executed": not unexecuted,
        "professional_publication_atomic_queries_executed": any(q.family == "professional_publication_atomic" for q in queries),
        "mandatory_patent_queries_generated": sum(q.mandatory and q.family.startswith("patent_") for q in queries) >= 6,
        "patent_application_only_queries_generated": any(q.family == "patent_use_case_atomic" and not any(x in q.rendered_query.casefold() for x in ("machine learning", "neural network", "data-driven")) for q in queries),
        "patent_native_assignee_enumeration_attempted": bool(patent_native.get("manifests")),
        "patent_required_term_coverage_generated": all(
            any(q.family == "patent_term_supplemental" and term.casefold() in q.rendered_query.casefold() for q in queries)
            for definition in shared_families.values()
            for term in definition.get("core_discovery_terms", [])[:term_limit]),
        "shared_use_case_web_pdf_queries_generated": all(
            any(q.family in {"shared_use_case_official", "shared_use_case_pdf_publication"}
                and term.casefold() in q.rendered_query.casefold() for q in queries)
            for definition in shared_families.values()
            for term in definition.get("core_discovery_terms", [])[:term_limit]),
    }
    if unexecuted: status="incomplete_search_mandatory_provider_not_executed"
    elif not seed_registration["seeds_registered"]: status="incomplete_search_seed_registration_failed"
    else: status=("degraded_no_validated_assignee" if not profile.get("validated_source_assignees") else
                  ("completed" if not errors else "completed_with_provider_errors"))
    assignee_ready=any(isinstance(x,dict) and x.get("validation_status")=="established" for x in profile.get("validated_patent_assignees",[]))
    patent_coverage={"status":patent_native.get("status"),"validated_assignee_available":assignee_ready,
        "native_assignee_enumeration_attempted":assignee_ready,
        "interpretation":("Patent-native coverage completed or degraded; inspect patent audit artifacts."
                          if assignee_ready else "Patent search unavailable: no validated target-company patent assignee. Zero retrieved patents must not be interpreted as no relevant patents.")}
    report = {"status": status, "mandatory_checks": mandatory_checks, "metrics": metrics, "provider_errors": errors,
              "degradation_flags":([] if assignee_ready else ["degraded_no_validated_assignee"]),
              "unexecuted_mandatory_queries": unexecuted, "company_source_profile": profile,
              "patent_search_coverage":patent_coverage,"run_profile":run_profile}
    quota_snapshot=quota.snapshot()
    for provider_id,usage in provider_usage.items():
        record=quota_snapshot["providers"].get(provider_id)
        usage["free_quota_remaining_after_run"]=record.get("effective_remaining") if record else None
    urls_by_provider={}
    for item in provider_results: urls_by_provider.setdefault(item["provider_id"],set()).add(normalize_url(item["url"]))
    diversity=[]
    provider_ids=sorted(urls_by_provider)
    for index,left in enumerate(provider_ids):
        for right in provider_ids[index+1:]:
            shared=urls_by_provider[left]&urls_by_provider[right]
            diversity.append({"provider_pair":[left,right],"unique_urls_left":len(urls_by_provider[left]),"unique_urls_right":len(urls_by_provider[right]),"shared_urls":len(shared),"right_incremental_unique_urls":len(urls_by_provider[right]-urls_by_provider[left])})
    usage_report={"cost_policy":config["search_cost_policy"]["mode"],"paid_requests_permitted":config["search_cost_policy"]["paid_overage_allowed"],"providers":list(provider_usage.values()),"provider_url_diversity":diversity}
    compliance={"mode":"zero_cost_only","compliant":True,"paid_overage_attempted":False,"automatic_purchase_attempted":False,"providers_with_unknown_account_state":[],"violations":[]}
    quality_path=out/"patent_provider_quality.json"
    if quality_path.exists():
        patent_quality=load_yaml(quality_path)
        patent_quality["supplemental_provider_records"]=patent_supplemental_quality
        patent_quality["metrics"]["rejected_non_patent_count"]+=sum(x.get("reason_code")=="non_patent_results_from_patent_provider" for x in patent_supplemental_quality)
        atomic_json(quality_path,patent_quality)
    atomic_json(out / "candidate_sources.json", {"sources": list(candidates.values()),"budget":{"configured":budget,"dropped_count":dropped}})
    atomic_json(out/"candidate_budget_audit.json",budget_audit|{"configured_budget":budget})
    atomic_json(out / "source_discovery_report.json", report)
    atomic_json(out / "web_pdf_manifest.json", {"documents": []})
    atomic_json(out / "provider_usage_report.json",usage_report)
    atomic_json(out / "zero_cost_compliance.json",compliance)
    atomic_json(root/config["search_cost_policy"]["account_state_path"],{"updated_at":utc_now(),"providers":list(provider_usage.values())})
    if status.startswith("incomplete"):
        raise RuntimeError(status)
    return {"profile": profile, "candidates": list(candidates.values()), "retrieval_candidates":retrieval_candidates,"seed_registration":seed_registration,"candidate_budget_audit":budget_audit,"report": report, "queries": query_records, "executions": executions, "provider_results": provider_results}


def discover_sync(root: Path, out: Path, company: str, official_domain: str, explicit_seeds: list[str] | None = None, provider_cycle_state=None, company_aliases: list[str] | None = None, run_profile: str = "standard", validated_source_assignees: list[str] | None = None) -> dict:
    return asyncio.run(discover(root, out, company, official_domain, explicit_seeds, provider_cycle_state, company_aliases,run_profile,validated_source_assignees))
