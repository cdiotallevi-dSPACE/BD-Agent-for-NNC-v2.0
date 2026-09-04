import json
from pathlib import Path

import jsonschema

from bd_agent_neural_net_coder.llm_response_validator import detect_truncation, parse_json_without_repair
from bd_agent_neural_net_coder.pipeline import normalize_llm_list_fields
from bd_agent_neural_net_coder.llm_context_builder import fit_complete_prompt
from bd_agent_neural_net_coder.prompt_loader import load_prompt_bundle
from bd_agent_neural_net_coder.provider_cycle_state import ProviderCycleState
from bd_agent_neural_net_coder.search_orchestrator import apply_candidate_budget, build_seed_registration


def test_v3_prompt_schema_is_compact():
    bundle=load_prompt_bundle(Path(__file__).resolve().parents[2],"gemma2:9b")
    assert bundle["bundle_id"]=="company_summary_v3.0"
    assert set(bundle["output_schema"]["properties"])=={
        "company_name","portfolio_supplier_name","overall_assessment",
        "key_information_gaps","recommended_next_actions",
    }


def test_v3_prompt_requires_need_solution_and_application_purpose():
    root=Path(__file__).resolve().parents[2]
    system=(root/"prompts"/"company_summary_system_v3.txt").read_text(encoding="utf-8")
    user=(root/"prompts"/"company_summary_user_template_v3.txt").read_text(encoding="utf-8")
    schema=json.loads((root/"prompts"/"company_summary_output_schema_v3.json").read_text(encoding="utf-8"))
    assert "evidenced engineering needs" in system
    assert "concrete engineering purpose" in system
    assert "why the offering from dSPACE is applicable" in system
    assert "100-to-300-word hard limits" in user
    assert schema["properties"]["overall_assessment"]["minLength"] == 450
    assert schema["properties"]["overall_assessment"]["maxLength"] == 3000


def test_empty_gemma_list_items_are_safely_normalized_before_validation():
    summary={
        "key_information_gaps":["", "   ", " Confirm target processor. "],
        "recommended_next_actions":[
            "  ",
            " Confirm the deployment target. ",
        ],
    }
    normalized,audit=normalize_llm_list_fields(summary)
    assert normalized["key_information_gaps"]==["Confirm target processor."]
    assert normalized["recommended_next_actions"]==["Confirm the deployment target."]
    assert audit=={
        "applied":True,
        "removed_empty_information_gaps":2,
        "removed_empty_recommended_actions":1,
    }


def test_recommended_actions_are_priority_ordered_strings():
    root=Path(__file__).resolve().parents[2]
    schema=json.loads((root/"prompts"/"company_summary_output_schema_v3.json").read_text(encoding="utf-8"))
    actions_schema=schema["properties"]["recommended_next_actions"]
    jsonschema.validate(["Confirm the target processor.", "Request an ONNX model sample."],actions_schema)
    assert "highest to lowest priority" in actions_schema["description"]


def test_recommended_action_objects_are_no_longer_accepted():
    root=Path(__file__).resolve().parents[2]
    schema=json.loads((root/"prompts"/"company_summary_output_schema_v3.json").read_text(encoding="utf-8"))
    actions_schema=schema["properties"]["recommended_next_actions"]
    try:
        jsonschema.validate([{"priority":"high","action":"Confirm the target processor."}],actions_schema)
    except jsonschema.ValidationError:
        pass
    else:
        raise AssertionError("object-form recommended action unexpectedly passed the compact schema")


def test_normalizer_does_not_hide_wrong_types_from_schema_validation():
    summary={"key_information_gaps":[7],"recommended_next_actions":[None]}
    normalized,audit=normalize_llm_list_fields(summary)
    assert normalized==summary
    assert audit["applied"] is False


def test_truncated_json_is_detected_and_not_repaired():
    raw='{"company_name":"Example","overall_assessment":"unfinished'
    result=detect_truncation(raw,{"eval_count":1800},1800)
    assert result["failure_code"]=="llm_output_truncated"
    try:
        parse_json_without_repair(raw)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("invalid JSON was repaired")


def test_auto_provider_without_credential_is_one_cycle_skip(tmp_path,monkeypatch):
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY",raising=False)
    monkeypatch.delenv("BRAVE_API_KEY",raising=False)
    state=ProviderCycleState(tmp_path/"provider_cycle_state.json",{"brave":{"activation_mode":"auto","credential_env":"BRAVE_SEARCH_API_KEY","credential_aliases":["BRAVE_API_KEY"]}})
    assert not state.available("brave")
    assert len(state.data["events"])==1
    assert state.data["events"][0]["event_type"]=="informational_skip"


def test_provider_rate_limit_event_is_cycle_scoped(tmp_path):
    state=ProviderCycleState(tmp_path/"provider_cycle_state.json",{"semantic_scholar":{"activation_mode":"enabled"}})
    state.record_rate_limit("semantic_scholar",{"Retry-After":"60"})
    state.record_rate_limit("semantic_scholar",{"Retry-After":"60"})
    assert not state.available("semantic_scholar")
    assert len([e for e in state.data["events"] if e["event_type"]=="provider_rate_limited"])==1


def test_v117_siemens_seeds_survive_historical_candidate_budget():
    seeds=[f"https://seed{i}.example.com/document.pdf" for i in range(13)]
    policy={"maximum_explicit_seed_entries_per_company":100,"protect_valid_seeds_for_retrieval":True}
    registration,canonical=build_seed_registration(seeds,policy)
    candidates={}
    for index,url in enumerate(canonical):
        candidates[url]={"canonical_url":url,"protected_for_retrieval":True,"source_domain_class":"partner_hosted","source_type_hint":"pdf"}
    for index in range(721):
        url=f"https://ordinary{index % 7}.example.com/page/{index}"
        candidates[url]={"canonical_url":url,"protected_for_retrieval":False,"source_domain_class":"official_company","source_type_hint":"html"}
    budget={"maximum_canonical_non_seed_candidates_per_company":286,"maximum_retrieved_non_seed_documents_per_company":250,"maximum_non_seed_candidates_per_host":120,"maximum_career_pages_per_company":60,"maximum_low_priority_third_party_pages":40}
    selected,retrieval,audit=apply_candidate_budget(candidates,budget)
    assert registration["seeds_registered"] is True
    assert audit["protected_seed_count"]==13
    assert audit["protected_seed_selected_count"]==13
    assert audit["non_seed_candidates_before_budget"]==721
    assert audit["non_seed_candidates_selected_after_budget"]==286
    assert len(selected)==299
    assert all(item["protected_for_retrieval"] for item in retrieval[:13])


def test_v117_invalid_seed_has_seed_specific_failure():
    registration,canonical=build_seed_registration(["ftp://unsafe.example.com/file"],{"maximum_explicit_seed_entries_per_company":100,"protect_valid_seeds_for_retrieval":True})
    assert canonical==[]
    assert registration["seeds_registered"] is False
    assert registration["seed_registration_status"]=="failed_configuration_invalid_seed_url"


def test_complete_prompt_budget_reserves_gemma_output_and_preserves_semantics():
    artifact={
        "schema_version":"1.1.0",
        "context":{
            "target_company":{"name":"Example"},
            "portfolio_supplier":{"name":"dSPACE GmbH"},
            "company_name":"Example",
            "grounded_portfolio_items":[
                {"dspace_commercial_name":"EPSS","owner":"dSPACE GmbH","supplier":"dSPACE GmbH"},
                {"dspace_commercial_name":"XSG","owner":"dSPACE GmbH","supplier":"dSPACE GmbH"},
            ],
            "strongest_applicability_mappings":[
                {"target_company_entity_id":"hvdc","engineering_need_id":"controller_hil","dspace_capability_id":"simulation","dspace_commercial_name":"EPSS"},
                {"target_company_entity_id":"converter","engineering_need_id":"fpga_validation","dspace_capability_id":"fpga","dspace_commercial_name":"XSG"},
                {"target_company_entity_id":"extra","engineering_need_id":"extra","dspace_capability_id":"extra","dspace_commercial_name":"XSG"},
            ],
            "relevant_company_evidence":[{"description":"evidence "+("x"*500)} for _ in range(8)],
            "selected_dspace_chunks":[
                {"dspace_portfolio_item_id":"epss","section":"capabilities","text_preview":"y"*500},
                {"dspace_portfolio_item_id":"xsg","section":"capabilities","text_preview":"z"*500},
            ],
            "limitations":["unknown detail"]*8,
            "recommended_actions":["Review evidence."],
            "authority":"Deterministic inputs are authoritative.",
        },
        "metrics":{"minimum_relevant_evidence_required":3,"truncation_reasons":[]},
    }
    bundle={
        "system_prompt":"S"*9000,
        "ownership_contract":{"portfolio_supplier":{"name":"dSPACE GmbH"}},
        "user_template":"{{COMPANY_CONTEXT_JSON}}\n{{OUTPUT_SCHEMA_JSON}}",
        "output_schema":{"type":"object","properties":{"overall_assessment":{"type":"string"}}},
    }
    limits={
        "maximum_complete_prompt_tokens":6200,
        "conservative_characters_per_token":3,
        "native_context_window_tokens":8192,
        "reserved_output_tokens":1800,
        "context_safety_margin_tokens":192,
    }
    fitted=fit_complete_prompt(artifact,bundle,limits)
    metrics=fitted["metrics"]
    assert metrics["prompt_budget_satisfied"] is True
    assert metrics["estimated_complete_prompt_tokens"] <= 6200
    assert metrics["estimated_total_reserved_tokens"] <= 8192
    assert len(fitted["context"]["relevant_company_evidence"]) >= 3
    assert len(fitted["context"]["grounded_portfolio_items"]) == 2
    assert len(fitted["context"]["strongest_applicability_mappings"]) >= 2
    assert len(fitted["context"]["selected_dspace_chunks"]) == 2
