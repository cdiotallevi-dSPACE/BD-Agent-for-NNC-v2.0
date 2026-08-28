"""Deterministic Tiny-AI / Edge-AI semantic gates for Neural Net Coder."""
from __future__ import annotations

NEURAL_TERMS = {"neural_network", "convolutional_neural_network", "recurrent_neural_network", "transformer_model", "autoencoder", "multi_layer_perceptron"}
TARGET_TERMS = {"microcontroller", "automotive_ecu", "bare_metal_or_rtos", "low_power_soc"}
WORKFLOW_TERMS = {"onnx_model", "embedded_code_generation", "embedded_c_cpp", "model_conversion"}
CONSTRAINT_TERMS = {"resource_constraints", "model_optimization", "model_verification", "safety_workflow"}
PARTNER_TERMS = {"silicon_vendor", "deployment_tool_vendor"}


def evaluate_nnc_gates(entity_ids: set[str]) -> dict:
    neural = sorted(entity_ids & NEURAL_TERMS)
    targets = sorted(entity_ids & TARGET_TERMS)
    workflows = sorted(entity_ids & WORKFLOW_TERMS)
    constraints = sorted(entity_ids & CONSTRAINT_TERMS)
    cloud_only = "cloud_or_server_target" in entity_ids and not targets
    direct_competitor = "direct_competitor" in entity_ids
    partner = bool(entity_ids & PARTNER_TERMS)
    role = "competitor" if direct_competitor else "partner_or_ecosystem" if partner else "potential_customer"
    return {
        "neural_network_gate": {"passed": bool(neural), "supporting_entity_ids": neural},
        "embedded_target_gate": {"passed": bool(targets) and not cloud_only, "supporting_entity_ids": targets},
        "deployment_workflow_gate": {"passed": bool(workflows), "supporting_entity_ids": workflows},
        "company_role_gate": {"passed": not direct_competitor, "role": role},
        "cloud_only": cloud_only,
        "constraint_signals": constraints,
        # v1.10: a confirmed neural engineering application may be an influence
        # mapping before edge target or workflow adoption is public.
        "positive_applicability_candidate": bool(neural and not direct_competitor),
    }


def score_nnc_applicability(gates: dict, evidence_quality: float) -> tuple[int, dict]:
    components = {
        "neural_model": 30 if gates["neural_network_gate"]["passed"] else 0,
        "embedded_target": 25 if gates["embedded_target_gate"]["passed"] else 0,
        "deployment_workflow": 20 if gates["deployment_workflow_gate"]["passed"] else 0,
        "constraints_and_verification": min(15, 5 * len(gates["constraint_signals"])),
        "evidence_quality": round(10 * max(0.0, min(1.0, evidence_quality))),
    }
    score = sum(components.values())
    if gates["company_role_gate"]["role"] == "partner_or_ecosystem":
        score = min(score, 60)
    if gates["company_role_gate"]["role"] == "competitor":
        score = 0
    if not gates["neural_network_gate"]["passed"]:
        score = min(score, 15)
    if gates["cloud_only"]:
        score = min(score, 25)
    return score, components
