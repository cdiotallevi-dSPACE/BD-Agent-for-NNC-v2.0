from __future__ import annotations

import json
from copy import deepcopy

from .prompt_loader import build_effective_prompt


def estimate_prompt_tokens(prompt: str, characters_per_token: int = 3) -> int:
    """Conservative deterministic estimate for the complete Gemma prompt."""
    return (len(prompt.encode("utf-8")) + characters_per_token - 1) // characters_per_token


def fit_complete_prompt(context_artifact: dict, prompt_bundle: dict, limits: dict) -> dict:
    """Fit the final serialized prompt while preserving mandatory semantic content."""
    artifact = deepcopy(context_artifact)
    context = artifact["context"]
    budget = int(limits["maximum_complete_prompt_tokens"])
    chars_per_token = int(limits["conservative_characters_per_token"])
    minimum_evidence = int(artifact["metrics"]["minimum_relevant_evidence_required"])
    reductions = list(artifact["metrics"].get("truncation_reasons", []))

    def measure() -> tuple[str, int]:
        prompt = build_effective_prompt(prompt_bundle, context)
        return prompt, estimate_prompt_tokens(prompt, chars_per_token)

    prompt, tokens = measure()
    while tokens > budget:
        if len(context["relevant_company_evidence"]) > minimum_evidence:
            context["relevant_company_evidence"].pop()
            reductions.append("complete_prompt_company_evidence_reduced")
        elif len(context["strongest_applicability_mappings"]) > len(context["grounded_portfolio_items"]):
            context["strongest_applicability_mappings"].pop()
            reductions.append("complete_prompt_mapping_variants_reduced")
        elif len(context.get("ranked_use_cases",[])) > 1:
            context["ranked_use_cases"].pop()
            reductions.append("complete_prompt_lower_ranked_use_cases_reduced")
        elif any(len(item.get("description", "")) > 160 for item in context["relevant_company_evidence"]):
            for item in context["relevant_company_evidence"]:
                item["description"] = item.get("description", "")[:160]
            reductions.append("complete_prompt_evidence_excerpts_shortened")
        elif any(len(item.get("text_preview", "")) > 180 for item in context["selected_dspace_chunks"]):
            for item in context["selected_dspace_chunks"]:
                item["text_preview"] = item.get("text_preview", "")[:180]
            reductions.append("complete_prompt_dspace_previews_shortened")
        elif context.get("limitations"):
            context["limitations"].pop()
            reductions.append("complete_prompt_limitations_reduced")
        elif context.get("recommended_actions"):
            context["recommended_actions"].pop()
            reductions.append("complete_prompt_recommended_actions_removed")
        elif len(context.get("selected_dspace_chunks",[])) > 1:
            context["selected_dspace_chunks"].pop()
            reductions.append("complete_prompt_optional_dspace_chunks_reduced")
        else:
            raise ValueError("mandatory complete LLM prompt exceeds reserved context budget")
        prompt, tokens = measure()

    native = int(limits["native_context_window_tokens"])
    reserved = int(limits["reserved_output_tokens"])
    safety = int(limits["context_safety_margin_tokens"])
    if budget + reserved + safety > native:
        raise ValueError("invalid LLM context reservation contract")
    artifact["metrics"].update({
        "complete_prompt_characters": len(prompt),
        "complete_prompt_utf8_bytes": len(prompt.encode("utf-8")),
        "estimated_complete_prompt_tokens": tokens,
        "maximum_complete_prompt_tokens": budget,
        "native_context_window_tokens": native,
        "reserved_output_tokens": reserved,
        "context_safety_margin_tokens": safety,
        "estimated_total_reserved_tokens": tokens + reserved + safety,
        "prompt_budget_satisfied": True,
        "truncation_reasons": sorted(set(reductions)),
    })
    artifact["schema_version"] = "1.2.0"
    return artifact


def build_llm_context(final:dict,relevant:dict,retrieval_records:list[dict],limits:dict)->dict:
    max_chars=min(int(limits["maximum_input_characters"]),int(limits["maximum_estimated_input_tokens"])*4)
    available=list(relevant.get("relevant_evidence",[]))
    available_total_count=len(available)
    maximum_use_cases=int(limits.get("maximum_ranked_use_cases",3))
    maximum_evidence_per_use_case=int(limits.get("maximum_evidence_sources_per_use_case",2))
    ranked_scores=sorted(final.get("overall_product_match",{}).get("use_case_scores",[]),key=lambda x:-int(x.get("use_case_score",0)))[:maximum_use_cases]
    ranked_ids=[item.get("use_case_id") for item in ranked_scores if item.get("use_case_id")]
    selected_available=[]; selected_source_ids=set(); evidence_per_use_case={}
    for use_case_id in ranked_ids:
        matches=[item for item in available
                 if (item.get("nnc_use_case_scoring") or {}).get("use_case_id")==use_case_id
                 or use_case_id in item.get("use_case_classes",[])]
        chosen=[]
        for item in matches:
            if item.get("source_id") in selected_source_ids: continue
            chosen.append(item); selected_available.append(item); selected_source_ids.add(item.get("source_id"))
            if len(chosen)>=maximum_evidence_per_use_case: break
        evidence_per_use_case[use_case_id]=len(chosen)
    for item in available:
        if len(selected_available)>=min(int(limits["target_relevant_company_evidence_sources"]),maximum_use_cases*maximum_evidence_per_use_case): break
        if item.get("source_id") in selected_source_ids: continue
        selected_available.append(item); selected_source_ids.add(item.get("source_id"))
    if selected_available:
        available=selected_available
    minimum=min(len(available),int(limits["minimum_relevant_company_evidence_sources"]))
    target=min(len(available),int(limits["target_relevant_company_evidence_sources"]),int(limits["maximum_relevant_evidence_sources"]))
    assessed=sorted((item for item in final["semantic_scopes"]["dspace_portfolio"] if item.get("hard_rule_passed")),key=lambda item:(-item["dspace_applicability_score"],item["dspace_portfolio_item_id"]))[:limits["maximum_portfolio_items"]]
    allowed_items={item["dspace_portfolio_item_id"] for item in assessed}

    mappings=[]; seen_mapping_variants=set()
    for item in final["applicability_mappings"]:
        if item["dspace_portfolio_item_id"] not in allowed_items: continue
        variant=(item["dspace_portfolio_item_id"],item["target_company_entity_id"],item["dspace_capability_id"])
        if variant in seen_mapping_variants: continue
        seen_mapping_variants.add(variant); mappings.append(item)
    selected_mappings=[]
    for portfolio_id in sorted(allowed_items):
        selected_mappings.extend([item for item in mappings if item["dspace_portfolio_item_id"]==portfolio_id][:limits["maximum_applicability_mappings_per_item"]])

    evidence=[{"description":item["description"][:limits["maximum_evidence_excerpt_characters_per_source"]]} for item in available[:target]]
    chunks=[]; seen_chunks=set()
    for record in retrieval_records:
        selected=[chunk for chunk in record.get("returned_chunks",[]) if chunk.get("selected")]
        kept=0
        for chunk in selected:
            if chunk["chunk_id"] in seen_chunks: continue
            seen_chunks.add(chunk["chunk_id"])
            chunks.append({
                "dspace_portfolio_item_id":record.get("dspace_portfolio_item_id"),
                **{key:chunk.get(key) for key in ("source_filename","section","text_preview")},
            })
            kept+=1
            if kept>=limits["maximum_dspace_chunks_per_item"]: break

    context={
        "target_company":final["target_company"],
        "portfolio_supplier":final["portfolio_supplier"],
        "company_name":final["company_name"],
        "ranked_use_cases":[{
            "use_case_id":item.get("use_case_id"),
            "use_case_score":item.get("use_case_score"),
            "relevance_band":item.get("relevance_band"),
            "mapping_class":item.get("mapping_class"),
            "company_neural_application":item.get("company_neural_application"),
            "edge_deployment_intent":item.get("edge_deployment_intent"),
            "deployment_workflow_fit":item.get("deployment_workflow_fit"),
        } for item in ranked_scores],
        "grounded_portfolio_items":[{
            key:item.get(key) for key in (
                "dspace_commercial_name","offering_type","owner","supplier",
                "relationship_to_target","dspace_applicability_score",
            )
        } for item in assessed],
        "strongest_applicability_mappings":[{
            key:item.get(key) for key in (
                "target_company_entity_id","engineering_need_id","dspace_capability_id",
                "dspace_commercial_name","applicability_relations","dspace_applicability_score",
            )
        } for item in selected_mappings],
        "relevant_company_evidence":evidence,
        "selected_dspace_chunks":chunks,
        "limitations":final.get("limitations",[])[:limits["maximum_limitations"]],
        "recommended_actions":["Review evidence and qualification questions before outreach."],
        "authority":"Deterministic scores, mappings, IDs, grounding, ownership, and supplier metadata are authoritative.",
    }
    truncation=[]
    while len(json.dumps(context,ensure_ascii=False,separators=(",",":")))>max_chars:
        if len(context["selected_dspace_chunks"])>len(assessed):
            context["selected_dspace_chunks"].pop(); truncation.append("duplicate_dspace_chunks_removed")
        elif len(context["strongest_applicability_mappings"])>len(assessed):
            context["strongest_applicability_mappings"].pop(); truncation.append("mapping_variants_reduced")
        elif len(context["relevant_company_evidence"])>minimum:
            context["relevant_company_evidence"].pop(); truncation.append("company_evidence_reduced_to_minimum")
        elif context["selected_dspace_chunks"]:
            context["selected_dspace_chunks"].pop(); truncation.append("dspace_chunks_reduced")
        elif context["strongest_applicability_mappings"]:
            context["strongest_applicability_mappings"].pop(); truncation.append("mappings_reduced")
        else:
            raise ValueError("mandatory LLM summary context exceeds configured limit")
    if available and not context["relevant_company_evidence"]:
        raise ValueError("selected_evidence_count cannot be zero when relevant evidence exists")
    if len(context["relevant_company_evidence"])<minimum:
        raise ValueError("minimum relevant company evidence retention failed")
    payload=json.dumps(context,ensure_ascii=False,separators=(",",":"))
    metrics={
        "source_json_characters":len(json.dumps(final,ensure_ascii=False)),
        "curated_context_characters":len(payload),
        "estimated_input_tokens":(len(payload)+3)//4,
        "relevant_evidence_available_count":available_total_count,
        "minimum_relevant_evidence_required":minimum,
        "minimum_retention_rule_satisfied":len(context["relevant_company_evidence"])>=minimum,
        "selected_evidence_count":len(context["relevant_company_evidence"]),
        "omitted_evidence_count":available_total_count-len(context["relevant_company_evidence"]),
        "selected_mapping_count":len(context["strongest_applicability_mappings"]),
        "omitted_mapping_count":max(0,len(final["applicability_mappings"])-len(context["strongest_applicability_mappings"])),
        "selected_dspace_chunk_count":len(context["selected_dspace_chunks"]),
        "maximum_ranked_use_cases":maximum_use_cases,
        "maximum_evidence_sources_per_use_case":maximum_evidence_per_use_case,
        "evidence_sources_selected_per_use_case":evidence_per_use_case,
        "truncation_reasons":sorted(set(truncation)),
    }
    return {"schema_version":"1.1.0","context":context,"metrics":metrics}
