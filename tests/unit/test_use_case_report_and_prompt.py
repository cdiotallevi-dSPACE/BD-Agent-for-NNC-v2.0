from pathlib import Path

from bd_agent_neural_net_coder.llm_context_builder import build_llm_context
from bd_agent_neural_net_coder.prompt_loader import load_prompt_bundle
from bd_agent_neural_net_coder.report_generator import _use_case_rows


def test_use_case_rows_are_distinct_and_score_sorted():
    final={"overall_product_match":{"use_case_scores":[
        {"use_case_id":"tractive_limit","use_case_score":55,"supporting_source_ids":["SRC-0002"]},
        {"use_case_id":"battery_predictive_charging","use_case_score":65,"supporting_source_ids":["SRC-0001","SRC-0003"]},
        {"use_case_id":"battery_predictive_charging","use_case_score":60},
    ]}}
    assert _use_case_rows(final)==[("Battery Predictive Charging","SRC-0001, SRC-0003",65),("Tractive Limit","SRC-0002",55)]


def test_gemma_prompt_is_use_case_led_and_blocks_generic_feature_copying():
    root=Path(__file__).resolve().parents[2]
    bundle=load_prompt_bundle(root,"gemma2:9b")
    system=bundle["system_prompt"]
    user=bundle["user_template"]
    assert "highest-scoring item in ranked_use_cases" in system
    assert "Do not summarize or reproduce a generic list" in system
    assert "Do not copy" in user and "use_case_score" in user


def test_llm_context_exposes_ranked_use_case_scores():
    final={
        "target_company":{},"portfolio_supplier":{},"company_name":"GM",
        "overall_product_match":{"use_case_scores":[
            {"use_case_id":"tractive","use_case_score":55},
            {"use_case_id":"battery","use_case_score":65},
        ]},
        "semantic_scopes":{"dspace_portfolio":[]},"applicability_mappings":[],
    }
    limits={"maximum_input_characters":10000,"maximum_estimated_input_tokens":3000,
            "minimum_relevant_company_evidence_sources":0,"target_relevant_company_evidence_sources":0,
            "maximum_relevant_evidence_sources":0,"maximum_evidence_excerpt_characters_per_source":100,
            "maximum_portfolio_items":1,"maximum_applicability_mappings_per_item":1,
            "maximum_dspace_chunks_per_item":1,"maximum_limitations":2}
    artifact=build_llm_context(final,{"relevant_evidence":[]},[],limits)
    assert [x["use_case_id"] for x in artifact["context"]["ranked_use_cases"]]==["battery","tractive"]


def test_llm_context_keeps_top_three_use_cases_and_two_sources_each():
    scores=[{"use_case_id":name,"use_case_score":score} for name,score in (("battery",80),("tractive",70),("diagnostics",60),("cabin",50))]
    final={"target_company":{},"portfolio_supplier":{},"company_name":"GM","overall_product_match":{"use_case_scores":scores},"semantic_scopes":{"dspace_portfolio":[]},"applicability_mappings":[]}
    evidence=[]
    for use_case in ("battery","tractive","diagnostics","cabin"):
        for number in range(3):
            evidence.append({"source_id":f"SRC-{len(evidence)+1:04d}","description":f"{use_case} evidence {number}","nnc_use_case_scoring":{"use_case_id":use_case}})
    limits={"maximum_input_characters":18000,"maximum_estimated_input_tokens":5000,"minimum_relevant_company_evidence_sources":3,"target_relevant_company_evidence_sources":6,"maximum_relevant_evidence_sources":10,"maximum_evidence_excerpt_characters_per_source":320,"maximum_ranked_use_cases":3,"maximum_evidence_sources_per_use_case":2,"maximum_portfolio_items":1,"maximum_applicability_mappings_per_item":1,"maximum_dspace_chunks_per_item":1,"maximum_limitations":2}
    artifact=build_llm_context(final,{"relevant_evidence":evidence},[],limits)
    assert [item["use_case_id"] for item in artifact["context"]["ranked_use_cases"]]==["battery","tractive","diagnostics"]
    assert len(artifact["context"]["relevant_company_evidence"])==6
    assert artifact["metrics"]["evidence_sources_selected_per_use_case"]=={"battery":2,"tractive":2,"diagnostics":2}
