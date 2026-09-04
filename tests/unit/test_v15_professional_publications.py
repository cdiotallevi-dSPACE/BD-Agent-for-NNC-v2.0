from pathlib import Path

from bd_agent_neural_net_coder.company_attribution import establish_document_company_attribution
from bd_agent_neural_net_coder.config_manager import load_yaml
from bd_agent_neural_net_coder.evidence_context import extract_document_evidence
from bd_agent_neural_net_coder.relevant_evidence_builder import build_relevant_evidence
from bd_agent_neural_net_coder.search_orchestrator import (
    GENERAL_WEB_FALLBACK, apply_candidate_budget, candidate_retrieval_priority, generate_queries, load_company_profile,
)

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = load_yaml(ROOT / "config/domains/tiny_edge_ai/company_domain_taxonomy.yaml")
URL = "https://saemobilus.sae.org/papers/methodology-recognize-vehicle-loading-condition-indirect-method-using-telematics-machine-learning-2019-26-0019"


def _profile():
    return {"company_name":"Mahindra & Mahindra Limited", "company_aliases":["Mahindra"],
            "official_domains":["mahindra.com"], "official_asset_domains":[], "related_corporate_domains":[],
            "partner_domains":[], "specialist_domains":[], "company_research_affiliations":[], "seed_urls":[]}


def test_atomic_sae_queries_are_generic_mandatory_and_seedless():
    queries = generate_queries(_profile())
    atomic = [q for q in queries if q.family == "professional_publication_atomic"]
    rendered = {q.rendered_query for q in atomic}
    assert 'site:saemobilus.sae.org/papers Mahindra telematics' in rendered
    assert 'site:saemobilus.sae.org/papers Mahindra "loading condition"' in rendered
    assert all(q.mandatory and q.target_provider_ids == GENERAL_WEB_FALLBACK for q in atomic)
    assert all(URL not in q.rendered_query for q in queries)


def test_validated_research_affiliation_expands_queries_without_seed():
    profile=load_company_profile(ROOT,"Mahindra & Mahindra Limited","mahindra.com")
    rendered={q.rendered_query for q in generate_queries(profile)}
    assert 'site:saemobilus.sae.org/papers "Mahindra Research Valley" "machine learning"' in rendered
    assert '"Mahindra Research Valley" SAE "machine learning"' in rendered
    assert profile["seed_urls"] == []


def test_sae_candidate_outranks_generic_annual_report():
    profile = _profile()
    sae = {"canonical_url":URL, "title_hint":"Methodology to Recognize Vehicle Loading Condition - An Indirect Method Using Telematics and Machine Learning",
           "snippet":"Vaisakh Venugopal, Mahindra Research Valley. Supervised machine learning model for real-time loading condition recognition.",
           "source_domain_class":"third_party_analytics", "source_type_hint":"html", "protected_for_retrieval":False}
    annual = {"canonical_url":"https://mahindra.com/annual-report.pdf", "title_hint":"Mahindra Annual Report",
              "snippet":"Corporate overview", "source_domain_class":"official_company", "source_type_hint":"pdf", "protected_for_retrieval":False}
    for item in (sae, annual):
        item["retrieval_priority_score"], item["retrieval_priority_reasons"] = candidate_retrieval_priority(item, profile)
    budget={"maximum_non_seed_candidates_per_host":10,"maximum_career_pages_per_company":10,
            "maximum_low_priority_third_party_pages":10,"maximum_canonical_non_seed_candidates_per_company":10,
            "maximum_retrieved_non_seed_documents_per_company":1}
    _, retrieval, _ = apply_candidate_budget({sae["canonical_url"]:sae, annual["canonical_url"]:annual}, budget)
    # The v1.10 retrieval contract gives target-company web sources first;
    # publisher evidence remains next in the ranked web pool.
    assert retrieval[0]["canonical_url"] == annual["canonical_url"]
    assert "professional_applied_ml_publication" in sae["retrieval_priority_reasons"]


def test_mahindra_sae_fixture_classifies_as_score_neutral_opportunity():
    text = ("Vaisakh Venugopal, Paul Raj Bob and Vipin Nair — Mahindra Research Valley. "
            "A supervised machine learning model is developed to recognize real-time vehicle loading condition "
            "by analyzing vehicle driving behavior. The low-cost method leverages telematics units and can optimize ADAS functions.")
    doc={"source_id":"SRC-0001","url":URL,"requested_url":URL,
         "title":"Methodology to Recognize Vehicle Loading Condition - An Indirect Method Using Telematics and Machine Learning",
         "pages":[{"page":1,"text":text}]}
    attribution=establish_document_company_attribution(doc,company="Mahindra & Mahindra Limited",
        official_domain="mahindra.com",company_aliases=["Mahindra"],candidate={"source_domain_class":"third_party_analytics"})
    result=extract_document_evidence(doc,TAXONOMY,attribution)
    opportunities=[e for e in result["accepted"] if e["relevance_class"]=="nnc_opportunity_evidence"]
    assert attribution["company_attribution_status"] == "established"
    assert opportunities and all(not e["mapping_eligibility"]["eligible"] and e["score_contribution"]==0 for e in opportunities)
    assert any(e["source_category"]=="professional_applied_ml_publication" for e in opportunities)
    assert any("indirect_physical_state_and_virtual_sensing" in e["use_case_classes"] for e in opportunities)
    relevant=build_relevant_evidence(result["accepted"],[{"source_id":"SRC-0001","url":URL,"title":doc["title"],
        "source_type":"html","source_domain_class":"third_party_analytics"}],[])
    assert relevant["source_count"]==0
    assert relevant["background_source_count"]==1
    assert relevant["company_background_evidence"][0]["source_category"]=="professional_applied_ml_publication"
