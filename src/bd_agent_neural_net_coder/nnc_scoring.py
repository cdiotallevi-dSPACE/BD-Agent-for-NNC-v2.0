"""Version 1.10 deterministic NNC use-case and company scoring."""
from __future__ import annotations

from collections import defaultdict


NEURAL_LEVELS = {
    "neural_network_actually_used_for_parameter_estimation": 55,
    "neural_network_explicit_operational_embodiment": 50,
    "neural_network_explicitly_claimed_for_parameter_estimation": 45,
    "neural_network_optional_but_semantically_connected_to_estimator": 35,
    "generic_machine_learning_estimator_without_neural_confirmation": 20,
    "indirect_physical_estimator_neural_candidate": 15,
    "generic_neural_network_mention": 5,
    "no_neural_or_machine_learning_method": 0,
}
EDGE_LEVELS = {
    "deployed_on_mcu_ecu_soc_or_edge_ai_device": 25,
    "target_edge_hardware_explicitly_selected": 22,
    "implementation_on_onboard_controller_explicit": 18,
    "real_time_onboard_execution_explicit": 15,
    "implementable_on_ecu_or_controller": 10,
    "embedded_adjacent_physical_application_only": 5,
    "no_edge_deployment_decision_disclosed": 0,
}
WORKFLOW_LEVELS = {
    "onnx_plus_generated_embedded_code": 20,
    "onnx_plus_explicit_edge_deployment": 17,
    "generated_c_or_cpp_from_neural_model": 15,
    "onnx_model_adoption": 12,
    "onnx_exportability_or_compatible_model_handover_confirmed": 10,
    "model_conversion_or_embedded_ai_toolchain": 8,
    "framework_known_and_likely_exportable": 5,
    "no_public_workflow_evidence": 0,
}


def relevance_band(score: int) -> str:
    if score >= 85:
        return "maximum_nnc_potential_fit"
    if score >= 65:
        return "high_nnc_relevance"
    if score >= 40:
        return "medium_nnc_relevance"
    if score >= 20:
        return "emerging_ml_opportunity"
    return "low_relevance"


def _workflow_level(text: str) -> str:
    fold = text.casefold()
    onnx = "onnx" in fold
    generated = any(x in fold for x in ("generated c code", "generated c++", "code generation", "model-to-code"))
    edge = any(x in fold for x in ("microcontroller", "electronic control unit", " ecu", "onboard", "on-board"))
    if onnx and generated:
        return "onnx_plus_generated_embedded_code"
    if onnx and edge:
        return "onnx_plus_explicit_edge_deployment"
    if generated:
        return "generated_c_or_cpp_from_neural_model"
    if onnx:
        return "onnx_model_adoption"
    if any(x in fold for x in ("model conversion", "embedded ai toolchain", "embedded-ai toolchain")):
        return "model_conversion_or_embedded_ai_toolchain"
    if any(x in fold for x in ("tensorflow", "pytorch", "keras", "matlab deep learning")):
        return "framework_known_and_likely_exportable"
    return "no_public_workflow_evidence"


def score_patent_use_case(analysis: dict, text: str) -> dict:
    """Score one coherent patent/application context; missing fields add zero, never reset."""
    fold = text.casefold()
    use_cases = analysis.get("use_case_classes", [])
    strength = analysis.get("patent_neural_evidence_strength", "absent")
    roles = analysis.get("algorithm_roles", {})
    has_defined_role = bool(roles.get("estimator") or roles.get("learning_or_adaptation_agent"))
    defined_application = bool(use_cases) and any(x in fold for x in (
        "estimat", "virtual measurement", "learning agent", "classification model", "regression model",
        "control", "autonomous driving", "recognition", "detection", "perception", "monitor"
    ))
    if strength == "confirmed_required_or_implemented" and defined_application:
        neural_level = "neural_network_explicit_operational_embodiment"
    elif strength == "claimed_optional_embodiment" and defined_application:
        neural_level = "neural_network_explicitly_claimed_for_parameter_estimation"
    elif strength == "mentioned_possible_method" and defined_application and has_defined_role:
        neural_level = "neural_network_optional_but_semantically_connected_to_estimator"
    elif strength == "generic_machine_learning_only" and defined_application:
        neural_level = "generic_machine_learning_estimator_without_neural_confirmation"
    elif "neural network" in fold:
        neural_level = "generic_neural_network_mention"
    elif any(x in fold for x in ("machine learning", "transfer learning", "regression model", "classification model", "data-driven")) and defined_application:
        neural_level = "generic_machine_learning_estimator_without_neural_confirmation"
    elif ("indirect_physical_state_and_virtual_sensing" in use_cases and
          any(x in fold for x in ("sensorless", "without using temperature sensors", "indirect measurement", "rotor temperature", "rotor resistance"))):
        neural_level = "indirect_physical_estimator_neural_candidate"
    else:
        neural_level = "no_neural_or_machine_learning_method"

    # Patent wording that merely says an algorithm *can be implemented* by an
    # ECU is intent (10), not proof of actual onboard execution.
    implementable = any(x in fold for x in (
        "implemented by a processing device", "implemented by a programmable", "can be implemented by",
        "can include any existing programmable electronic control unit"
    ))
    real_time_onboard = ("real-time" in fold or "real time" in fold) and any(x in fold for x in (
        "onboard", "on-board", "onboard charging module", "battery management controller", "ress controller"
    ))
    explicit_onboard = any(x in fold for x in (
        "executes on the controller", "executed by the controller", "implemented in the controller",
        "onboard controller executes", "on-board controller executes", "stored by the controller",
        "loaded into the controller", "implemented by the controller", "controller is configured to utilize"
    ))
    fixed_controller_inference = (analysis.get("runtime_and_lifecycle", {}).get("fixed_trained_inference") == "confirmed"
                                  and analysis.get("onboard_context") == "confirmed")
    if explicit_onboard or fixed_controller_inference:
        edge_level = "implementation_on_onboard_controller_explicit"
    elif implementable:
        # A patent's permissive "can be implemented by an ECU" language is
        # conservatively classified at 10 even when the application itself is
        # described as real-time. It does not prove actual onboard execution.
        edge_level = "implementable_on_ecu_or_controller"
    elif real_time_onboard:
        edge_level = "real_time_onboard_execution_explicit"
    elif analysis.get("onboard_context") == "confirmed":
        edge_level = "embedded_adjacent_physical_application_only"
    else:
        edge_level = "no_edge_deployment_decision_disclosed"

    workflow_level = _workflow_level(text)
    neural_points = NEURAL_LEVELS[neural_level]
    edge_points = EDGE_LEVELS[edge_level]
    workflow_points = WORKFLOW_LEVELS[workflow_level]
    score_eligible = neural_points > 0 or workflow_points > 0
    score_exclusion_reason = None if score_eligible else "edge_context_without_neural_or_workflow_signal"
    total = min(100, neural_points + edge_points + workflow_points) if score_eligible else 0
    if neural_points >= 45 and edge_points >= 15 and workflow_points >= 12:
        mapping_class = "nnc_maximum_workflow_fit"
    elif neural_points >= 45 and edge_points >= 15:
        mapping_class = "nnc_deployment_fit"
    elif neural_points >= 45:
        mapping_class = "nnc_influence_opportunity"
    else:
        mapping_class = None
    mapping_eligible = mapping_class is not None
    return {
        "company_neural_application": {"classification": neural_level, "points": neural_points},
        "edge_deployment_intent": {"classification": edge_level, "points": edge_points},
        "deployment_workflow_fit": {"classification": workflow_level, "points": workflow_points},
        "use_case_score": total,
        "score_eligible": score_eligible,
        "score_exclusion_reason": score_exclusion_reason,
        "relevance_band": relevance_band(total),
        "mapping_class": mapping_class,
        "mapping_eligible": mapping_eligible,
        "relevance_class": "nnc_applicability_evidence" if mapping_eligible else "nnc_opportunity_evidence",
        "deployment_readiness": {
            "onnx_adoption": "confirmed" if workflow_level in {"onnx_model_adoption", "onnx_plus_explicit_edge_deployment", "onnx_plus_generated_embedded_code"} else "unconfirmed",
            "generated_code_workflow": "confirmed" if workflow_level in {"generated_c_or_cpp_from_neural_model", "onnx_plus_generated_embedded_code"} else "unconfirmed",
            "qualification_required": workflow_points < 20,
        },
    }


def aggregate_company_scores(evidence: list[dict]) -> dict:
    """Best distinct application + 10/5 breadth bonus; corroboration does not duplicate."""
    by_case: dict[str, list[dict]] = defaultdict(list)
    for item in evidence:
        scoring = item.get("nnc_use_case_scoring") or {}
        score_eligible=scoring.get("score_eligible",int(scoring.get("use_case_score",0)) > 0)
        if (not scoring or score_eligible is not True or int(scoring.get("use_case_score",0)) <= 0
                or item.get("relevant_evidence_eligible") is False
                or item.get("relevance_class") == "contextual_company_evidence"):
            continue
        cases = [c for c in item.get("use_case_classes",[]) if c and not str(c).upper().startswith("SRC-")]
        if not cases:
            continue
        # Specific families take precedence over the generic indirect-sensing umbrella.
        specific = [c for c in cases if c != "indirect_physical_state_and_virtual_sensing"] or cases
        by_case[sorted(specific)[0]].append(item)
    use_cases = []
    for case_id, items in by_case.items():
        best = max(items, key=lambda x: int(x["nnc_use_case_scoring"]["use_case_score"]))
        ranked=sorted(items,key=lambda x:-int(x["nnc_use_case_scoring"]["use_case_score"]))
        use_cases.append({"use_case_id": case_id, **best["nnc_use_case_scoring"],
                          "supporting_evidence_ids": sorted({x["evidence_id"] for x in items}),
                          "supporting_source_ids":list(dict.fromkeys(x.get("source_id") for x in ranked if x.get("source_id")))})
    use_cases.sort(key=lambda x: (-x["use_case_score"], x["use_case_id"]))
    base = use_cases[0]["use_case_score"] if use_cases else 0
    strong_count = sum(x["use_case_score"] >= 40 for x in use_cases)
    breadth = (10 if strong_count >= 2 else 0) + (5 if strong_count >= 3 else 0)
    total = min(100, base + breadth)
    return {"use_cases": use_cases, "base_score": base, "opportunity_breadth_bonus": breadth,
            "overall_product_match": total, "rating": relevance_band(total)}
