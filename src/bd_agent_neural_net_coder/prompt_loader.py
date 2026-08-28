from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml


class PromptBundleError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_prompt_bundle(root: Path, model: str) -> dict:
    manifest_path = root / "prompts/company_summary_prompt_manifest_v3.yaml"
    if not manifest_path.is_file():
        raise PromptBundleError("prompt manifest missing")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bundle = manifest.get("prompt_bundle", {})
    assets = {}
    effective_assets = {}
    for key in ("system_prompt", "user_template", "output_schema", "ownership_contract"):
        entry = bundle.get(key, {})
        path = (root / entry.get("path", "")).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise PromptBundleError(f"prompt asset missing or outside application root: {key}")
        raw = path.read_bytes()
        if not raw.strip():
            raise PromptBundleError(f"empty prompt asset: {key}")
        digest = _sha256(raw)
        if entry.get("sha256") != digest:
            raise PromptBundleError(f"prompt asset hash mismatch: {key}")
        text = raw.decode("utf-8")
        assets[key] = json.loads(text) if key == "output_schema" else yaml.safe_load(text) if key == "ownership_contract" else text
        effective_assets[key] = {
            "version": str(entry["version"]),
            "resolved_path": str(path),
            "sha256": digest,
        }
    if model not in bundle.get("compatible_models", []):
        raise PromptBundleError(f"prompt bundle incompatible with model: {model}")
    jsonschema.Draft202012Validator.check_schema(assets["output_schema"])
    clauses = assets["ownership_contract"]
    if clauses.get("portfolio_supplier", {}).get("name") != "dSPACE GmbH":
        raise PromptBundleError("ownership contract supplier mismatch")
    return {
        "bundle_id": bundle["bundle_id"],
        "system_prompt": assets["system_prompt"],
        "user_template": assets["user_template"],
        "output_schema": assets["output_schema"],
        "ownership_contract": assets["ownership_contract"],
        "effective_manifest": {
            "prompt_bundle_id": bundle["bundle_id"],
            "model": model,
            "loaded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ownership_contract_version": effective_assets["ownership_contract"]["version"],
            "assets": effective_assets,
            "validation_result": "valid",
        },
    }


def build_effective_prompt(bundle: dict, context: dict) -> str:
    payload = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    schema = json.dumps(bundle["output_schema"], ensure_ascii=False, separators=(",", ":"))
    contract = yaml.safe_dump(bundle["ownership_contract"], sort_keys=True, allow_unicode=True)
    return (
        bundle["system_prompt"].rstrip()
        + "\n\nOWNERSHIP CONTRACT\n"
        + contract
        + "\n"
        + bundle["user_template"].replace("{{COMPANY_CONTEXT_JSON}}", payload).replace("{{OUTPUT_SCHEMA_JSON}}", schema)
    )
