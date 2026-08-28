from pathlib import Path
from bd_agent_neural_net_coder.model_runtime import (
    EMBEDDING_MODEL, FINAL_REPORT_MODEL, validate_collection_manifest,
)

def test_fixed_production_models():
    assert EMBEDDING_MODEL == "bge-large"
    assert FINAL_REPORT_MODEL == "gemma2:9b"

def test_collection_model_mismatch_requires_reindex(tmp_path: Path):
    manifest=tmp_path/"manifest.json"
    manifest.write_text('{"embedding_model":"other","embedding_dimension":1024}')
    result=validate_collection_manifest(manifest)
    assert result["query_allowed"] is False
    assert result["required_action"]=="full_re_embedding_and_re_indexing"
