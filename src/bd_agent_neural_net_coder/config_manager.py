from __future__ import annotations
import json
from pathlib import Path
import yaml
import copy
from jsonschema import Draft202012Validator

def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict): raise ValueError(f"{path}: expected mapping")
    return data

def _deep_merge(base: dict, override: dict) -> dict:
    result=copy.deepcopy(base)
    for key,value in override.items():
        if isinstance(value,dict) and isinstance(result.get(key),dict):
            result[key]=_deep_merge(result[key],value)
        else:
            result[key]=copy.deepcopy(value)
    return result

def load_search_config(root: Path, run_profile: str | None = None) -> dict:
    """Load search configuration and apply a named, auditable run profile."""
    config=load_yaml(root/"config/search_providers.yaml")
    name=run_profile or "standard"
    profiles=config.pop("run_profiles",{})
    if name=="standard" and not profiles:
        profiles={"standard":{}}
    if name not in profiles:
        raise ValueError(f"unknown BDA run profile: {name}")
    effective=_deep_merge(config,profiles[name])
    effective["active_run_profile"]=name
    return effective
def validate_all(root: Path) -> list[str]:
    errors: list[str] = []
    for path in root.rglob("*.yaml"):
        schema_path = path.parent / "schemas" / f"{path.stem}.schema.json"
        if not schema_path.exists():
            errors.append(f"missing schema: {schema_path}"); continue
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        for error in Draft202012Validator(schema).iter_errors(load_yaml(path)):
            errors.append(f"{path}: {error.message}")
    if not errors:
        domain = load_yaml(root / "domains/tiny_edge_ai/company_domain_taxonomy.yaml")
        needs = {x["engineering_need_id"] for x in load_yaml(root / "domains/tiny_edge_ai/engineering_need_taxonomy.yaml")["engineering_needs"]}
        items = {x["dspace_portfolio_item_id"] for x in load_yaml(root / "dspace_portfolio/dspace_portfolio_profiles.yaml")["dspace_portfolio_items"]}
        terms = {x["term_id"] for x in domain["terms"]}
        for rule in load_yaml(root / "dspace_portfolio/applicability_mapping_rules.yaml")["mapping_rules"]:
            for value in rule["target_company_side"]["required_entity_ids"]:
                if value not in terms: errors.append(f"unknown target entity {value}")
            for value in rule["neutral_need_side"]["engineering_need_ids"]:
                if value not in needs: errors.append(f"unknown need {value}")
            if rule["dspace_side"]["dspace_portfolio_item_id"] not in items: errors.append("unknown dSPACE portfolio item")
            if rule["dspace_side"]["dspace_portfolio_item_id"] != "neural_net_coder":
                errors.append("all NNC applicability rules must terminate at neural_net_coder")
    return errors
