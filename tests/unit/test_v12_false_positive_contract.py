from pathlib import Path

from bd_agent_neural_net_coder.company_attribution import establish_document_company_attribution
from bd_agent_neural_net_coder.config_manager import load_yaml
from bd_agent_neural_net_coder.evidence_context import extract_document_evidence
from bd_agent_neural_net_coder.relevant_evidence_builder import build_relevant_evidence


ROOT = Path(__file__).resolve().parents[2]
TAXONOMY = load_yaml(ROOT / "config/domains/tiny_edge_ai/company_domain_taxonomy.yaml")


def _doc(text, *, title="source.pdf", url="https://third.example/source.pdf", source_id="SRC-0001"):
    return {"source_id": source_id, "url": url, "requested_url": url, "title": title, "text": text,
            "pages": [{"page": 1, "text": text}], "error": None}


def _established(doc):
    return establish_document_company_attribution(
        doc, company="General Motors", official_domain="gm.com",
        company_aliases=["General Motors Company", "GMC", "GM"],
        candidate={"source_domain_class": "official_company"},
    )


def test_gm_ambiguous_alias_tinyml_paper_is_background_only():
    text = """TinyML for Small Microcontrollers
    Universidad Nacional de La Plata. EmbedIA deploys a convolutional neural network
    as a C++ application on a microcontroller using TensorFlow Lite Micro and CMSIS-NN.
    References
    In: Diaz, G.M. (eds.) Smart Technologies, Systems and Applications.
    """
    doc = _doc(text, title="Documento_completo.pdf")
    attribution = establish_document_company_attribution(
        doc, company="General Motors", official_domain="gm.com",
        company_aliases=["General Motors Company", "GMC", "GM"],
        candidate={"source_domain_class": "third_party_analytics"},
    )
    assert attribution["company_attribution_status"] == "not_established"
    assert attribution["attributed_company_id"] is None
    assert attribution["source_attribution_scope"] == "general_industry_background"
    assert set(attribution["reason_codes"]) == {
        "target_company_not_established", "ambiguous_company_alias_only",
        "bibliography_initials_alias_collision",
    }
    result = extract_document_evidence(doc, TAXONOMY, attribution)
    assert result["accepted"] == []
    assert result["context_bundles"] == []
    assert result["background"]
    assert all(x["score_contribution"] == 0 and not x["mapping_eligible"] for x in result["background"])


def test_owner_manual_ecu_is_not_mapping_or_relevant_evidence():
    doc = _doc(
        "Wheel speed sensors transmit information to the ABS electronic control unit. The controller operates the brakes.",
        title="2021-chevrolet-owners-manual.pdf", url="https://gm.com/owners-manual.pdf",
    )
    result = extract_document_evidence(doc, TAXONOMY, _established(doc))
    ecu = next(x for x in result["accepted"] if x["taxonomy_term_id"] == "automotive_ecu")
    assert not ecu["mapping_eligibility"]["eligible"]
    assert "target_only_no_neural_context" in ecu["mapping_eligibility"]["reason_codes"]
    relevant = build_relevant_evidence(result["accepted"], [{"source_id":"SRC-0001","url":doc["url"],"title":doc["title"],"source_type":"pdf","content_hash":"x","source_domain_class":"official_company"}], [{"mapping_id":"MAP-BAD","supporting_company_evidence_ids":[ecu["evidence_id"]],"engineering_need_id":"resource_fit_estimation"}])
    assert relevant["source_count"] == 0


def test_obd_linear_quantization_is_not_model_optimization():
    doc = _doc(
        "The ECU diagnostic signal uses linear quantization for exhaust gas and lambda sensor values.",
        title="19OBDG07 Diagnostics.pdf", url="https://gm.com/19OBDG07.pdf",
    )
    result = extract_document_evidence(doc, TAXONOMY, _established(doc))
    quant = next(x for x in result["accepted"] if x["taxonomy_term_id"] == "model_optimization")
    assert not quant["mapping_eligibility"]["eligible"]
    assert "signal_quantization_not_model_quantization" in quant["mapping_eligibility"]["reason_codes"]


def test_cross_document_keyword_mixing_produces_no_context_bundle():
    texts = [
        "General Motors research evaluates a convolutional neural network.",
        "General Motors exports an ONNX model into generated C code.",
        "General Motors vehicles contain an ABS electronic control unit.",
    ]
    bundles = []
    for index, text in enumerate(texts, 1):
        doc = _doc(text, source_id=f"SRC-{index:04d}")
        attr = establish_document_company_attribution(doc, company="General Motors", official_domain="gm.com", company_aliases=["GM"], candidate={"source_domain_class":"third_party_analytics"})
        bundles.extend(extract_document_evidence(doc, TAXONOMY, attr)["context_bundles"])
    assert bundles == []


def test_complete_local_bundle_is_mapping_eligible():
    doc = _doc("General Motors deploys a convolutional neural network from an ONNX model as generated C code on a microcontroller.")
    attr = establish_document_company_attribution(doc, company="General Motors", official_domain="gm.com", company_aliases=["GM"], candidate={"source_domain_class":"third_party_analytics"})
    result = extract_document_evidence(doc, TAXONOMY, attr)
    assert result["context_bundles"]
    assert any(x["mapping_eligibility"]["eligible"] for x in result["accepted"])


def test_candidate_contract_separates_scan_target_from_attribution():
    from bd_agent_neural_net_coder.search_orchestrator import generate_queries
    profile={"company_name":"General Motors","company_aliases":["GM"],"official_domains":["gm.com"],"official_asset_domains":[],"related_corporate_domains":[],"partner_domains":[],"specialist_domains":[]}
    query=next(x for x in generate_queries(profile) if x.family == "company_alias")
    assert query.priority == "low"
