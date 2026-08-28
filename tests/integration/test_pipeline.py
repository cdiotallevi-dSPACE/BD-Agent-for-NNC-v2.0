from pathlib import Path
from bd_agent_neural_net_coder.pipeline import Pipeline
def test_evidence_extraction_and_mapping():
    root=Path(__file__).resolve().parents[2]; p=Pipeline(root)
    docs=[{"url":"https://example.test/tiny-ai","title":"Tiny AI","text":"We deploy a convolutional neural network as an ONNX model on a microcontroller.","pages":[{"page":1,"text":"We deploy a convolutional neural network as an ONNX model on a microcontroller."}],"error":None}]
    accepted,rejected=p._extract(docs)
    assert accepted and not rejected
    assert all(e["entity_scope"]=="target_company" for e in accepted)
    assert all(e["mapping_eligibility"]["eligible"] for e in accepted)
