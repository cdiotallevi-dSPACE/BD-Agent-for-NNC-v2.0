# Data dictionary

- `target_company_entity_id`: normalized investigated-company entity.
- `engineering_need_id`: neutral simulation/test/validation need.
- `dspace_capability_id`: supported capability from an authoritative portfolio profile.
- `dspace_portfolio_item_id`: unambiguous dSPACE offering identifier.
- `evidence_status`: `confirmed`, `inferred`, `unknown`, or `contradicted`.
- `assessment`: `accepted`, `rejected`, or `ambiguous`.
- `applicability_mapping`: entity → need → capability → portfolio item trace.
# Version 1.2 attribution and locality fields

## Candidate source

- `scan_target_company_id`: company whose scan discovered the candidate.
- `attributed_company_id`: initially null; populated only after source identity
  is established.
- `company_attribution_status`: `unverified`, `established`,
  `not_established`, `review_required`, or `contradicted`.

## Company attribution artifact

- `source_attribution_scope`: `target_company` or
  `general_industry_background`.
- `identity_anchors`: deterministic source/domain anchors used for attribution.
- `reason_codes`: deterministic attribution exclusions.
- `mapping_eligible`, `score_contribution`, `relevant_evidence_eligible`:
  downstream hard-gate decisions.

## Evidence and context bundles

- `context_bundle_ids`: locally coherent technical contexts supporting evidence.
- `context_bundle_gate_status`: `pass` only when neural model, constrained
  embedded target, and deployment workflow occur locally.
- `mapping_eligibility`: eligibility flag and deterministic reason codes.
- `background_technology_evidence`: technically relevant matches from sources
  that failed target-company attribution; never target-company facts.

