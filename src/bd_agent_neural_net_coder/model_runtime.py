from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

OLLAMA_URL = "http://127.0.0.1:11434"
EMBEDDING_MODEL = "bge-large"
FINAL_REPORT_MODEL = "gemma2:9b"

def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def validate_models(base_url: str = OLLAMA_URL) -> dict:
    result = {
        "validated_at": _now(), "provider": "ollama", "ollama_url": base_url,
        "embedding": {"model": EMBEDDING_MODEL, "available": False, "request_ok": False, "dimension": None, "digest": None},
        "final_report": {"model": FINAL_REPORT_MODEL, "available": False, "request_ok": False, "valid_json": False},
    }
    try:
        with httpx.Client(base_url=base_url, timeout=120) as client:
            response = client.get("/api/tags")
            response.raise_for_status()
            installed = {item["name"]: item for item in response.json().get("models", [])}
            embed_entry = installed.get(EMBEDDING_MODEL) or installed.get(f"{EMBEDDING_MODEL}:latest")
            report_entry = installed.get(FINAL_REPORT_MODEL)
            result["embedding"]["available"] = embed_entry is not None
            result["embedding"]["digest"] = embed_entry.get("digest") if embed_entry else None
            result["final_report"]["available"] = report_entry is not None
            if embed_entry:
                response = client.post("/api/embed", json={"model": EMBEDDING_MODEL, "input": "BDA model preflight"})
                response.raise_for_status()
                vectors = response.json().get("embeddings", [])
                result["embedding"]["dimension"] = len(vectors[0]) if vectors else 0
                result["embedding"]["request_ok"] = bool(vectors and vectors[0])
            if report_entry:
                response = client.post("/api/generate", json={
                    "model": FINAL_REPORT_MODEL, "stream": False, "format": "json",
                    "options": {"temperature": 0.2, "num_predict": 80},
                    "prompt": 'Return only JSON: {"executive_summary":"model preflight","next_actions":[]}',
                })
                response.raise_for_status()
                parsed = json.loads(response.json()["response"])
                result["final_report"]["request_ok"] = True
                result["final_report"]["valid_json"] = isinstance(parsed.get("executive_summary"), str) and isinstance(parsed.get("next_actions"), list)
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
        if isinstance(exc, httpx.HTTPStatusError):
            result["http_status"] = exc.response.status_code
            result["response_body"] = exc.response.text[:1000]
    result["semantic_runtime_ready"] = bool(result["embedding"]["available"] and result["embedding"]["request_ok"] and (result["embedding"]["dimension"] or 0) > 0)
    result["final_report_runtime_ready"] = bool(result["final_report"]["available"] and result["final_report"]["request_ok"] and result["final_report"]["valid_json"])
    return result

def validate_collection_manifest(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "query_allowed": False, "reason": "collection_manifest_missing"}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    actual = manifest.get("embedding_model")
    if actual != EMBEDDING_MODEL:
        return {"exists": True, "query_allowed": False, "reason": "embedding_model_mismatch", "expected": EMBEDDING_MODEL, "actual": actual, "required_action": "full_re_embedding_and_re_indexing"}
    if not manifest.get("embedding_dimension"):
        return {"exists": True, "query_allowed": False, "reason": "embedding_dimension_missing"}
    return {"exists": True, "query_allowed": True, "embedding_model": actual}
