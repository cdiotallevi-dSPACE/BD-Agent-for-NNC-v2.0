import copy
import hashlib
import shutil
from pathlib import Path

import yaml
import json
import pytest

from bd_agent_neural_net_coder.llm_context_builder import build_llm_context
from bd_agent_neural_net_coder.narrative_ownership_validator import validate_narrative_ownership
from bd_agent_neural_net_coder.ownership_contract_builder import enrich_ownership
from bd_agent_neural_net_coder.prompt_loader import build_effective_prompt, load_prompt_bundle
from bd_agent_neural_net_coder.pipeline import Pipeline


ITEM={"dspace_portfolio_item_id":"electrical_power_systems_simulation_package_epss","dspace_commercial_name":"Electrical Power Systems Simulation Package (EPSS)","owner":"dSPACE GmbH","supplier":"dSPACE GmbH","aliases":["EPSS","Electrical Power Systems Simulation Package","power systems simulation package"]}


def test_schneider_possessive_sentence_is_rejected():
    response={"executive_summary":"Schneider Electric's power systems simulation package (EPSS) is highly applicable.","recommended_next_actions":[]}
    result=validate_narrative_ownership(response,"Schneider Electric",[],[ITEM])
    assert result["status"]=="invalid_response"
    assert result["failure_code"]=="llm_product_ownership_violation"


def test_dspace_attributed_sentence_is_valid():
    response={"executive_summary":"dSPACE's Electrical Power Systems Simulation Package (EPSS) is applicable to Schneider Electric's engineering needs.","recommended_next_actions":[]}
    result=validate_narrative_ownership(response,"Schneider Electric",[],[ITEM])
    assert result["status"]=="valid"


@pytest.mark.parametrize("assessment",[
    "The dSPACE Electrical Power Systems Simulation Package (EPSS) supports converter simulation.",
    "A dSPACE offering like Electrical Power Systems Simulation Package (EPSS) supports converter simulation.",
    "dSPACE offers two relevant offerings: the Electrical Power Systems Simulation Package (EPSS) and other tools.",
    "dSPACE offers two relevant offerings that address engineering needs: another system and the Electrical Power Systems Simulation Package (EPSS).",
    "The dSPACE Electrical Power Systems Simulation Package (EPSS) platform supports converter simulation.",
    "Electrical Power Systems Simulation Package (EPSS) from dSPACE supports converter simulation.",
    "Electrical Power Systems Simulation Package (EPSS) offering from dSPACE supports converter simulation.",
])
def test_unambiguous_dspace_attribution_variants_pass(assessment):
    result=validate_narrative_ownership(
        {"overall_assessment":assessment,"recommended_next_actions":[]},
        "Schneider Electric",[],[ITEM],
    )
    assert result["status"]=="valid"


def test_broader_attribution_does_not_allow_target_company_ownership():
    response={"overall_assessment":"Schneider Electric's Electrical Power Systems Simulation Package (EPSS) is used for simulation.","recommended_next_actions":[]}
    result=validate_narrative_ownership(response,"Schneider Electric",[],[ITEM])
    assert result["status"]=="invalid_response"
    assert result["failure_code"]=="llm_product_ownership_violation"


def test_ownership_enrichment_preserves_v114_score_and_mapping():
    final={"company_name":"Schneider Electric","overall_dspace_portfolio_applicability":87,"semantic_scopes":{"dspace_portfolio":[{"dspace_portfolio_item_id":ITEM["dspace_portfolio_item_id"],"hard_rule_passed":True,"dspace_applicability_score":90}]},"applicability_mappings":[{"mapping_id":"MAP-0001","mapping_display":"hvdc_converter_system -> controller_hil -> hvdc_real_time_simulation -> electrical_power_systems_simulation_package_epss","dspace_portfolio_item_id":ITEM["dspace_portfolio_item_id"]}]}
    baseline=(final["overall_dspace_portfolio_applicability"],final["applicability_mappings"][0]["mapping_display"])
    profiles=[{"dspace_portfolio_item_id":ITEM["dspace_portfolio_item_id"],"commercial_name":ITEM["dspace_commercial_name"],"owner":"dSPACE GmbH","supplier":"dSPACE GmbH","offering_type":"product","aliases":ITEM["aliases"]}]
    enrich_ownership(final,profiles)
    assert baseline==(final["overall_dspace_portfolio_applicability"],final["applicability_mappings"][0]["mapping_display"])


def test_context_retains_three_company_sources():
    from test_v113_report_contract import sample_final
    final=sample_final()
    relevant={"relevant_evidence":[{"source_id":f"SRC-{i}","description":"converter evidence","canonical_url":f"https://example.com/{i}","accepted_evidence_ids":[f"EVD-{i}"]} for i in range(8)]}
    limits={"maximum_input_characters":18000,"maximum_estimated_input_tokens":5000,"minimum_relevant_company_evidence_sources":3,"target_relevant_company_evidence_sources":6,"maximum_relevant_evidence_sources":10,"maximum_evidence_excerpt_characters_per_source":320,"maximum_portfolio_items":4,"maximum_applicability_mappings_per_item":3,"maximum_dspace_chunks_per_item":1,"maximum_limitations":8,"maximum_recommended_actions":8}
    artifact=build_llm_context(final,relevant,[],limits)
    assert artifact["metrics"]["selected_evidence_count"]>=3
    assert artifact["metrics"]["minimum_retention_rule_satisfied"] is True


def test_runtime_prompt_bundle_is_loaded_and_hashed():
    root=Path(__file__).resolve().parents[2]
    bundle=load_prompt_bundle(root,"gemma2:9b")
    prompt=build_effective_prompt(bundle,{"company_name":"Marker Company"})
    assert "The target company is the prospective user" in prompt
    assert "Marker Company" in prompt
    for asset in bundle["effective_manifest"]["assets"].values():
        assert len(asset["sha256"])==64


def test_prompt_marker_changes_effective_prompt_and_recorded_hash(tmp_path):
    source=Path(__file__).resolve().parents[2]/"prompts"
    destination=tmp_path/"prompts"
    shutil.copytree(source,destination)
    original=load_prompt_bundle(tmp_path,"gemma2:9b")
    system_path=destination/"company_summary_system_v3.txt"
    system_path.write_text(system_path.read_text(encoding="utf-8")+"\nTEST_PROMPT_MARKER\n",encoding="utf-8")
    manifest_path=destination/"company_summary_prompt_manifest_v3.yaml"
    manifest=yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest["prompt_bundle"]["system_prompt"]["sha256"]=hashlib.sha256(system_path.read_bytes()).hexdigest()
    manifest_path.write_text(yaml.safe_dump(manifest,sort_keys=False),encoding="utf-8")
    changed=load_prompt_bundle(tmp_path,"gemma2:9b")
    assert "TEST_PROMPT_MARKER" in build_effective_prompt(changed,{})
    assert original["effective_manifest"]["assets"]["system_prompt"]["sha256"]!=changed["effective_manifest"]["assets"]["system_prompt"]["sha256"]


def test_invalid_gemma_ownership_uses_fallback_without_retry(tmp_path,monkeypatch):
    from test_v113_report_contract import sample_final
    final=sample_final(); calls=[]
    class Response:
        def raise_for_status(self): return None
        def json(self):
            assessment="Siemens Energy's EPSS is applicable. "+" ".join(["Assessment context"]*69)
            return {"response":json.dumps({"company_name":"Siemens Energy","portfolio_supplier_name":"dSPACE GmbH","overall_assessment":assessment,"key_information_gaps":[],"recommended_next_actions":[]})}
    def post(*args,**kwargs): calls.append(1); return Response()
    monkeypatch.setattr("bd_agent_neural_net_coder.pipeline.httpx.post",post)
    cfg={"prewarm_model":False,"keep_alive":"30m","soft_timeout_warning_seconds":360,"temperature":0.2,"max_output_tokens":1800,"maximum_serialized_response_characters":8000,"timeout_seconds":480,"ownership_validation":{"first_mention_attribution_window_characters":100}}
    bundle={"system_prompt":"system","user_template":"{{COMPANY_CONTEXT_JSON}} {{OUTPUT_SCHEMA_JSON}}","output_schema":{"type":"object"},"ownership_contract":{}}
    Pipeline(Path.cwd())._summary_attempt(tmp_path,"siemens-energy","stamp",final,{"context":{}},cfg,bundle)
    assert len(calls)==1
    assert final["llm_summary_status"]=="invalid_response"
    assert final["narrative_source"]=="deterministic_template"
    assert final["overall_dspace_portfolio_applicability"]==96
    validation=json.loads((tmp_path/"siemens-energy_stamp_narrative_validation.json").read_text())
    assert validation["ownership_validation"]["failure_code"]=="llm_product_ownership_violation"
