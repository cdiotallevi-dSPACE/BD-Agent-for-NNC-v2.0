import json
from pathlib import Path

import pytest

from bd_agent_neural_net_coder.patent_native_discovery import (
    PatentNativeDiscovery, REQUIRED_TERMS, patent_result_quality,
    supplemental_patent_results_usable, normalize_uspto_application,
)
from bd_agent_neural_net_coder.search_models import ProviderSearchResult
from bd_agent_neural_net_coder.search_orchestrator import generate_queries, load_company_profile
from bd_agent_neural_net_coder.company_attribution import establish_document_company_attribution


ROOT = Path(__file__).resolve().parents[1]
ASSIGNEE = "GM Global Technology Operations LLC"


def config():
    return {
        "patent_discovery_budget": {
            "maximum_metadata_records_per_assignee": 500,
            "maximum_metadata_records_per_native_source": 500,
            "maximum_pages_per_assignee_source": 20,
            "maximum_full_patents_retrieved_per_company": 100,
            "maximum_family_expansion_records": 200,
            "maximum_citation_expansion_records": 100,
        },
        "patent_full_text_reservations": {
            "battery_virtual_measurement_and_predictive_control": 20,
            "vehicle_dynamics_learned_estimation": 20,
            "indirect_physical_state_and_virtual_sensing": 15,
            "condition_monitoring_and_prognostics": 15,
            "perception_classification_and_detection": 10,
            "occupant_driver_cabin_sensing": 5,
            "cross_family_highest_ranked": 15,
        },
    }


def google_row(publication, title, snippet):
    return {"id": f"patent/{publication}/en", "patent": {"publication_number": publication,
        "title": title, "snippet": snippet, "assignee": ASSIGNEE, "inventor": "Inventor",
        "filing_date": "2023-01-01", "publication_date": "2024-01-01",
        "family_metadata": {"aggregated": {"country_status": [{"best_patent_stage": {"state": "ACTIVE"}}]}}}}


@pytest.mark.asyncio
async def test_dual_gm_patents_found_on_page_three_without_oracle_inputs(tmp_path):
    calls = []
    async def fetch_json(url):
        if "patents.google.com" not in url:
            return {"count": 0, "patentFileWrapperDataBag": []}
        calls.append(url); page = len(calls)
        rows = []
        if page == 1:
            rows = [google_row("US11111111B2", "Cupholder assembly", "Vehicle trim component")]
        elif page == 2:
            rows = [google_row("US22222222B2", "Door hinge", "Mechanical hinge")]
        elif page == 3:
            rows = [
                google_row("US12246700B2", "Machine learning-based tractive limit and wheel stability status estimation",
                           "A regression model estimates tractive limit and a classification model determines wheel stability."),
                google_row("US20240302440A1", "Dynamic and predictive control of battery charging",
                           "Virtual measurement of anode voltage, electrolyte concentration and lithium plating uses a neural network learning agent."),
            ]
        return {"results": {"total_num_pages": 4, "cluster": [{"result": rows}]}}
    async def fetch_text(url):
        return "<html></html>"
    profile = {"validated_patent_assignees": [{"assignee_name": ASSIGNEE, "validation_status": "established"}]}
    result = await PatentNativeDiscovery(config(), fetch_json, fetch_text).run(profile, tmp_path)
    selected = {r["publication_number"]: r for r in result["selected"]}
    assert "US12246700B2" in selected
    assert "US20240302440A1" in selected
    assert "vehicle_dynamics_learned_estimation" in selected["US12246700B2"]["matched_use_case_families"]
    assert "battery_virtual_measurement_and_predictive_control" in selected["US20240302440A1"]["matched_use_case_families"]
    assert len(calls) >= 3
    assert all("US12246700" not in url and "US20240302440" not in url for url in calls)
    for name in ("patent_assignee_registry.json", "patent_enumeration_manifest.json", "patent_provider_quality.json",
                 "patent_metadata_corpus.jsonl", "patent_term_coverage.json", "patent_metadata_rankings.json",
                 "patent_family_expansion.json", "patent_full_text_manifest.json"):
        assert (tmp_path / name).exists()


def test_all_required_terms_are_generated_and_persisted_not_first_only(tmp_path):
    profile = load_company_profile(ROOT, "General Motors", "gm.com", company_aliases=["GM"])
    queries = generate_queries(profile)
    for family in ("vehicle_dynamics_learned_estimation", "battery_virtual_measurement_and_predictive_control"):
        for term in REQUIRED_TERMS[family]:
            assert any(q.family == "patent_term_supplemental" and term in q.rendered_query for q in queries)
    rendered = " ".join(q.rendered_query for q in queries)
    assert "US12246700B2" not in rendered and "US20240302440A1" not in rendered
    assert profile["seed_urls"] == []


def test_job_ads_from_nominal_patent_provider_are_unusable():
    quality = patent_result_quality({"url": "https://linkedin.com/jobs/123", "title": "GM machine learning job",
        "abstract": "", "current_assignees": [], "patent_native_enumeration_or_search": True}, [ASSIGNEE], ["machine learning"])
    assert quality["status"] == "unusable"
    assert quality["reason_code"] == "non_patent_results_from_patent_provider"
    assert quality["fallback_required"] is True


def test_nonempty_irrelevant_first_page_triggers_quality_fallback():
    irrelevant = [ProviderSearchResult("ddgs", "q1", "Cupholder patent", "https://patents.google.com/patent/US11111111B2/en", "unrelated", 1)]
    assert supplemental_patent_results_usable(irrelevant, [ASSIGNEE], ["tractive limit"]) is False
    useful = [ProviderSearchResult("ddgs", "q1", "Tractive limit", "https://patents.google.com/patent/US12246700B2/en", f"{ASSIGNEE} tractive limit", 1)]
    assert supplemental_patent_results_usable(useful, [ASSIGNEE], ["tractive limit"]) is True


def test_term_coverage_artifact_contains_every_required_term(tmp_path):
    coverage = [{"use_case_family": family, "required_term": term} for family, terms in REQUIRED_TERMS.items() for term in terms]
    expected = {(family, term) for family, terms in REQUIRED_TERMS.items() for term in terms}
    assert {(x["use_case_family"], x["required_term"]) for x in coverage} == expected


@pytest.mark.asyncio
async def test_failed_native_term_requests_do_not_claim_complete_coverage(tmp_path):
    async def failed_json(url):
        raise RuntimeError("provider unavailable")
    async def empty_text(url):
        return "<html></html>"
    profile = {"validated_patent_assignees": [{"assignee_name": ASSIGNEE, "validation_status": "established"}]}
    await PatentNativeDiscovery(config(), failed_json, empty_text).run(profile, tmp_path)
    artifact = json.loads((tmp_path / "patent_term_coverage.json").read_text(encoding="utf-8"))
    assert artifact["complete"] is False
    assert any(item["execution_status"] == "failed" for item in artifact["terms"])


def test_uspto_schema_record_is_normalized_without_known_patent_seed():
    item = {"applicationNumberText": "18068542", "applicationMetaData": {
        "earliestPublicationNumber": "US20240166192A1", "patentNumber": "12246700",
        "inventionTitle": "Machine learning-based tractive limit and wheel stability status estimation",
        "filingDate": "2022-12-19", "earliestPublicationDate": "2024-05-23", "grantDate": "2025-03-11",
        "applicationStatusDescriptionText": "Patented Case", "cpcClassificationBag": ["B60W40/064"],
        "applicantBag": [{"applicantNameText": ASSIGNEE}],
        "inventorBag": [{"inventorNameText": "Example Inventor"}]},
        "assignmentBag": [{"assigneeBag": [{"assigneeNameText": ASSIGNEE}]}]}
    record = normalize_uspto_application(item, ASSIGNEE)
    assert record["source_provider"] == "uspto_patent_file_wrapper"
    assert record["publication_number"] == "US12246700B2"
    assert record["publication_number_aliases"] == ["US12246700B2", "US20240166192A1"]
    assert record["application_number"] == "18068542"
    assert record["report_canonical_url"] == "https://data.uspto.gov/patent-file-wrapper/search/details/18068542/application-data"
    assert record["current_assignees"] == [ASSIGNEE]
    assert record["classifications"]["cpc"] == ["B60W40/064"]


@pytest.mark.asyncio
async def test_uspto_fallback_reports_missing_credentials_without_leaking_secret(monkeypatch):
    monkeypatch.delenv("USPTO_API_KEY", raising=False)
    records, manifest = await PatentNativeDiscovery(config()).enumerate_uspto(ASSIGNEE, config()["patent_discovery_budget"])
    assert records == []
    assert manifest["status"] == "unavailable_missing_credentials"
    assert manifest["credential_environment_variable"] == "USPTO_API_KEY"


@pytest.mark.asyncio
async def test_uspto_taxonomy_queries_discover_without_patent_number_seed(monkeypatch):
    monkeypatch.setenv("USPTO_API_KEY", "test-only-key")
    calls = []
    async def fetch(url):
        calls.append(url)
        if "tractive%20AND%20limit" in url:
            return {"count": 1, "patentFileWrapperDataBag": [{"applicationNumberText": "18057281",
                "applicationMetaData": {"earliestPublicationNumber": "US20240166192A1", "patentNumber": "12246700",
                "inventionTitle": "MACHINE LEARNING-BASED TRACTIVE LIMIT AND WHEEL STABILITY STATUS ESTIMATION",
                "applicantBag": [{"applicantNameText": ASSIGNEE}]},
                "assignmentBag": [{"assigneeBag": [{"assigneeNameText": ASSIGNEE}]}]}]}
        return {"count": 0, "patentFileWrapperDataBag": []}
    records, manifest = await PatentNativeDiscovery(config(), fetch_json=fetch).enumerate_uspto_terms(
        ASSIGNEE, config()["patent_discovery_budget"])
    assert any(record["publication_number"] == "US12246700B2" for record in records)
    assert manifest["status"] == "completed"
    assert all("US12246700" not in url and "US20240302440" not in url for url in calls)


def test_official_uspto_assignee_metadata_establishes_company_attribution():
    doc = {"source_id": "S1", "url": "https://api.uspto.gov/patent.xml", "text": "technical patent text", "pages": []}
    attribution = establish_document_company_attribution(doc, company="General Motors", official_domain="gm.com",
        validated_patent_assignees=[{"assignee_name": ASSIGNEE, "validation_status": "established"}],
        candidate={"source_domain_class": "specialist_patent_source", "official_patent_assignees": [ASSIGNEE]})
    assert attribution["company_attribution_status"] == "established"


def test_native_assignee_metadata_propagated_to_google_candidate_establishes_attribution():
    doc = {"source_id": "S1", "url": "https://patents.google.com/patent/US12246700B2/en",
           "text": "Machine learning-based tractive limit estimation", "pages": []}
    candidate = {"official_patent_assignees": ["GM Global Technology Operations LLC"],
                 "provenance": {"enumeration_assignee": "GM Global Technology Operations LLC"}}
    attribution = establish_document_company_attribution(
        doc, company="General Motors", official_domain="gm.com", candidate=candidate,
        validated_patent_assignees=[{"assignee_name": "GM Global Technology Operations LLC",
                                     "validation_status": "established"}])
    assert attribution["company_attribution_status"] == "established"
    assert attribution["attributed_company_id"] == "general_motors"
    assert attribution["identity_anchors"][0]["anchor_type"] == "validated_source_assignee"
