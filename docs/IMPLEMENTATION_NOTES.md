# Implementation Notes

## BDA for NNC v2.0

The application was derived from the separate, read-only
`BD-Agent-for-PwEl-v2.0` baseline. The original repository was not modified.

Implemented NNC changes:

- distribution `bd-agent-for-nnc-v2` and package `bd_agent_neural_net_coder`;
- active domain `tiny_edge_ai`;
- single terminal portfolio item `neural_net_coder`;
- Tiny-AI model, MCU/ECU target, deployment, optimization, verification, safety,
  role, use-case, hardware, and framework taxonomies;
- Python neural-network, embedded-target, deployment-workflow, company-role,
  cloud-only, partner, and competitor gates;
- NNC-specific score components and caps;
- NNC discovery queries and official PDF search;
- persistent ChromaDB collection `nnc_portfolio_documents`;
- Neural Net Coder ownership, attribution, and product-boundary prompt controls;
- design identifiers in final assessments and run manifests;
- NNC-specific unit tests.

The implementation retains the supplied PwEl v2.0 runtime architecture, which
corresponds to its included Version 1.17 implementation state. Requirements in
the NNC document that assume later PwEl v1.26 code are implemented where the
baseline exposes the relevant extension point. No unapproved Neural Net Coder
PDF was copied or fabricated. Production positive recommendations therefore
remain correctly blocked until approved NNC documents are placed in
`data/dspace_portfolio_documents` and ingested.
# Design 1.2.0 implementation (2026-08-03)

- Added a deterministic document-level target-company attribution gate before
  technical evidence extraction.
- Candidate provenance now stores `scan_target_company_id` separately from the
  initially null `attributed_company_id`; search execution no longer asserts a
  factual company relationship.
- Added company alias risk classes. Short acronyms such as `GM` remain valid
  low-priority discovery terms but cannot independently establish attribution.
- Added bibliography/personal-initial collision detection and the reason codes
  `target_company_not_established`, `ambiguous_company_alias_only`, and
  `bibliography_initials_alias_collision`.
- Added `general_industry_background` isolation. Technically relevant sources
  that fail attribution produce no target-company evidence, mappings, score, or
  Relevant Evidence and are excluded from company-specific LLM context.
- Added local context bundles requiring neural-model, embedded-target, and
  deployment-workflow evidence within one bounded document context.
- Added deterministic controls for signal quantization, generic vehicle/OBD
  manuals, and cross-document gate mixing.
- Tightened Relevant Evidence promotion to require established attribution,
  matching attributed/scan company IDs, accepted evidence, mapping eligibility,
  a passing context bundle, and use by a published mapping.
- Added the four mandatory General Motors false-positive regression contracts.
- Run manifests now identify specification `1.2` and design document `1.2.0`.
- No deviations from the v1.2 false-positive requirements are known in this
  implementation increment.

## Retrieval progress and page-budget hardening

- Added flushed stage messages for discovery, bounded retrieval, attribution,
  evidence/context extraction, mapping, LLM context, narrative, and reporting.
- Added periodic document/page counters during retrieval and evidence analysis.
- Enforced a deterministic maximum of 2,500 parsed PDF pages per company run,
  300 pages per PDF, and 50 parsed PDFs. Candidates beyond these limits remain
  auditable but receive explicit budget-exclusion/truncation statuses.
- Added manifest fields for available pages, parsed pages, skipped pages, and
  the effective run-level PDF page budget.
- Added regression tests for total-page, per-document, document-count, and
  progress-output behavior.
## Design v1.3.0 (2026-08-03)

- Added mandatory seedless `applied_ml_research` DDGS queries, including SAE Mobilus/SAE publication searches.
- Added generic distinctive-brand plus corporate-organizational-unit attribution; ambiguous acronyms such as `GM` remain insufficient.
- Added `nnc_opportunity_evidence` for concrete company ML applications with physical/embedded adjacency and maturity signals.
- Opportunity evidence is reportable but cannot create an NNC mapping and contributes zero product-fit score.
- Retained the v1.1/v1.2 local neural-model, embedded-target, and deployment-workflow gates unchanged.
- Added the `MAHINDRA-FN-SAE-ML-LOAD-CONDITION` regression contract.
## Design v1.5.0 (2026-08-04)

- Added generic `professional_applied_ml_publication` discovery and classification.
- Replaced mandatory publisher Boolean searches with independent atomic SAE queries using company variables.
- Added ordered DDGS/Brave/SerpAPI/Serper zero-result fallback for professional-publication queries.
- Added deterministic pre-retrieval scoring so professional applied-ML evidence outranks generic annual reports.
- Added indirect physical-state/virtual-sensing and battery-health discovery lexicons.
- Added seedless `MAHINDRA-FN-SAE-VEHICLE-LOADING-ML` regression coverage.
- Mapping gates and product-fit scoring remain unchanged; opportunity evidence contributes zero score.
## Design v1.6/v1.7 patent discovery and classification

- Added mandatory, application-led patent discovery with at least six independent queries, a 20% target/15% minimum reserved query share, and DDGS/Brave/SerpAPI/Serper zero-result fallback.
- Added generic validated patent-assignee identity anchors and a GM profile for `GM Global Technology Operations LLC`; ambiguous short aliases remain non-attribution anchors.
- Added industry baseline use-case ladders, application-only patent queries, bounded CPC sibling searches, and high patent retrieval priority.
- Added role-aware patent semantics for neural embodiments, regressors/classifiers, virtual measurements, estimators, learning agents, controllers, and onboard contexts.
- Patent opportunity evidence remains mapping-ineligible and contributes zero product-fit score unless the existing complete NNC mapping gates independently pass.
- Added seed-free regression coverage for `US12246700B2` and `US20240302440A1`.
- The separately referenced v1.6/v1.7 YAML patch artifacts were unavailable; the complete authoritative Markdown specifications were used directly.
## Design v1.8 patent-native discovery

- Patent discovery now starts from validated assignee identities and paginated Google Patents/Justia native metadata sources; general-web patent queries are supplemental.
- Added a separate 500-record assignee metadata corpus and 100-document full-text budget, deterministic local ranking, family-specific retrieval reservations, and required-term coverage for every v1.8 vehicle-dynamics and predictive-battery term.
- Added native assignee-plus-taxonomy searches to surface deep corpus records without using known publication numbers or URLs as production inputs.
- Patent-provider and supplemental fallback success is quality-based. Job advertisements, generic pages, missing identifiers, absent assignees, and taxonomy-free result sets do not terminate fallback.
- Added all eight required patent audit artifacts, bounded expansion-channel reporting, and post-retrieval full-text status updates.
- Native-provider requests use bounded eight-second timeouts and persist degraded capability status rather than leaving the terminal inactive during throttling.
- Added `GM-FN-PATENT-NATIVE-DUAL-DISCOVERY` coverage, including page-three discovery, dual-family selection, job-ad rejection, quality fallback, full term coverage, and seed/query oracle prohibition.
## Fast patent retest mode

- Added `bda test-patent-discovery --company <name>`, which uses the selected Companies.xlsx identity and runs only patent-native enumeration, complete term coverage, local ranking, reserved full-text retrieval, attribution, and relevance classification.
- The command skips general web discovery, sitemap/internal crawling, PDF-link discovery, portfolio grounding, Gemma narrative generation, workbook rating updates, and report rendering.
- Preserved the 500-record patent metadata corpus while reducing full patent retrieval to 40 with proportional family reservations.
- Reduced ordinary full-run limits to 60 non-seed documents, 20 PDFs, 50 pages per PDF, and 500 total parsed PDF pages; crawler and publication-discovery limits were reduced proportionally.
## Shared cross-channel NNC use-case taxonomy (2026-08-07)

- Added `shared_use_case_taxonomy.yaml` as the single versioned vocabulary for
  patent-native discovery, supplemental patent search, official-company web
  search, PDF/professional-publication discovery, local ranking, full-text
  assessment, human-readable use-case aggregation and deterministic scoring.
- Core terms are executed as bounded atomic queries. Extended synonyms are
  matched locally to avoid DDGS query explosion and rate limiting. CPC terms
  are patent-only metadata signals; context terms are assessment-only.
- Added generic validated-assignee neural queries and application-led families
  for electric-machine thermal estimation, combustion/powertrain neural
  control, autonomous-driving neural perception and battery state-of-power
  adaptation. No company or patent identifier is a production discovery seed.
- USPTO taxonomy quality now considers available abstract/keywords, native
  query provenance and CPC classifications instead of title-only matching.
- The same technical analyzer and v1.10 score are used for attributed HTML,
  PDF, professional-publication and patent evidence. Discovery remains
  separate from attribution and approval.
- Fast and standard patent reservations were rebalanced across the expanded
  application families. Regression oracles cover US12091027B2,
  US20260110742A1, US10788396B2 and US11594040B2 without querying by number.
- Tuned the three leading Stellantis pilot patterns generically: recurrent ANN
  virtual-temperature sensing, LSTM battery state-of-power inference with a
  separately qualified transfer-learning lifecycle, and compact feed-forward
  controller ANN calibration. Fixed trained inference, online updating,
  architecture size, sensor elimination and commercial recency are persisted
  independently. Older/ICE context never reduces technical Product Fit.
# v1.12 shared public-OEM application discovery

- Added public OEM application vocabulary for battery estimation, motor thermal management,
  perception, driver monitoring, diagnostics, software-defined vehicles, virtual sensing and
  AI-enabled vehicle control.
- Application-only web queries now complement neural/embedded solution vocabulary.
- Validated Source assignees from `Companies.xlsx` now drive general web and PDF/publication
  searches in addition to patent-native discovery.
- Fast runs execute bounded core terms; extended synonyms remain deterministic local matching
  and assessment vocabulary.
- Application-led queries are generated before supplemental patent-web queries so the latter
  cannot consume the complete DDGS allowance.
# 2026-08-28: launcher completion verification

Both launchers now invoke the unchanged scan-registry command through a stdlib
guard. A zero exit code alone is insufficient: exactly one new cycle manifest,
fresh start/end timestamps, completed execution, and complete nonempty company
results are required. A unique receipt is checked independently by CMD, so a
blocked verifier returning zero cannot report success. Degraded completion and
pending workbook updates are disclosed. Existing historical manifests cannot
satisfy the check. No endpoint-security configuration is changed. Concurrent
cycles are conservatively rejected when more than one fresh manifest appears.

## 2026-08-28: bounded execution resource reuse

- Reuse one portfolio store, index validation and synchronous HTTP client per
  company run. Check ingestion lock and manifest generation before reuse; fail
  closed if the index changes. No cross-company embedding cache is introduced.
- Embed distinct applicability queries in batches of at most eight; keep all
  original Chroma queries, filters, ranking and mapping order. Failed batches
  fall back to individual embedding requests. Duplicate embedding work alone
  is eliminated; scoring and evidence rules are unchanged.
- Pool asynchronous provider HTTP clients within an event-loop scope, isolated
  by provider and transport/auth settings, and close them on scope exit.
- Replace fixed download batches with bounded workers and a bounded reorder
  window (twice configured concurrency). Parse/allocate PDF budgets in original
  ranked order, never completion order. Preserve patent-only serial pacing.
- Hash PDF bytes incrementally. Preserve the historical hex-text SHA256 in
  content_hash for compatibility; add raw_content_hash and explicit encoding.
  Bound joined page-text intermediates and explicitly close parsed PDFs.
- discovery_events.jsonl is append-only and flushed/fsynced per event. The
  three existing discovery JSON snapshots checkpoint every ten updates or five
  seconds on activity, and finally on normal or exceptional exit. A hard kill
  can leave snapshots stale; replay_journal reconstructs committed deltas,
  ignoring only an incomplete final line. Independent-provider lifecycle/result
  events also remain available for diagnosis before ordered result merging.
- Conservative concurrency overlaps only eligible non-metered Semantic Scholar
  with DDGS for the same independent query. Reserve quota before scheduling;
  merge in original order. Fallback queries remain sequential and conditional.
  Native patent discovery and same-provider throttling remain unchanged.
- No search configuration, query span, scoring weights or source/page budgets
  are reduced. Tests cover selected-chunk equivalence with deterministic mock
  embeddings, resource lifetime, ranked PDF budgets, hash compatibility,
  cancellation, audit replay and provider fallback/quota behavior. Live model
  numerical equivalence and elapsed-time gains require a later authorized run;
  no live BDA scan is performed while endpoint-security investigation is open.
# 2026-08-31 — Compact narrative action contract

- Simplified `recommended_next_actions` to an array of non-empty action strings.
- Action priority is deterministic from array order: highest priority first.
- Updated prompt, schema, normalization, fallback output, and validation together.

# 2026-08-31 — Company Background Evidence report partition

- Relevant Evidence now contains only sources linked to a precise scored use case or an explicit applicability mapping.
- Accepted opportunity sources without that link are preserved under COMPANY BACKGROUND EVIDENCE immediately after Relevant Evidence.
- Background sources remain approved-source counts, but cannot affect Product Fit, mappings, or the LLM context.

# 2026-08-31 — Bidirectional use-case/evidence source invariant

- Edge adjacency alone now scores zero when both neural-application and deployment-workflow points are zero; explicit estimator-substitution candidates remain eligible through their neural-opportunity classification.
- Company aggregation consumes only sources already qualified for Relevant Evidence.
- Supporting Sources and Relevant Evidence must contain exactly the same source-ID set; report generation fails on either-direction mismatch.

# 2026-09-04 — Configuration and specification reconciliation

- Audited the seven proposals in `doc_mismatches_and_modifications_report.md` against the production code.
- Replaced the legacy power-electronics layer inventory with the eight layer values actually used by the Tiny/Edge-AI company taxonomy and corrected its schema cardinality.
- Marked the unreferenced v1.5 use-case taxonomy and domain-local search profiles as deprecated; runtime behavior remains in `shared_use_case_taxonomy.yaml` and `config/search_providers.yaml`.
- Mirrored the Python scoring level dictionaries and edge-only score exclusion in `scoring_rules.yaml` without moving runtime authority out of `nnc_scoring.py`.
- Documented exact relevance-band identifiers, declarative-only YAML roles, and the rendered report-order distinction.
- No search, scoring, attribution, evidence or report runtime behavior was changed by this documentation/configuration reconciliation.
