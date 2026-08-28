from __future__ import annotations


OWNER = "dSPACE GmbH"
RELATIONSHIP = "applicable_to_target_company_engineering_needs"


def enrich_ownership(final: dict, profiles: list[dict]) -> dict:
    by_id = {item["dspace_portfolio_item_id"]: item for item in profiles}
    recommended_ids = {
        mapping["dspace_portfolio_item_id"]
        for mapping in final.get("applicability_mappings", [])
    }
    for item_id in recommended_ids:
        profile = by_id.get(item_id)
        if not profile:
            raise ValueError(f"missing dSPACE portfolio profile: {item_id}")
        for field in ("commercial_name", "owner", "supplier", "offering_type", "aliases"):
            if not profile.get(field):
                raise ValueError(f"missing ownership metadata {field}: {item_id}")
        if profile["owner"] != OWNER or profile["supplier"] != OWNER:
            raise ValueError(f"owner/supplier metadata mismatch: {item_id}")

    for item in final["semantic_scopes"]["dspace_portfolio"]:
        if item.get("hard_rule_passed"):
            profile = by_id[item["dspace_portfolio_item_id"]]
            item.update({
                "dspace_commercial_name": profile["commercial_name"],
                "owner": profile["owner"],
                "supplier": profile["supplier"],
                "offering_type": profile["offering_type"],
                "aliases": list(profile["aliases"]),
                "relationship_to_target": RELATIONSHIP,
            })
    for mapping in final["applicability_mappings"]:
        profile = by_id[mapping["dspace_portfolio_item_id"]]
        mapping.update({
            "dspace_commercial_name": profile["commercial_name"],
            "owner": profile["owner"],
            "supplier": profile["supplier"],
            "dspace_offering_type": profile["offering_type"],
            "dspace_product_aliases": list(profile["aliases"]),
            "relationship_to_target": RELATIONSHIP,
        })
    final["target_company"] = {
        "name": final["company_name"],
        "role": "prospective_user_of_applicable_dspace_offerings",
    }
    final["portfolio_supplier"] = {
        "name": OWNER,
        "role": "owner_and_supplier_of_all_dspace_portfolio_items",
    }
    return final
