from pathlib import Path

from bd_agent_neural_net_coder.company_attribution import establish_document_company_attribution
from bd_agent_neural_net_coder.evidence_context import analyze_patent, classify_source_category, extract_document_evidence
from bd_agent_neural_net_coder.search_orchestrator import candidate_retrieval_priority, generate_queries, load_company_profile


ROOT = Path(__file__).resolve().parents[1]


def gm_profile():
    return load_company_profile(ROOT, "General Motors", "gm.com", company_aliases=["General Motors Company", "GMC", "GM"],
        validated_source_assignees=["GM Global Technology Operations LLC"])


def test_v16_v17_generate_generic_patent_discovery_without_oracle_seed():
    profile = gm_profile()
    queries = generate_queries(profile)
    patent = [q for q in queries if q.family.startswith("patent_")]
    assert sum(q.mandatory for q in patent) >= 6
    assert any(q.family == "patent_use_case_atomic" and '"battery charging"' in q.rendered_query and "machine learning" not in q.rendered_query.casefold() for q in patent)
    assert any("GM Global Technology Operations LLC" in q.rendered_query and "patents.google.com" in q.rendered_query for q in patent)
    assert any("G01R31/392" in q.rendered_query for q in patent)
    assert all("US12246700" not in q.rendered_query and "US20240302440" not in q.rendered_query for q in queries)
    assert profile["seed_urls"] == []


def test_patent_candidates_receive_pre_retrieval_priority():
    profile = gm_profile()
    patent = {"title_hint": "Dynamic and predictive control of battery charging", "snippet": "GM Global Technology Operations LLC", "canonical_url": "https://patents.google.com/patent/example/en"}
    generic = {"title_hint": "General Motors annual report", "snippet": "company overview", "canonical_url": "https://example.org/annual-report"}
    assert candidate_retrieval_priority(patent, profile)[0] > candidate_retrieval_priority(generic, profile)[0]


def patent_doc(text: str, url: str) -> dict:
    return {"source_id": "SRC-0001", "url": url, "title": "Patent", "pages": [{"page": 1, "text": text}]}


def attribution(doc):
    return establish_document_company_attribution(doc, company="General Motors", official_domain="gm.com",
        company_aliases=["General Motors Company", "GMC", "GM"],
        validated_source_assignees=gm_profile()["validated_source_assignees"], candidate={"source_domain_class": "third_party_analytics"})


def test_v16_tractive_limit_patent_attribution_and_semantics():
    text = """Assignee: GM Global Technology Operations LLC. A controller and electronic control unit uses onboard sensors.
    A machine learning regression model estimates a tractive limit and a classification model determines wheel stability,
    wheel slip, and tire saturation. Dependent claim 3: wherein the regression algorithm comprises a neural network."""
    doc = patent_doc(text, "https://patents.google.com/patent/US12246700B2/en")
    attr = attribution(doc)
    analysis = analyze_patent(text)
    assert attr["company_attribution_status"] == "established"
    assert attr["identity_anchors"][0]["anchor_type"] == "validated_source_assignee"
    assert classify_source_category(doc, text, attr) == "target_company_patent"
    assert analysis["patent_neural_evidence_strength"] == "claimed_optional_embodiment"
    assert analysis["applied_ml_activity"] == {"regression_model": "confirmed", "classification_model": "confirmed"}
    assert "vehicle_dynamics_learned_estimation" in analysis["use_case_classes"]
    assert analysis["onboard_context"] == "confirmed"


def test_v17_predictive_battery_patent_role_aware_semantics():
    text = """Assignee: GM Global Technology Operations LLC. Dynamic and predictive control of battery charging executes in
    a RESS controller, onboard charging module OBCM, and battery management controller BMS. Virtual measurements include
    anode voltage, electrolyte concentration, capacity loss, an aging parameter and a lithium plating limit. A hybrid
    physics-based and data-driven neural network estimator estimates internal battery state. A learning agent implemented
    using a neural network periodically updates adaptive calibration. An EKF and model predictive controller are alternatives."""
    doc = patent_doc(text, "https://patents.google.com/patent/US20240302440A1/en")
    attr = attribution(doc)
    analysis = analyze_patent(text)
    assert attr["company_attribution_status"] == "established"
    assert analysis["patent_neural_evidence_strength"] == "confirmed_required_or_implemented"
    assert "battery_virtual_measurement_and_predictive_control" in analysis["use_case_classes"]
    assert all(value == "confirmed" for value in analysis["virtual_measurements"].values())
    assert "neural_network_estimator" in analysis["algorithm_roles"]["estimator"]
    assert "neural_network_learning_agent" in analysis["algorithm_roles"]["learning_or_adaptation_agent"]
    assert analysis["onboard_context"] == "confirmed"


def test_v110_claimed_neural_estimator_creates_influence_mapping_without_onnx():
    text = """GM Global Technology Operations LLC patent. A machine learning regression model estimates tractive limit
    and wheel stability using an onboard ECU. Dependent claim: wherein the method may comprise a neural network."""
    doc = patent_doc(text, "https://patents.google.com/patent/example/en")
    attr = attribution(doc)
    taxonomy = {"terms": [{"term_id": "neural_network", "name": "neural network", "aliases": []}]}
    result = extract_document_evidence(doc, taxonomy, attr)
    assert result["accepted"]
    record = result["accepted"][0]
    assert record["relevance_class"] == "nnc_applicability_evidence"
    assert record["relevant_evidence_eligible"] is True
    assert record["mapping_eligibility"]["eligible"] is True
    # "using an onboard ECU" establishes embedded adjacency (5), while the
    # exact GM patent adds the stronger implementable-on-ECU language (10).
    assert record["score_contribution"] == 50
    assert record["mapping_class"] == "nnc_influence_opportunity"
