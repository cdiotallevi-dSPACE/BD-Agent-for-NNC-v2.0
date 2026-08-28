from pathlib import Path

from bd_agent_neural_net_coder.company_attribution import establish_document_company_attribution
from bd_agent_neural_net_coder.config_manager import load_yaml
from bd_agent_neural_net_coder.evidence_context import extract_document_evidence
from bd_agent_neural_net_coder.relevant_evidence_builder import build_relevant_evidence
from bd_agent_neural_net_coder.search_orchestrator import generate_queries

ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = load_yaml(ROOT / "config/domains/tiny_edge_ai/company_domain_taxonomy.yaml")
URL = "https://saemobilus.sae.org/papers/methodology-recognize-vehicle-loading-condition-indirect-method-using-telematics-machine-learning-2019-26-0019"


def test_mahindra_sae_source_is_opportunity_not_mapping_evidence():
    text = ("Authors are affiliated with Mahindra Research Valley. This technical paper develops a supervised "
            "machine learning model for real-time vehicle loading condition recognition from vehicle driving "
            "behavior and telematics units, with ADAS and maintenance applications.")
    doc = {"source_id":"SRC-0001", "url":URL, "requested_url":URL,
           "title":"Methodology to Recognize Vehicle Loading Condition", "pages":[{"page":1,"text":text}]}
    attribution = establish_document_company_attribution(doc, company="Mahindra & Mahindra Limited",
        official_domain="mahindra.com", company_aliases=["Mahindra"],
        candidate={"source_domain_class":"third_party_analytics"})
    assert attribution["company_attribution_status"] == "established"
    assert any(a["anchor_type"] == "corporate_organizational_unit_affiliation" for a in attribution["identity_anchors"])
    result = extract_document_evidence(doc, TAXONOMY, attribution)
    opportunity = [e for e in result["accepted"] if e["relevance_class"] == "nnc_opportunity_evidence"]
    assert opportunity
    assert not any(e["mapping_eligibility"]["eligible"] for e in opportunity)
    relevant = build_relevant_evidence(result["accepted"], [{"source_id":"SRC-0001","url":URL,
        "title":doc["title"],"source_type":"html","source_domain_class":"third_party_analytics"}], [])
    assert relevant["source_count"] == 1
    item = relevant["relevant_evidence"][0]
    assert item["relevance_class"] == "nnc_opportunity_evidence"
    assert item["product_fit_score_contribution"] == 0
    assert not item["mapping_eligible"]
    assert "not disclosed" in item["description"]


def test_applied_ml_queries_are_mandatory_and_seedless():
    profile={"company_name":"Mahindra & Mahindra Limited","company_aliases":["Mahindra"],
             "official_domains":["mahindra.com"],"official_asset_domains":[],"related_corporate_domains":[],
             "partner_domains":[],"specialist_domains":[]}
    queries=generate_queries(profile)
    applied=[q for q in queries if q.family == "applied_ml_research"]
    assert len(applied) >= 4
    assert all(q.mandatory and "ddgs" in q.target_provider_ids for q in applied)
    assert any("saemobilus.sae.org" in q.rendered_query for q in applied)


def test_ambiguous_gm_unit_name_does_not_establish_attribution():
    text="The authors list GM Labs. The paper develops a supervised machine learning model for real-time vehicle estimation."
    doc={"source_id":"SRC-X","url":"https://example.org/paper","pages":[{"page":1,"text":text}]}
    attr=establish_document_company_attribution(doc, company="General Motors", official_domain="gm.com",
        company_aliases=["GM"], candidate={"source_domain_class":"third_party_analytics"})
    assert attr["company_attribution_status"] == "not_established"
