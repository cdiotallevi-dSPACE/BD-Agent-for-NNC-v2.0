from bd_agent_neural_net_coder.nnc_scoring import aggregate_company_scores, score_patent_use_case
from bd_agent_neural_net_coder.pipeline import calculate_cycle_source_counts, consolidate_use_case_mappings
from bd_agent_neural_net_coder.report_generator import _display_evidence_description
from bd_agent_neural_net_coder.search_orchestrator import classify_domain

def test_google_patents_is_always_specialist_and_approved_counter_uses_category():
    assert classify_domain("https://patents.google.com/patent/US1/en",{})=="specialist_patent_source"
    sources=[{"source_id":"SRC-0001","url":"https://patents.google.com/patent/US1/en","source_type":"html","content_hash":"x","retrieval_status":"retrieved","source_domain_class":"third_party_analytics"}]
    relevant={"relevant_evidence":[{"source_id":"SRC-0001","source_category":"target_company_patent"}]}
    assert calculate_cycle_source_counts(sources,relevant)["total_retrieved_and_approved_patents"]==1

def test_sensorless_physical_estimator_gets_low_nonzero_fit_without_mapping():
    analysis={"use_case_classes":["indirect_physical_state_and_virtual_sensing"],"patent_neural_evidence_strength":"absent","algorithm_roles":{},"onboard_context":"unconfirmed"}
    result=score_patent_use_case(analysis,"A sensorless method estimates rotor temperature from rotor resistance without using temperature sensors.")
    assert result["use_case_score"]==15
    assert result["mapping_eligible"] is False

def test_unclassified_source_ids_do_not_become_use_cases_and_descriptions_are_complete():
    evidence=[{"evidence_id":"E1","source_id":"SRC-0106","use_case_classes":[],"nnc_use_case_scoring":{"use_case_score":15}}]
    assert aggregate_company_scores(evidence)["use_cases"]==[]
    statement="A complete evidence statement that must remain complete."
    assert _display_evidence_description(statement)==statement

def test_mapping_consolidation_separates_customer_adoption_from_product_capability():
    mappings=[{"mapping_id":f"OLD-{i}","use_case_id":"battery_state_estimation","target_company_entity_id":"battery","dspace_applicability_score":60,"dspace_commercial_name":"Neural Net Coder","nnc_use_case_scoring":{"deployment_readiness":{"onnx_adoption":"unconfirmed","generated_code_workflow":"unconfirmed"}}} for i in range(7)]
    result=consolidate_use_case_mappings(mappings)
    assert len(result)==1
    assert "unconfirmed" in result[0]["customer_evidence_and_readiness"]
    assert "potential" in result[0]["nnc_product_capability"].casefold()
