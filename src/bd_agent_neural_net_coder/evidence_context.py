"""Local-context evidence extraction and false-positive controls."""
from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import urlparse

from .core import sha256_text
from .nnc_domain import NEURAL_TERMS, TARGET_TERMS, WORKFLOW_TERMS
from .nnc_scoring import score_patent_use_case
from .shared_use_case_taxonomy import family_terms, load_shared_use_case_taxonomy, match_use_case_families

LOCAL_SPAN = 1400
MODEL_QUANTIZATION_CONTEXT = re.compile(
    r"(?i)(neural|network|model|weights?|activations?|tensor|int8|post-training|quantization-aware|onnx)"
)
ML_ACTIVITY = re.compile(r"(?i)(supervised (?:machine )?learning model|machine[- ]learning[- ]based|machine learning model|data[- ]driven (?:model|estimator|classifier)|neural network|artificial neural network|deep neural network|\bANN\b|\bDNN\b|transfer learning|virtual sensor|soft sensor|sensorless estimat|classifier|recognition model|neuro[- ]?fuzzy|ANFIS|ANFC)")
PHYSICAL_ADJACENCY = re.compile(r"(?i)(vehicle|automotive|telematics?|ADAS|autonomous driving|powertrain|combustion|motor|battery|control|estimat|condition monitoring|predictive maintenance|sensor|onboard|device|loading condition|payload|vehicle mass|driving behavior|driving behaviour)")
APPLICATION_MATURITY = re.compile(r"(?i)(real[- ]time|deployed|trial|prototype|experimental|measured|driving (?:behavior|behaviour)|real[- ]system data)")
CLOUD_ONLY = re.compile(r"(?i)(exclusively|only)\s+(?:in|on|using)?\s*(?:the )?(?:cloud|server|datacenter|data center)")
PATENT_ML = re.compile(r"(?i)(machine learning|transfer learning|regression model|classification model|data[- ]driven|neural network|\bANN\b|\bDNN\b|learning agent)")
PATENT_PHYSICAL = re.compile(r"(?i)(battery|vehicle|wheel|tire|tractive|charging|controller|control unit|onboard|sensor|physical state|motor|rotor|stator|combustion|engine|autonomous driving)")


def classify_source(doc: dict) -> str:
    if doc.get("source_category_hint") == "target_company_patent":
        return "target_company_patent"
    label = f"{doc.get('title','')} {doc.get('url','')}".lower()
    if ("patents.google.com/patent" in label or "patents.justia.com" in label
            or "api.uspto.gov/api/v1/datasets/products/files/" in label
            or "data.uspto.gov/files/" in label):
        return "target_company_patent"
    if any(x in label for x in ("owner-manual", "owners-manual", "owner manual")):
        return "vehicle_owner_manual"
    if any(x in label for x in ("obd", "diagnostic", "service-manual", "repair-manual")):
        return "obd_or_diagnostic_manual"
    if any(x in label for x in ("paper", "proceedings", "bitstream", "publication")):
        return "academic_publication"
    return "general_web_source"


def classify_source_category(doc: dict, text: str, attribution: dict) -> str:
    host = re.sub(r"^www\.", "", urlparse(doc.get("url", "")).hostname or "")
    patent_hint = doc.get("source_category_hint") == "target_company_patent"
    if attribution.get("company_attribution_status") == "established" and (patent_hint or host in {
        "patents.google.com", "patents.justia.com", "api.uspto.gov", "data.uspto.gov"
    }):
        return "target_company_patent"
    professional_host = host in {"saemobilus.sae.org", "sae.org", "mathworks.com"}
    professional_form = any(x in f"{doc.get('title','')} {doc.get('url','')}".lower() for x in ("paper", "presentation", "conference", "proceedings", "case study", "user_stor", ".pdf"))
    if attribution.get("company_attribution_status") == "established" and professional_host and professional_form and ML_ACTIVITY.search(text) and PHYSICAL_ADJACENCY.search(text):
        return "professional_applied_ml_publication"
    return "unclassified"


def analyze_patent(text: str) -> dict:
    """Role-aware v1.6/v1.7 patent semantics; never grants mapping eligibility."""
    fold = text.casefold()
    claim_context = bool(re.search(r"(?i)(what is claimed|claims?\s*\(|dependent claim|wherein).{0,500}neural network", text))
    implemented = bool(re.search(r"(learning agent|estimator).{0,180}(includes?|including|comprises?|uses?|implemented).{0,100}neural network", text, re.I | re.S)
                       or re.search(r"neural network.{0,120}(estimator|learning agent)", text, re.I | re.S)
                       or re.search(r"(?:trained )?(?:artificial |deep )?neural networks?.{0,180}(?:estimate|control|classif|detect|recogn|predict|accessed|executed|stored)", text, re.I | re.S)
                       or re.search(r"(?:LSTM|long short-term memory).{0,180}(?:estimate|control|classif|detect|recogn|predict|binary search)", text, re.I | re.S)
                       or re.search(r"(?:estimate|control|classif|detect|recogn|predict).{0,180}(?:trained )?(?:artificial |deep )?neural networks?", text, re.I | re.S))
    possible = bool(re.search(r"(?i)(neural network|artificial neural network|deep neural network|\bANN\b|\bDNN\b|\bRNN\b|\bLSTM\b|long short-term memory)", text))
    explicit_operational = bool(re.search(r"(?i)(?:controller|ECU|BMS|control system).{0,260}(?:access|execute|store|use|utiliz|perform).{0,140}(?:trained )?(?:artificial |deep )?neural network", text, re.S)
                                or re.search(r"(?i)(?:trained )?(?:artificial |deep )?neural network.{0,220}(?:stored|executed|accessed|used|implemented) (?:by|in) (?:the )?(?:vehicle |engine )?controller", text, re.S)
                                or re.search(r"(?i)(?:method|calibration).{0,100}implemented by (?:the )?(?:vehicle |engine )?controller.{0,400}(?:ANN|neural network)", text, re.S)
                                or re.search(r"(?i)(?:control system|controller).{0,220}(?:perform|use|utiliz|access)?.{0,40}(?:LSTM|long short-term memory).{0,180}(?:estimat|binary search|state of power|SOP)", text, re.S))
    if explicit_operational:
        strength = "confirmed_required_or_implemented"
    elif claim_context:
        strength = "claimed_optional_embodiment"
    elif implemented:
        strength = "confirmed_required_or_implemented"
    elif possible:
        strength = "mentioned_possible_method"
    elif re.search(r"(?i)(machine learning|regression model|classification model|data[- ]driven)", text):
        strength = "generic_machine_learning_only"
    else:
        strength = "absent"
    use_cases = list(match_use_case_families(text, include_context=False))
    if re.search(r"(?i)(tractive limit|traction limit|tire[- ]road friction|wheel stability|wheel slip|slip ratio|tire saturation|vehicle[- ]dynamics)", text):
        use_cases.extend(["indirect_physical_state_and_virtual_sensing", "vehicle_dynamics_learned_estimation"])
    if re.search(r"(?i)(battery charging|predictive charging|dynamic charging|charging control|anode (?:potential|voltage)|electrolyte concentration|lithium plating|capacity loss|battery state|state of (?:health|charge))", text):
        use_cases.extend(["battery_virtual_measurement_and_predictive_control", "battery_health_and_state_estimation", "indirect_physical_state_and_virtual_sensing"])
    hidden_layers = re.search(r"(?i)(?:compris(?:es|ing)|defines?|includes?|has|having)\s+(?:two|2)\s+(?:hidden\s+)?LSTM layers|(?:two|2) hidden layers", text)
    hidden_units = re.search(r"(?i)(?:sixteen|16) (?:hidden units|neurons)(?: per (?:hidden )?layer)?|(?:twelve|12) neurons per (?:hidden )?layer", text)
    fixed_inference = bool(re.search(r"(?i)(?:trained|generated) (?:ANN|LSTM|(?:artificial |deep )?neural network|battery voltage estimation model).{0,500}(?:stored|loaded|accessed|used|utilized|estimating|determining|controlling)", text, re.S)
                           or re.search(r"(?i)(?:controller|control system).{0,300}(?:trained|generated) (?:ANN|LSTM|(?:artificial |deep )?neural network|battery voltage estimation model)", text, re.S)
                           or (re.search(r"(?i)(?:LSTM|long short-term memory)", text)
                               and re.search(r"(?i)controller.{0,100}(?:utilize|use|access).{0,60}trained model", text, re.S)))
    online_update = bool(re.search(r"(?i)(?:transfer learning|online learning|model updating|update(?:d|s|ing)? (?:the )?(?:SOP|battery|neural|machine learning).{0,40}model)", text))
    sensor_elimination = bool(re.search(r"(?i)(?:does not include|without|eliminat(?:e|es|ing)|not required).{0,100}(?:temperature )?sensors?|sensors? (?:are )?only used temporarily", text, re.S))
    return {
        "patent_neural_evidence_strength": strength,
        "neural_model_status": "confirmed_as_embodiment" if implemented else ("possible_but_not_selected_or_confirmed" if possible else "unconfirmed"),
        "use_case_classes": sorted(set(use_cases)),
        "applied_ml_activity": {
            "regression_model": "confirmed" if "regression model" in fold else "unconfirmed",
            "classification_model": "confirmed" if "classification model" in fold else "unconfirmed",
        },
        "virtual_measurements": {
            "anode_potential": "confirmed" if re.search(r"(?i)anode (?:potential|voltage)", text) else "unconfirmed",
            "electrolyte_concentration": "confirmed" if "electrolyte concentration" in fold else "unconfirmed",
            "capacity_loss": "confirmed" if "capacity loss" in fold else "unconfirmed",
            "aging_parameter": "confirmed" if re.search(r"(?i)(aging|ageing) (?:parameter|variable)", text) else "unconfirmed",
            "lithium_plating_related_limit": "confirmed" if "lithium plating" in fold else "unconfirmed",
        },
        "algorithm_roles": {
            "estimator": sorted(x for x, present in (("extended_kalman_filter", bool(re.search(r"(?i)(EKF|extended Kalman)", text))), ("physics_based_model", "physics-based" in fold or "physics based" in fold), ("neural_network_estimator", bool(re.search(r"(?i)neural network.{0,100}estimat|estimat.{0,100}neural network", text))), ("hybrid_data_driven_estimator", bool(re.search(r"(?i)hybrid.{0,100}(data[- ]driven|neural)", text)))) if present),
            "optimizer_or_controller": sorted(x for x, present in (("model_predictive_controller", bool(re.search(r"(?i)(model predictive|MPC)", text))), ("charging_current_optimizer", bool(re.search(r"(?i)charging current.{0,80}(optim|control)", text)))) if present),
            "learning_or_adaptation_agent": sorted(x for x, present in (("neural_network_learning_agent", bool(re.search(r"(?i)neural network.{0,120}learning agent|learning agent.{0,120}neural network", text))), ("adaptive_calibration_model", bool(re.search(r"(?i)(adaptive|periodically update).{0,100}calibration", text)))) if present),
        },
        "onboard_context": "confirmed" if re.search(r"(?i)(onboard|on-board|electronic control unit|ECU|RESS controller|onboard charging module|OBCM|battery management controller|BMS|vehicle controller|engine controller|control system.{0,80}vehicle|controller of the vehicle|stored by the controller|implemented by the controller)", text, re.S) else "unconfirmed",
        "model_architecture": {
            "recurrent_ann": "confirmed" if re.search(r"(?i)(recurrent[- ]type ANN|recurrent neural network|RNN)", text) else "unconfirmed",
            "lstm": "confirmed" if re.search(r"(?i)(LSTM|long short-term memory)", text) else "unconfirmed",
            "feed_forward_ann": "confirmed" if re.search(r"(?i)feed[- ]forward (?:artificial neural network|ANN)", text) else "unconfirmed",
            "hidden_layer_count": 2 if hidden_layers else None,
            "hidden_units_or_neurons_per_layer": (16 if hidden_units and re.search(r"(?i)(sixteen|16)", hidden_units.group(0)) else (12 if hidden_units else None)),
        },
        "runtime_and_lifecycle": {
            "fixed_trained_inference": "confirmed" if fixed_inference else "unconfirmed",
            "real_time_inference": "confirmed" if re.search(r"(?i)real[- ]time", text) else "unconfirmed",
            "online_or_lifecycle_model_update": "confirmed_separate_workflow" if online_update else "not_disclosed",
            "sensor_elimination_or_training_only_sensor": "confirmed" if sensor_elimination else "unconfirmed",
        },
        "nnc_scope_boundary": {
            "fixed_trained_inference_fit": "high" if fixed_inference and possible else "unconfirmed",
            "online_transfer_learning_handling": "separate_qualification_required" if online_update else "not_applicable",
            "onnx_or_generated_code_evidence": "unconfirmed",
        },
        "pilot_assessment": {
            "priority_class": ("strongest_first_pilot" if fixed_inference and sensor_elimination
                               else ("strong_pilot_separate_online_learning" if fixed_inference and online_update
                                     else ("strong_compact_embedded_pilot_legacy_ice_context"
                                           if fixed_inference and re.search(r"(?i)feed[- ]forward", text) and re.search(r"(?i)(spark|combustion|internal combustion)", text)
                                           else ("strong_fixed_inference_pilot" if fixed_inference else "qualification_required")))),
            "technical_fit_penalized_for_age": False,
            "commercial_recency_qualification": "required" if re.search(r"(?i)(spark ignit|internal combustion|combustion phasing)", text) else "not_flagged",
        },
    }


def _term_matches(text: str, terms: list[dict]) -> list[dict]:
    matches = []
    for term in terms:
        for alias in [term["name"], *term.get("aliases", [])]:
            match = re.search(rf"(?i)(?<!\w){re.escape(alias)}(?!\w)", text)
            if match:
                matches.append({"term": term, "alias": alias, "start": match.start(), "end": match.end()})
                break
    # Use-case evidence is sourced directly from the same versioned taxonomy
    # used by discovery and ranking. These are target-company application
    # entities; they still require attribution and the downstream evidence
    # gates before approval or scoring.
    existing = {item["term"]["term_id"] for item in matches}
    for family_id, definition in load_shared_use_case_taxonomy()["use_case_families"].items():
        if family_id in existing:
            continue
        for alias in family_terms(family_id):
            match = re.search(rf"(?i)(?<!\w){re.escape(alias)}(?!\w)", text)
            if match:
                matches.append({"term": {"term_id": family_id, "name": definition["display_name"],
                    "aliases": list(family_terms(family_id)), "entity_scope": "target_company",
                    "entity_kind": "use_case", "domain_layer": "application"},
                    "alias": alias, "start": match.start(), "end": match.end()})
                break
    return matches


def _complete_clusters(matches: list[dict]) -> list[list[dict]]:
    ordered = sorted(matches, key=lambda item: item["start"])
    clusters: list[list[dict]] = []
    for left in range(len(ordered)):
        cluster = [item for item in ordered[left:] if item["start"] - ordered[left]["start"] <= LOCAL_SPAN]
        ids = {item["term"]["term_id"] for item in cluster}
        if ids & NEURAL_TERMS and ids & TARGET_TERMS and ids & WORKFLOW_TERMS:
            signature = tuple(sorted((item["term"]["term_id"], item["start"]) for item in cluster))
            if not any(tuple(sorted((x["term"]["term_id"], x["start"]) for x in old)) == signature for old in clusters):
                clusters.append(cluster)
    return clusters


def extract_document_evidence(doc: dict, taxonomy: dict, attribution: dict, evidence_start: int = 1) -> dict:
    accepted: list[dict] = []
    rejected: list[dict] = []
    background: list[dict] = []
    bundles: list[dict] = []
    source_id = doc["source_id"]
    source_class = classify_source(doc)
    next_id = evidence_start
    seen: set[str] = set()

    for page in doc.get("pages") or [{"page": None, "text": doc.get("text", "")}]:
        text = re.sub(r"\s+", " ", str(page.get("text", ""))).strip()
        matches = _term_matches(text, taxonomy["terms"])
        if not attribution["mapping_eligible"]:
            for match in matches:
                background.append({
                    "source_id": source_id, "source_url": doc["url"], "source_page": page.get("page"),
                    "taxonomy_term_id": match["term"]["term_id"], "source_attribution_scope": "general_industry_background",
                    "technical_domain_relevance": "high", "mapping_eligible": False, "score_contribution": 0,
                    "relevant_evidence_eligible": False, "reason_codes": attribution["reason_codes"],
                })
            continue

        # The same deterministic application analysis is applied to patents,
        # HTML, PDFs and professional publications. Source type affects
        # attribution/approval, never vocabulary or scoring semantics.
        technical_analysis = analyze_patent(text)
        use_case_scoring = score_patent_use_case(technical_analysis, text) if technical_analysis["use_case_classes"] else None
        opportunity_pass = bool(attribution["company_attribution_status"] == "established"
            and (source_class in {"academic_publication", "target_company_patent"} or any(a.get("anchor_type") == "official_domain_ownership" for a in attribution.get("identity_anchors", [])))
            and ((source_class == "target_company_patent" and PATENT_ML.search(text) and PATENT_PHYSICAL.search(text)) or (ML_ACTIVITY.search(text) and PHYSICAL_ADJACENCY.search(text) and APPLICATION_MATURITY.search(text)))
            and not (CLOUD_ONLY.search(text) and not PHYSICAL_ADJACENCY.search(text)))
        source_category = classify_source_category(doc, text, attribution)
        use_case_classes = []
        if re.search(r"(?i)(indirect sensing|indirect measurement|virtual sensor|soft sensor|sensorless|state estimation|operating[- ]condition|loading condition|payload estimation|vehicle mass estimation|driving behavio(?:u)?r|telematics based inference)", text):
            use_case_classes.append("indirect_physical_state_and_virtual_sensing")
        if re.search(r"(?i)(vehicle loading condition|loading condition recognition|vehicle load estimation|payload estimation|vehicle mass estimation)", text):
            use_case_classes.append("vehicle_operating_condition_recognition")
        use_case_classes.extend(technical_analysis["use_case_classes"])
        clusters = _complete_clusters(matches)
        eligible_positions = {(item["term"]["term_id"], item["start"]) for cluster in clusters for item in cluster}
        for cluster_no, cluster in enumerate(clusters, 1):
            start = max(0, min(item["start"] for item in cluster) - 220)
            end = min(len(text), max(item["end"] for item in cluster) + 300)
            bundles.append({
                "context_bundle_id": f"CTX-{source_id[4:]}-{page.get('page') or 0:04d}-{cluster_no:02d}",
                "source_id": source_id, "source_page": page.get("page"), "gate_status": "pass",
                "company_attribution_status": "established", "attributed_company_id": attribution["attributed_company_id"],
                "dimension_entity_ids": {
                    "neural_model": sorted({x["term"]["term_id"] for x in cluster if x["term"]["term_id"] in NEURAL_TERMS}),
                    "embedded_target": sorted({x["term"]["term_id"] for x in cluster if x["term"]["term_id"] in TARGET_TERMS}),
                    "deployment_workflow": sorted({x["term"]["term_id"] for x in cluster if x["term"]["term_id"] in WORKFLOW_TERMS}),
                },
                "passage": text[start:end], "reason_codes": ["complete_local_context_bundle"],
            })

        for match in matches:
            term_id = match["term"]["term_id"]
            start, end = max(0, match["start"] - 220), min(len(text), match["end"] + 300)
            passage = text[start:end]
            reason_codes: list[str] = []
            eligible = (term_id, match["start"]) in eligible_positions
            if term_id == "model_optimization" and "quantization" in match["alias"].lower() and not MODEL_QUANTIZATION_CONTEXT.search(passage):
                eligible = False
                reason_codes.append("signal_quantization_not_model_quantization")
            if source_class in {"vehicle_owner_manual", "obd_or_diagnostic_manual"} and not eligible:
                reason_codes.extend(["target_only_no_neural_context", "generic_vehicle_manual"])
            if not eligible:
                reason_codes.append("incomplete_context_bundle")
            fp = sha256_text(term_id + passage.lower())
            assessment = "accepted" if fp not in seen else "rejected"
            if assessment == "rejected":
                reason_codes.append("duplicate_claim")
            seen.add(fp)
            bundle_ids = [b["context_bundle_id"] for b in bundles if b["source_page"] == page.get("page") and term_id in sum(b["dimension_entity_ids"].values(), [])]
            v110_mapping = bool(use_case_scoring and use_case_scoring["mapping_eligible"] and opportunity_pass)
            eligible = eligible or v110_mapping
            if v110_mapping:
                reason_codes = [code for code in reason_codes if code != "incomplete_context_bundle"]
                reason_codes.append("v1_10_neural_application_mapping")
            relevance_class = (use_case_scoring["relevance_class"] if use_case_scoring and opportunity_pass
                               else ("nnc_mapping_evidence" if eligible else ("nnc_opportunity_evidence" if opportunity_pass else "contextual_company_evidence")))
            record = {
                "evidence_id": f"EVD-{next_id:05d}", "entity_scope": "target_company",
                "claim": f"Company evidence mentions {match['term']['name']}", "passage": passage,
                "source_id": source_id, "source_url": doc["url"], "source_page": page.get("page"),
                "taxonomy_term_id": term_id, "evidence_status": "confirmed", "assessment": assessment,
                "confidence": 0.85, "claim_fingerprint": fp, "rejection_reason": "duplicate_claim" if assessment == "rejected" else None,
                "scan_target_company_id": attribution["scan_target_company_id"],
                "attributed_company_id": attribution["attributed_company_id"],
                "company_attribution_status": attribution["company_attribution_status"],
                "source_attribution_scope": "target_company", "source_class": source_class,
                "context_bundle_ids": bundle_ids, "context_bundle_gate_status": "pass" if eligible else "fail",
                "mapping_eligibility": {"eligible": eligible, "reason_codes": list(dict.fromkeys(reason_codes))},
                "score_contribution": use_case_scoring["use_case_score"] if use_case_scoring and opportunity_pass else ("eligible" if eligible else 0),
                "relevant_evidence_eligible": eligible or opportunity_pass,
                "relevance_class": relevance_class,
                "opportunity_evidence_gate_status": "pass" if opportunity_pass else "fail",
                "neural_model_status": "confirmed" if eligible else "unconfirmed",
                "embedded_execution_status": "confirmed" if eligible else "unconfirmed",
                "onnx_status": "confirmed" if eligible and term_id == "onnx_model" else "unconfirmed",
                "claim_ceiling": {"allowed":["confirmed_target_company_ml_project","potential_nnc_qualification_opportunity","neural_architecture_not_disclosed","embedded_execution_not_disclosed"],"prohibited":["confirmed_neural_network","confirmed_mcu_deployment","confirmed_onnx_workflow","confirmed_nnc_applicability_mapping"]} if opportunity_pass else None,
                "source_category": source_category,
                "use_case_classes": use_case_classes,
                "patent_neural_evidence_strength": technical_analysis["patent_neural_evidence_strength"],
                "patent_analysis": technical_analysis if source_class == "target_company_patent" else None,
                "technical_application_analysis": technical_analysis,
                "nnc_use_case_scoring": use_case_scoring,
                "mapping_class": use_case_scoring.get("mapping_class") if use_case_scoring else None,
            }
            next_id += 1
            (accepted if assessment == "accepted" else rejected).append(record)

    evidence_by_bundle: dict[str, list[str]] = defaultdict(list)
    for record in accepted:
        if record["mapping_eligibility"]["eligible"]:
            for bundle_id in record["context_bundle_ids"]:
                evidence_by_bundle[bundle_id].append(record["evidence_id"])
    for bundle in bundles:
        bundle["evidence_ids"] = sorted(set(evidence_by_bundle[bundle["context_bundle_id"]]))
    return {"accepted": accepted, "rejected": rejected, "background": background, "context_bundles": bundles, "next_evidence_id": next_id}
