# Code-to-document alignment review — 4 September 2026

Scope: production application at `C:\Users\ClaudioD\Desktop\BDA for NNC v2.0`
and the seven proposals in `doc_mismatches_and_modifications_report.md`.

| # | Proposal | Decision | Applied treatment |
| --- | --- | --- | --- |
| 1 | Replace legacy power-electronics domain layers | Accepted with correction | Replaced them with the eight values actually present in `company_domain_taxonomy.yaml`. Also changed the schema from the obsolete `minItems: 9` assumption to `minItems: 1` plus uniqueness; the original proposal alone would have made validation fail. The file is an inventory, not a runtime classifier. |
| 2 | Deprecate `use_case_taxonomy.yaml` | Accepted with correction | Marked it `status: deprecated`, not merely with a comment while leaving `status: active`. Updated its schema to admit the truthful status. `shared_use_case_taxonomy.yaml` v1.12.0 remains runtime-authoritative. |
| 3 | Deprecate domain-local `search_profiles.yaml` | Accepted | Added an explicit non-runtime/deprecation notice. Runtime profiles are loaded from `config/search_providers.yaml`. |
| 4 | Document declarative YAML versus hardcoded Python | Accepted | Added an explicit file/status table. The listed YAML files are validated inventory/reference files; actual attribution, exclusions and query generation are in Python. |
| 5 | Expand `scoring_rules.yaml` | Accepted with extension | Mirrored all three point dictionaries from `nnc_scoring.py` and added the newer edge-only score-ineligibility rule. Python remains runtime-authoritative. |
| 6 | Publish exact relevance-band keys | Accepted | Added all five machine identifiers and their display meanings. |
| 7 | Explain `REQUIRED_ORDER` omission | Accepted as implementation clarification | Documented that rendered Markdown/PDF has seven sections while the unused tuple is a six-title primary-section marker. No report behavior was changed. |
| 8 | CLI section already accurate | Validated | No modification required beyond retaining the existing implementation-accurate command list and limitations. |

Additional findings applied beyond the report:

- The proposed eight-layer replacement conflicted with the old layer schema;
  both had to be reconciled together.
- A deprecation comment paired with `status: active` would remain misleading;
  the status and schema were corrected together.
- The scoring mirror also lacked the implemented rule that edge adjacency alone
  cannot create Product Fit when both neural and workflow signals are zero.

Validation required after these changes:

1. `bda validate-config` must report no schema/configuration errors.
2. Unit tests must remain green because no runtime behavior is intentionally changed.
3. The production and maintained repository copies of every changed file must
   have identical SHA-256 hashes after deployment.
