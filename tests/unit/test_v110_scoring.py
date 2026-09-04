from bd_agent_neural_net_coder.nnc_scoring import aggregate_company_scores, relevance_band, score_patent_use_case


def test_gm_tractive_limit_scores_55_without_onnx_reset():
    analysis = {
        "patent_neural_evidence_strength": "claimed_optional_embodiment",
        "use_case_classes": ["vehicle_dynamics_learned_estimation"],
        "algorithm_roles": {"estimator": ["neural_network_estimator"], "learning_or_adaptation_agent": []},
        "onboard_context": "confirmed",
    }
    text = ("A neural network regression model estimates the tractive limit. The algorithm can be implemented "
            "by a programmable electronic control unit.")
    result = score_patent_use_case(analysis, text)
    assert result["company_neural_application"]["points"] == 45
    assert result["edge_deployment_intent"]["points"] == 10
    assert result["deployment_workflow_fit"]["points"] == 0
    assert result["use_case_score"] == 55
    assert result["mapping_class"] == "nnc_influence_opportunity"
    assert result["mapping_eligible"] is True


def test_gm_predictive_battery_scores_65_without_onnx_reset():
    analysis = {
        "patent_neural_evidence_strength": "confirmed_required_or_implemented",
        "use_case_classes": ["battery_virtual_measurement_and_predictive_control"],
        "algorithm_roles": {"estimator": ["neural_network_estimator"],
                            "learning_or_adaptation_agent": ["neural_network_learning_agent"]},
        "onboard_context": "confirmed",
    }
    text = ("A neural network learning agent estimates anode voltage for predictive battery charging. "
            "Real-time operation is performed by an onboard charging module.")
    result = score_patent_use_case(analysis, text)
    assert result["company_neural_application"]["points"] == 50
    assert result["edge_deployment_intent"]["points"] == 15
    assert result["use_case_score"] == 65
    assert result["mapping_class"] == "nnc_deployment_fit"


def test_company_aggregation_is_best_case_plus_breadth_not_sum():
    evidence = [
        {"evidence_id": "E1", "source_id": "S1", "use_case_classes": ["vehicle_dynamics_learned_estimation"],
         "nnc_use_case_scoring": {"use_case_score": 55}},
        {"evidence_id": "E2", "source_id": "S2", "use_case_classes": ["battery_virtual_measurement_and_predictive_control"],
         "nnc_use_case_scoring": {"use_case_score": 65}},
        {"evidence_id": "E3", "source_id": "S3", "use_case_classes": ["battery_virtual_measurement_and_predictive_control"],
         "nnc_use_case_scoring": {"use_case_score": 60}},
    ]
    result = aggregate_company_scores(evidence)
    assert result["base_score"] == 65
    assert result["opportunity_breadth_bonus"] == 10
    assert result["overall_product_match"] == 75
    assert result["rating"] == "high_nnc_relevance"


def test_relevance_boundaries():
    assert [relevance_band(x) for x in (19, 20, 39, 40, 64, 65, 84, 85, 100)] == [
        "low_relevance", "emerging_ml_opportunity", "emerging_ml_opportunity",
        "medium_nnc_relevance", "medium_nnc_relevance", "high_nnc_relevance",
        "high_nnc_relevance", "maximum_nnc_potential_fit", "maximum_nnc_potential_fit",
    ]


def test_edge_adjacency_alone_cannot_create_product_fit():
    analysis={"patent_neural_evidence_strength":"absent","use_case_classes":["battery_health_and_state_estimation"],
              "algorithm_roles":{"estimator":[],"learning_or_adaptation_agent":[]},"onboard_context":"confirmed"}
    result=score_patent_use_case(analysis,"The controller performs charging control for a battery system.")
    assert result["company_neural_application"]["points"]==0
    assert result["deployment_workflow_fit"]["points"]==0
    assert result["edge_deployment_intent"]["points"]==5
    assert result["score_eligible"] is False
    assert result["use_case_score"]==0
    assert result["score_exclusion_reason"]=="edge_context_without_neural_or_workflow_signal"


def test_explicit_sensorless_estimator_remains_low_score_neural_substitution_candidate():
    analysis={"patent_neural_evidence_strength":"absent","use_case_classes":["indirect_physical_state_and_virtual_sensing"],
              "algorithm_roles":{"estimator":[],"learning_or_adaptation_agent":[]},"onboard_context":"confirmed"}
    result=score_patent_use_case(analysis,"A controller estimates rotor temperature from rotor resistance without using temperature sensors.")
    assert result["company_neural_application"]["classification"]=="indirect_physical_estimator_neural_candidate"
    assert result["company_neural_application"]["points"]==15
    assert result["score_eligible"] is True
    assert result["use_case_score"]==20


def test_contextual_company_evidence_is_not_aggregated_even_with_preliminary_score():
    evidence=[{"evidence_id":"E1","source_id":"SRC-0090","use_case_classes":["battery_health_and_state_estimation"],
               "relevance_class":"contextual_company_evidence","relevant_evidence_eligible":False,
               "nnc_use_case_scoring":{"use_case_score":5,"score_eligible":True}}]
    assert aggregate_company_scores(evidence)["use_cases"]==[]
