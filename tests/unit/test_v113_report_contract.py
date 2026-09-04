import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
from pypdf import PdfReader

from bd_agent_neural_net_coder.llm_context_builder import build_llm_context
from bd_agent_neural_net_coder.pipeline import (
    DESIGN_DOCUMENT_VERSION,
    SPECIFICATION_VERSION,
    Pipeline,
    build_source_records,
)
from bd_agent_neural_net_coder.relevant_evidence_builder import build_relevant_evidence
from bd_agent_neural_net_coder.report_generator import render_reports, report_identity


def sample_final():
    mapping={"mapping_id":"MAP-0001","mapping_chain":["hvdc_converter_system","controller_hil","hvdc_real_time_simulation","electrical_power_systems_simulation_package_epss"],"mapping_display":"hvdc_converter_system -> controller_hil -> hvdc_real_time_simulation -> electrical_power_systems_simulation_package_epss","target_company_entity_id":"hvdc_converter_system","engineering_need_id":"controller_hil","dspace_capability_id":"hvdc_real_time_simulation","dspace_portfolio_item_id":"electrical_power_systems_simulation_package_epss","dspace_commercial_name":"Electrical Power Systems Simulation Package (EPSS)","owner":"dSPACE GmbH","supplier":"dSPACE GmbH","dspace_product_aliases":["EPSS","Electrical Power Systems Simulation Package"],"dspace_offering_type":"product","supporting_company_evidence_ids":["EVD-00001"],"dspace_source_references":[{"source_filename":"epss.pdf","page_start":2,"page_end":2,"section":"HVDC","chunk_id":"chunk-1"}]}
    moment=datetime(2026,7,27,5,40,39,tzinfo=timezone.utc)
    return {"run_id":"siemens-energy-20260726T094140Z","company_name":"Siemens Energy","target_company":{"name":"Siemens Energy","official_domain":"siemens-energy.com","country":"Germany","role":"prospective_user_of_applicable_dspace_offerings"},"portfolio_supplier":{"name":"dSPACE GmbH","role":"owner_and_supplier_of_all_dspace_portfolio_items"},"overall_dspace_portfolio_applicability":96,"overall_product_match":{"band":"strong","use_case_scores":[{"use_case_id":"hvdc_converter_control","use_case_score":96,"supporting_source_ids":["SRC-0001"]}]},"semantic_scopes":{"dspace_portfolio":[{"dspace_portfolio_item_id":"electrical_power_systems_simulation_package_epss","dspace_commercial_name":"Electrical Power Systems Simulation Package (EPSS)","owner":"dSPACE GmbH","supplier":"dSPACE GmbH","aliases":["EPSS","Electrical Power Systems Simulation Package"],"dspace_applicability_score":100,"hard_rule_passed":True}]},"applicability_mappings":[mapping],"report_data":{"relevant_evidence_source_ids":["SRC-0001"],"relevant_evidence_count":1,"applicability_mapping_ids":["MAP-0001"],"applicability_mapping_count":1,**report_identity("Siemens Energy",moment)}}


def test_runtime_manifest_uses_v110_design_metadata():
    assert SPECIFICATION_VERSION=="1.10"
    assert DESIGN_DOCUMENT_VERSION=="1.10.0"
    source=(Path(__file__).resolve().parents[2]/"src"/"bd_agent_neural_net_coder"/"pipeline.py").read_text(encoding="utf-8")
    assert 'manifest["specification_version"]="1.8"' not in source
    assert 'manifest["design_document_version"]="1.8.0"' not in source


def test_relevant_evidence_deduplicates_source_and_remains_traceable():
    accepted=[{"evidence_id":"EVD-00001","source_id":"SRC-0001","source_page":2,"taxonomy_term_id":"hvdc_converter_system","passage":"HVDC converter control","assessment":"accepted"},{"evidence_id":"EVD-00002","source_id":"SRC-0001","source_page":4,"taxonomy_term_id":"hvdc_converter_system","passage":"grid fault operation","assessment":"accepted"}]
    sources=[{"source_id":"SRC-0001","url":"https://example.com/hvdc.pdf","title":"HVDC PLUS","source_type":"pdf","content_hash":"sha256:abc","source_domain_class":"official_company_asset"}]
    mappings=[{"mapping_id":"MAP-0001","engineering_need_id":"controller_hil","supporting_company_evidence_ids":["EVD-00001","EVD-00002"]}]
    result=build_relevant_evidence(accepted,sources,mappings)
    assert result["source_count"]==1
    assert result["relevant_evidence"][0]["display_number"]==1
    assert result["relevant_evidence"][0]["accepted_evidence_ids"]==["EVD-00001","EVD-00002"]
    assert "pages 2, 4" in result["relevant_evidence"][0]["description"]


def test_patent_relevant_evidence_has_stable_identity_and_complete_sentence():
    analysis={"patent_neural_evidence_strength":"claimed_optional_embodiment","neural_model_status":"possible_but_not_selected_or_confirmed","onboard_context":"confirmed"}
    accepted=[{"evidence_id":"EVD-00001","source_id":"SRC-0001","source_page":None,"taxonomy_term_id":"neural_network","passage":"he exemplary model discussed above is updated. The controller estimates a tractive limit using a neural network.","assessment":"accepted","relevance_class":"nnc_applicability_evidence","patent_analysis":analysis,"nnc_use_case_scoring":{"use_case_score":55,"mapping_eligible":True,"mapping_class":"nnc_influence_opportunity"}}]
    sources=[{"source_id":"SRC-0001","url":"https://patents.google.com/patent/US12246700B2/en","title":"US12246700B2 - Machine learning tractive limit - Google Patents","patent_title":"Machine learning-based tractive limit and wheel stability status estimation","normalized_publication_number":"US12246700B2","patent_abstract":"e limit. In another aspect, a controller estimates wheel stability using a classification model.","source_type":"html","content_hash":"sha256:patent","source_domain_class":"specialist_patent_source"}]
    mappings=[{"mapping_id":"MAP-0001","engineering_need_id":"edge_deployment","supporting_company_evidence_ids":["EVD-00001"]}]
    item=build_relevant_evidence(accepted,sources,mappings)["relevant_evidence"][0]
    assert item["description"].startswith("Patent US12246700B2 — Machine learning-based tractive limit and wheel stability status estimation.")
    assert "In another aspect" in item["description"]
    assert "he exemplary" not in item["description"]
    assert ". e limit." not in item["description"]


def test_signed_uspto_transport_url_is_not_published_as_relevant_evidence_url():
    analysis={"patent_neural_evidence_strength":"confirmed_required_or_implemented","neural_model_status":"confirmed_as_embodiment","onboard_context":"confirmed"}
    evidence={"evidence_id":"EVD-00001","source_id":"SRC-0001","taxonomy_term_id":"neural_network","passage":"The neural network estimates an internal battery state.","assessment":"accepted","relevance_class":"nnc_applicability_evidence","patent_analysis":analysis,"nnc_use_case_scoring":{"use_case_score":65,"mapping_eligible":True,"mapping_class":"nnc_deployment_fit"}}
    signed="https://data.uspto.gov/files/patent.xml?Expires=1&Signature=secret&Key-Pair-Id=key"
    source={"source_id":"SRC-0001","url":signed,"source_type":"html","content_hash":"sha256:x","source_domain_class":"specialist_patent_source","normalized_publication_number":"US20240302440A1","patent_application_number":"18180520","patent_title":"Dynamic and predictive control of battery charging"}
    mapping={"mapping_id":"MAP-0001","engineering_need_id":"edge_deployment","supporting_company_evidence_ids":["EVD-00001"]}
    item=build_relevant_evidence([evidence],[source],[mapping])["relevant_evidence"][0]
    assert item["canonical_url"]=="https://data.uspto.gov/patent-file-wrapper/search/details/18180520/application-data"
    assert "Signature" not in item["canonical_url"]
    assert "Expires" not in item["canonical_url"]


def test_native_patent_title_propagates_when_retrieved_document_title_is_empty():
    signed="https://data.uspto.gov/files/patent.xml?Expires=1&Signature=secret"
    docs=[{"requested_url":signed,"url":signed,"title":"","source_type":"html","content_hash":"sha256:x","parse_status":"retrieved","error":None}]
    candidates={signed:{"normalized_publication_number":"US20240302440A1","patent_application_number":"18180520","patent_title":"Dynamic and predictive control of battery charging","title_hint":"Dynamic and predictive control of battery charging","report_canonical_url":"https://data.uspto.gov/patent-file-wrapper/search/details/18180520/application-data","source_domain_class":"specialist_patent_source","snippet":"A processor estimates a dynamic battery variable."}}
    source=build_source_records(docs,candidates,set())[0]
    assert source["title"]=="Dynamic and predictive control of battery charging"
    assert source["patent_title"]==source["title"]

    analysis={"patent_neural_evidence_strength":"confirmed_required_or_implemented","neural_model_status":"confirmed_as_embodiment","onboard_context":"confirmed"}
    evidence={"evidence_id":"EVD-00001","source_id":"SRC-0001","taxonomy_term_id":"neural_network","passage":"The neural network estimates an internal battery state.","assessment":"accepted","relevance_class":"nnc_applicability_evidence","patent_analysis":analysis,"nnc_use_case_scoring":{"use_case_score":65,"mapping_eligible":True,"mapping_class":"nnc_deployment_fit"}}
    mapping={"mapping_id":"MAP-0001","engineering_need_id":"edge_deployment","supporting_company_evidence_ids":["EVD-00001"]}
    item=build_relevant_evidence([evidence],[source],[mapping])["relevant_evidence"][0]
    assert item["source_title"]=="Dynamic and predictive control of battery charging"


def test_curated_context_stays_under_v113_limits():
    final=sample_final(); relevant={"relevant_evidence":[{"source_id":f"SRC-{i}","description":"x"*500,"canonical_url":f"https://example.com/{i}","accepted_evidence_ids":[f"EVD-{i}"]} for i in range(30)]}
    limits={"maximum_input_characters":18000,"maximum_estimated_input_tokens":5000,"minimum_relevant_company_evidence_sources":3,"target_relevant_company_evidence_sources":6,"maximum_relevant_evidence_sources":10,"maximum_evidence_excerpt_characters_per_source":320,"maximum_portfolio_items":4,"maximum_applicability_mappings_per_item":3,"maximum_dspace_chunks_per_item":1,"maximum_limitations":8,"maximum_recommended_actions":8}
    artifact=build_llm_context(final,relevant,[],limits)
    assert artifact["metrics"]["curated_context_characters"]<=18000
    assert artifact["metrics"]["estimated_input_tokens"]<=5000
    assert 3<=artifact["metrics"]["selected_evidence_count"]<=10


def test_timeout_fallback_is_informative_and_exactly_one_summary_call(tmp_path,monkeypatch):
    final=sample_final(); calls=[]
    def timeout(*args,**kwargs): calls.append(1); raise httpx.ReadTimeout("timed out")
    monkeypatch.setattr("bd_agent_neural_net_coder.pipeline.httpx.post",timeout)
    cfg={"prewarm_model":False,"keep_alive":"30m","soft_timeout_warning_seconds":360,"temperature":0.2,"max_output_tokens":1200,"timeout_seconds":480,"ownership_validation":{"first_mention_attribution_window_characters":100}}
    bundle={"system_prompt":"system","user_template":"{{COMPANY_CONTEXT_JSON}} {{OUTPUT_SCHEMA_JSON}}","output_schema":{"type":"object"},"ownership_contract":{}}
    Pipeline(Path.cwd())._summary_attempt(tmp_path,"siemens-energy","20260726T094140Z",final,{"context":{"score":96}},cfg,bundle)
    assert len(calls)==1 and final["llm_summary_status"]=="timeout"
    text=final["narrative"]["executive_summary"]
    assert "96/100" in text and "1 relevant target-company sources" in text and "1 grounded applicability mappings" in text and "status was timeout" in text


def test_prompt_budget_failure_skips_gemma_but_preserves_deterministic_report(tmp_path,monkeypatch):
    final=sample_final(); calls=[]
    monkeypatch.setattr("bd_agent_neural_net_coder.pipeline.httpx.post",lambda *args,**kwargs:calls.append(1))
    cfg={"prewarm_model":False,"keep_alive":"30m","soft_timeout_warning_seconds":360,"temperature":0.2,"max_output_tokens":1800,"maximum_serialized_response_characters":8000,"timeout_seconds":480,"ownership_validation":{"first_mention_attribution_window_characters":100}}
    bundle={"system_prompt":"S"*20000,"user_template":"{{COMPANY_CONTEXT_JSON}} {{OUTPUT_SCHEMA_JSON}}","output_schema":{"type":"object"},"ownership_contract":{}}
    context={"schema_version":"1.1.0","context":{"ranked_use_cases":[{"use_case_id":"battery"}],"relevant_company_evidence":[{"description":"evidence"}],"strongest_applicability_mappings":[],"grounded_portfolio_items":[],"selected_dspace_chunks":[],"limitations":[],"recommended_actions":[]},"metrics":{"minimum_relevant_evidence_required":1,"truncation_reasons":[]}}
    limits={"maximum_complete_prompt_tokens":100,"conservative_characters_per_token":3,"native_context_window_tokens":8192,"reserved_output_tokens":1800,"context_safety_margin_tokens":192}
    fitted=Pipeline(Path.cwd())._summary_attempt(tmp_path,"siemens-energy","stamp",final,context,cfg,bundle,limits)
    assert calls==[]
    assert final["llm_summary_status"]=="skipped_prompt_budget"
    assert final["llm_failure_code"]=="llm_prompt_budget_exceeded"
    assert final["narrative_source"]=="deterministic_template"
    assert final["llm_fallback_used"] is True
    assert fitted["metrics"]["prompt_budget_satisfied"] is False
    validation=json.loads((tmp_path/"siemens-energy_stamp_narrative_validation.json").read_text())
    assert validation["overall_status"]=="skipped_prompt_budget"


def test_pdf_has_readable_name_mappings_before_evidence_and_clickable_url(tmp_path):
    final=sample_final(); final["narrative"]={"executive_summary":"Deterministic narrative."}
    relevant={"relevant_evidence":[{"display_number":1,"source_id":"SRC-0001","description":"HVDC PLUS, page 2: converter control","canonical_url":"https://example.com/hvdc.pdf"}]}
    moment=datetime(2026,7,27,5,40,39,tzinfo=timezone.utc)
    pdf=render_reports(tmp_path,"siemens-energy","20260726T094140Z",final,relevant,moment)
    assert pdf.name=="Siemens-Energy_Sales-Assessment_2026-07-27_05-40-39_UTC.pdf"
    reader=PdfReader(pdf); text="\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Report generated on 27 July 2026 at 05:40:39 UTC" in text
    assert "Company domain: siemens-energy.com" in text
    assert "Country: Germany" in text
    assert "OVERALL ASSESSMENT" in text and "Narrative" not in text
    assert "Customer Evidence / Readiness" in " ".join(text.split())
    assert "Potential NNC Capability" in " ".join(text.split())
    assert "Source ID" in text
    assert "SRC-0001" in text
    markdown=(tmp_path/"siemens-energy_20260726T094140Z_sales_assessment.md").read_text(encoding="utf-8")
    assert "| Source ID | Evidence | URL |" in markdown
    assert "| SRC-0001 |" in markdown
    assert "| 1 |" not in markdown
    assert text.index("Use-Case Product Fit")<text.index("Relevant Evidence")<text.index("COMPANY BACKGROUND EVIDENCE")<text.index("Applicability Mappings")<text.index("Authoritative dSPACE Portfolio Sources")
    assert any("/URI" in str(annotation.get_object().get("/A",{})) for page in reader.pages for annotation in page.get("/Annots",[]))


def test_unscored_source_is_reported_only_as_company_background_evidence(tmp_path):
    final=sample_final(); final["narrative"]={"executive_summary":"Deterministic narrative."}
    final["report_data"].update({"company_background_evidence_source_ids":["SRC-0007"],"company_background_evidence_count":1})
    relevant={"relevant_evidence":[{"display_number":1,"source_id":"SRC-0001","description":"Scored use-case evidence.","canonical_url":"https://example.com/use-case"}],
              "company_background_evidence":[{"display_number":1,"source_id":"SRC-0007","description":"General company neural-network context.","canonical_url":"https://example.com/background"}]}
    pdf=render_reports(tmp_path,"siemens-energy","20260726T094140Z",final,relevant,datetime(2026,7,27,5,40,39,tzinfo=timezone.utc))
    text="\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
    relevant_block=text.split("Relevant Evidence",1)[1].split("COMPANY BACKGROUND EVIDENCE",1)[0]
    background_block=text.split("COMPANY BACKGROUND EVIDENCE",1)[1].split("Applicability Mappings",1)[0]
    assert "SRC-0007" not in relevant_block
    assert "SRC-0007" in background_block


def test_pdf_shortens_evidence_display_without_mutating_json(tmp_path):
    final=sample_final(); final["narrative"]={"executive_summary":"Deterministic narrative."}
    original="Long evidence description containing detailed page references and several technical excerpts for audit traceability."
    relevant={"relevant_evidence":[{"display_number":1,"source_id":"SRC-0001","description":original,"canonical_url":"https://example.com/hvdc.pdf"}]}
    pdf=render_reports(tmp_path,"siemens-energy","20260726T094140Z",final,relevant,datetime(2026,7,27,5,40,39,tzinfo=timezone.utc))
    text="\n".join(page.extract_text() or "" for page in PdfReader(pdf).pages)
    assert relevant["relevant_evidence"][0]["description"]==original
    assert original not in text
    assert "Long evidence description" in text


def test_multi_page_evidence_table_repeats_headers(tmp_path):
    final=sample_final(); final["narrative"]={"executive_summary":"Deterministic narrative."}
    relevant={"relevant_evidence":[{"display_number":i+1,"source_id":f"SRC-{i+1:04d}","description":f"Evidence source {i}: "+"converter control and grid validation "*4,"canonical_url":f"https://example.com/technical/publication/{i}/long-document-name.pdf"} for i in range(55)]}
    final["report_data"]["relevant_evidence_source_ids"]=[x["source_id"] for x in relevant["relevant_evidence"]]
    final["overall_product_match"]["use_case_scores"][0]["supporting_source_ids"]=list(final["report_data"]["relevant_evidence_source_ids"])
    pdf=render_reports(tmp_path,"siemens-energy","20260726T094140Z",final,relevant,datetime(2026,7,27,5,40,39,tzinfo=timezone.utc))
    reader=PdfReader(pdf); page_texts=[page.extract_text() or "" for page in reader.pages]
    assert len(reader.pages)>1
    evidence_pages=[text for text in page_texts if "https://example.com/technical" in text]
    assert len(evidence_pages)>1 and all("URL" in text.splitlines() for text in evidence_pages)
