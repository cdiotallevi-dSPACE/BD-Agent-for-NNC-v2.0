from bd_agent_neural_net_coder.nnc_domain import evaluate_nnc_gates, score_nnc_applicability


def test_generic_ai_does_not_pass_neural_gate():
    gates = evaluate_nnc_gates({"generic_machine_learning", "microcontroller", "model_conversion"})
    score, _ = score_nnc_applicability(gates, 1.0)
    assert not gates["neural_network_gate"]["passed"]
    assert score <= 15


def test_confirmed_nn_mcu_and_onnx_pass_core_gates():
    gates = evaluate_nnc_gates({"convolutional_neural_network", "microcontroller", "onnx_model", "resource_constraints"})
    score, components = score_nnc_applicability(gates, 0.9)
    assert gates["positive_applicability_candidate"]
    assert score >= 80
    assert components["embedded_target"] == 25


def test_cloud_only_and_competitor_controls():
    cloud = evaluate_nnc_gates({"neural_network", "onnx_model", "cloud_or_server_target"})
    cloud_score, _ = score_nnc_applicability(cloud, 1.0)
    competitor = evaluate_nnc_gates({"neural_network", "microcontroller", "onnx_model", "direct_competitor"})
    competitor_score, _ = score_nnc_applicability(competitor, 1.0)
    assert cloud_score <= 25
    assert competitor["company_role_gate"]["role"] == "competitor"
    assert competitor_score == 0


def test_silicon_vendor_routes_to_partner_band():
    gates = evaluate_nnc_gates({"neural_network", "microcontroller", "onnx_model", "silicon_vendor", "model_optimization"})
    score, _ = score_nnc_applicability(gates, 1.0)
    assert gates["company_role_gate"]["role"] == "partner_or_ecosystem"
    assert score <= 60
