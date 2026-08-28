# BD Agent for Neural Net Coder

## Current Implementation Specification and Architecture Reference

| Identifier | Current value |
| --- | --- |
| Repository | `BD-Agent-for-NNC-v2.0` |
| Application directory | `C:\Users\ClaudioD\Desktop\BDA for NNC v2.0` |
| Python distribution | `bd-agent-for-nnc-v2` |
| Import package | `bd_agent_neural_net_coder` |
| application_version | `2.0.0` |
| specification_version | `1.10` |
| design_document_version | `1.10.0` |
| Documentation reconciliation date | `2026-08-28` |
| Domain | `tiny_edge_ai` |
| Terminal portfolio item | `neural_net_coder` — Neural Net Coder, from dSPACE |
| Product alias | ONNX-2-Target |
| Registry | `data/Companies.xlsx`, worksheet `Companies` |

This document describes the implemented v2.0 behavior. It is not a requirement
to implement currently absent capabilities. Future improvements must be labeled
as planned rather than implemented.

This revision reconciles the previous historical design with the Python source
and configuration present on the reconciliation date. It consolidates the old
v1.0–v1.2 requirements and later historical appendices instead of retaining
contradictory requirements alongside the current behavior. The runtime version
values above come from `pipeline.py`; the application version also appears in
`__init__.py` and `pyproject.toml`. Individual YAML/schema version numbers may
differ; they are not the application or run-manifest version.

The repository name is not the Desktop directory name. Relative paths below
refer to the application directory unless explicitly identified otherwise.
This documentation update changes no application code, configuration, scoring
weights, credentials, workbooks, or search budgets. It does not establish that
all historical design requirements have been implemented.

## 1. Purpose and semantic boundaries

BDA discovers public company engineering activity, attributes retrieved material
to the company, extracts deterministic evidence, assesses potential Neural Net
Coder fit, and produces auditable JSON, Markdown, PDF and workbook results.
Public patents, engineering publications, official company pages and PDFs are
discovery channels, not automatic proof of applicability or production adoption.

The three semantic scopes remain distinct:

- `target_company`: attributable company facts and evidence.
- `neutral_engineering_need`: inferred engineering needs tied to those facts.
- `dspace_portfolio`: authoritative dSPACE capabilities and retrieved grounding.

`core.validate_scope_names()` rejects its explicit list of prohibited generic
cross-scope keys. Existing scoped assessment fields and report labels retain
their actual schemas; this is not a blanket prohibition on every string that
contains `product`.

Generic AI/ML does not pass the neural-network gate by itself. Neural methods,
physical applications, deployment and workflow must not be fabricated from
unrelated keywords. The v1.10 scoring path nevertheless permits nonzero
opportunity scores below the threshold for an NNC mapping. Missing ONNX or
code-generation disclosure is not by itself a zero-score or rejection rule.
NNC is a potential solution, not an assertion that the company already uses it.

Positive NNC applicability mappings terminate at `neural_net_coder` and require
selected authoritative portfolio chunks. Opportunity evidence without an NNC
mapping is a separate publication path. The LLM does not determine evidence
acceptance, scores, mappings, or workbook results.

## 2. Technology stack and actual package layout

Python 3.11 or later is declared in `pyproject.toml`. Runtime dependencies
include Typer, HTTPX, DDGS, BeautifulSoup, ChromaDB, PyMuPDF, pypdf, openpyxl,
ReportLab, PyYAML, jsonschema, pydantic, python-dotenv and the Ollama package.
The model endpoint integration also uses direct HTTPX calls.

LlamaIndex is not used by the current v2.0 implementation. `llama-index>=0.11`
remains an optional, unused **`vector` extra**, not the `dev` extra. Its presence
in an environment does not imply LlamaIndex orchestration is implemented.

The production package is flat:

```text
src/bd_agent_neural_net_coder/
  __init__.py, __main__.py
  cli.py, pipeline.py, core.py, models.py, config_manager.py
  search_orchestrator.py, search_models.py, shared_use_case_taxonomy.py
  patent_native_discovery.py, patent_retest.py
  company_attribution.py, evidence_context.py, nnc_domain.py, nnc_scoring.py
  portfolio_index.py, relevant_evidence_builder.py, report_generator.py
  llm_context_builder.py, prompt_loader.py, llm_response_validator.py
  narrative_ownership_validator.py, ownership_contract_builder.py
  model_runtime.py, credential_manager.py, workbook.py
  provider_registry.py, provider_quota_ledger.py, provider_cycle_state.py
  execution_resources.py, audit_journal.py
  ddgs_provider.py, brave_provider.py, serpapi_provider.py, serper_provider.py
  github_provider.py, semantic_scholar_provider.py, patent_provider.py
  sitemap_provider.py, internal_crawler_provider.py, pdf_link_provider.py
```

Query generation and routing live in `search_orchestrator.py`; retrieval lives
in `pipeline.py`; portfolio retrieval/validation live in `portfolio_index.py`;
mapping and grounding enforcement span the latter two modules. There is no
separate run-context, generic document-cache, portfolio-grounding-gate,
async-retriever or search-provider subpackage in this implementation.

Root-level `Run-BDA.cmd`, `Run-BDA-Fast.cmd` and `verify_cycle_launch.py` implement
the launch/verification path. They are not Python package modules.

## 3. Configuration and identity inputs

The active domain directory is `config/domains/tiny_edge_ai/`. It contains:

```text
company_domain_taxonomy.yaml       company_domain_layers.yaml
company_identity_rules.yaml        company_alias_policy.yaml
engineering_need_taxonomy.yaml     hardware_target_taxonomy.yaml
model_and_framework_taxonomy.yaml  query_templates.yaml
search_profiles.yaml              shared_use_case_taxonomy.yaml
use_case_taxonomy.yaml             scoring_rules.yaml
page_relevance.yaml               exclusions.yaml
schemas/
```

Other configuration lives in `config/search_providers.yaml`, `config/runtime/`
and `config/dspace_portfolio/`. Runtime files include `models.yaml`,
`company_registry.yaml`, `hardware_profiles.yaml` and `model_benchmarks.yaml`.
Portfolio files include profiles, aliases, index configuration and
`applicability_mapping_rules.yaml`. Prompt assets live under `prompts/` and are
loaded through `prompt_loader.py` with an effective-prompt manifest.

Configuration files are not proof that every described feature is implemented.
Some query templates, classification heuristics, score levels, retrieval
thresholds and provider behavior are also encoded in Python. In particular,
`generate_queries()`, `nnc_scoring.py` and `portfolio_index.retrieve()` must be
consulted before claiming a YAML-only change affects runtime behavior.

`shared_use_case_taxonomy.py` supplies shared engineering vocabulary to web,
PDF/publication and patent discovery and local matching. Core discovery terms
are bounded by profile; extended terms support local matching. Company names,
domains and identities are substituted at runtime. Matching an application term
raises discovery priority; it is not automatic evidence approval.

Optional `data/company_source_profiles/<slug>.yaml` files can supply domains,
aliases, publication hubs, industry and seeds. They cannot silently supply
validated patent assignees: `load_company_profile()` discards that legacy YAML
field and resolves validated identities from the runtime input.

For registry cycles, column P supplies those operator-validated identities.
They are persisted in `source_assignee_registry.json` and the patent assignee
registry. They are not independently certified corporate relationships by BDA.
Without them native discovery is `degraded_no_validated_assignee`, not proof
that the company has no relevant patents.

Current limitation: the registry reads `industry`, but `scan-registry` does not
pass that value into `Pipeline.run()`. The search profile's industry defaults
to `unknown` unless supplied by its profile. Do not promise that editing the
workbook industry alone changes industry-specific query families.

## 4. Companies.xlsx contract

Headers are stripped of surrounding whitespace, then matched by their actual
names. All listed headers are required. Columns C and H–P are explicitly
position-validated; the other input fields are accessed by header.

| Layout | Header | Behavior |
| --- | --- | --- |
| A | `company_id` | Stable row identity for update verification |
| B | `company_name` | Company name and run identity |
| C | `Other_names` | Comma-separated aliases; trim and case-insensitive deduplication |
| D | `company_domain` | Bare domain or URL accepted; normalized to hostname |
| E | `country` | Report context |
| F | `industry` | Read in snapshot; see profile propagation limitation above |
| G | `notes` | Registry context |
| H | `Scan Y/N` | Trimmed, uppercased `Y` selects a row |
| I | `Overall Product Match` | Blank, whitespace or numeric 0–100; overwritten after assessment |
| J | `Total Retrieved Sources` | Per-company cycle result |
| K | `Total Retrieved and approved Sources` | Per-company cycle result |
| L | `total retrieved PDFs` | Per-company cycle result |
| M | `total retrieved and approved PDFs` | Per-company cycle result |
| N | `total retrieved Patents` | Per-company cycle result |
| O | `total retrieved and approved patents` | Per-company cycle result |
| P | `Validated Source assignees` | Operator-approved source identities |

Column P prefers semicolon separators; if no semicolon is present, commas are
used. Names are trimmed and deduplicated case-insensitively. Use semicolons
when an individual legal name contains a comma. Aliases and validated assignees
are different inputs: a short discovery alias does not confer attribution.

The cycle snapshots selected rows. Before writing, `workbook.update_rating()`
checks company ID/name and original score/count cells to avoid overwriting
concurrent changes. It creates a cycle backup, saves via a temporary workbook,
checks readability and replaces the workbook. Failure queues a pending update
in the batch directory; it does not erase the deterministic assessment.

`calculate_cycle_source_counts()` defines retrieved sources using successful
parse/retrieval status and a content hash. Approved means represented in Relevant
Evidence. PDF and patent counts overlap where applicable; they are not disjoint
categories. Patent counting recognizes publication metadata and patent domains,
not only a source-domain label, and deduplicates by publication number or URL.

## 5. Standard company-cycle execution

```text
Registry validation and selected-row snapshot
  -> portfolio index preflight
  -> native patent discovery + supplemental web queries + site/PDF discovery
  -> deterministic candidate ranking and budget selection
  -> bounded retrieval and PDF parsing
  -> company attribution, evidence extraction and context assessment
  -> deterministic scoring and Chroma-grounded applicability mappings
  -> Relevant Evidence, use-case consolidation and source counts
  -> deterministic JSON persistence and workbook callback
  -> optional protected summary attempt or deterministic fallback
  -> Markdown/PDF rendering, company manifest and cycle summary
```

Companies in a registry cycle run sequentially. Native patent enumeration runs
before the ordinary provider-query loop inside `discover()`. Sitemap, internal
crawler, publication hub and PDF-link discovery follow that loop. Prioritizing
official-company sources for retrieval does not mean they execute first.

`execution_status`, `quality_status`, degradation flags and workbook status are
separate. A completed run can have degraded provider coverage or LLM fallback.
The workbook callback runs after deterministic JSON persistence and **before**
the optional narrative/PDF stages; a later failure can leave updated workbook
cells and partial artifacts. The overall cycle records that outcome.

## 6. Discovery, patents and coverage

### 6.1 General sources

DDGS performs general web, official-domain, application-led, PDF/publication and
supplemental patent searches; it is not a patent-only provider. Other adapters
include Brave, SerpAPI, Serper, Semantic Scholar and GitHub. Their execution is
conditional on configuration, credentials, query budgets and cycle state.

Fallback chains are conditional on usable results for designated query families.
Other queries may target several providers independently. Configured mandatory
queries can still be skipped or fail because of budgets, unavailable credentials,
rate limits or provider failure. Audit records describe actual coverage; neither
a generated query nor a nonempty provider response proves useful retrieval.

Candidate ranking favors official-company sources, and patent selection favors
official USPTO records over Google-hosted alternatives. Explicit valid seeds
have their own protection/cap policy. URL normalization removes fragments and
tracking parameters and canonicalizes hosts. Native publication metadata is
merged with matching web candidates so established assignee context can follow
the source into attribution.

### 6.2 Patent-native implementation

`PatentNativeDiscovery.run()` resolves validated assignees, runs USPTO enumeration
and taxonomy queries, Google Patents enumeration and term queries, then Justia.
USPTO uses the Patent File Wrapper search endpoint, normalized application/
publication identifiers and metadata/full-text locations. The API key is loaded
locally and sent to the API; credentials are not report content.

Records are quality-checked, normalized/deduplicated, matched locally against
selected taxonomy terms, ranked, and selected with use-case reservations. Full
text is retrieved through the pipeline. Failed selected slots can be backfilled
from ranked unattempted patents, bounded by replacement-attempt limits.

Quality checks reject non-patent records and distinguish assignee/taxonomy signals
from raw result count. Search snippets remain discovery signals, not sufficient
standalone proof of company attribution or technical implementation.

Actual native request handling has an instance-level lock, minimum interval,
bounded retries for HTTP 429/500/502/503/504, and per-host open-circuit state.
This is not a universal throttle shared across all application modules.

The following are **not implemented as active discovery capabilities**:

- EPO OPS integration (a disabled configuration entry is not an adapter).
- Patent family/citation/continuation neighborhood crawling: the current
  `patent_family_expansion.json` records empty results and unavailable metadata.
- Automatic corporate-assignee validation when the workbook supplies none.

An outer enumeration `completed` flag is not evidence that every provider or
term succeeded. Inspect nested source outcomes, term coverage, quality records,
selection and full-text results. Exhaustive patent coverage is not guaranteed.

## 7. Retrieval budgets, PDF handling and cache

Current checked-in settings are shown below. Runtime configuration/profile
merging remains the operational source; this table is a dated snapshot.

| Control | Standard | fast_iteration |
| --- | ---: | ---: |
| DDGS maximum queries | 120 | 80 |
| DDGS results/query | 10 | 6 |
| Retrieval maximum_total_urls | 80 | 30 |
| Non-seed retrieved-document cap | 60 | 30 |
| PDF documents | 20 | 6 |
| Pages per PDF | 50 | 25 |
| Total parsed PDF pages per `_retrieve()` call | 500 | 150 |
| Download concurrency | 6 | 6 |
| PDF-link pages inspected | 200 | 60 |
| PDF links discovered | 15 | 6 |
| Native full-patent selection maximum | 80 | 12 |
| Replacement patent attempts maximum | 80 | 12 |
| General candidate patent-selection cap | 20 | 12 |

These are different stage budgets, not interchangeable promises of actual
downloads. Native selection, general candidate selection and retrieval can
further limit one another. Replacement `_retrieve()` invocations initialize
their own PDF counters; a single global cross-invocation PDF budget is not
implemented. A downloaded payload over `max_download_bytes` is rejected after
receipt; this is not a streaming network-byte cap.

PDF-link discovery bounds inspected pages, uses bounded concurrency, reports
progress, recognizes XML content, and prioritizes official/professional pages.
It stops scheduling further discovery when its PDF-link budget is met; already
in-flight work is bounded. This budget differs from PDF **parsed-page** limits.
The XML path uses BeautifulSoup's `xml` parser, which requires an available XML
backend such as lxml. lxml is not explicitly listed in the current base
dependencies; a missing backend is caught as a page-inspection failure. This
dependency gap should not be mistaken for successful XML coverage.

When the parsed-page budget reaches zero, remaining retrieved PDFs receive
budget-exclusion status; no more pages in that retrieval call are extracted.
HTML processing and subsequent deterministic assessment continue. Lack of text
is not proof of irrelevance. Image-only text extraction can produce
`ocr_required`; automatic OCR is not implemented.

Company evidence is extracted and classified deterministically. `bge-large` is
currently used for dSPACE portfolio indexing and portfolio retrieval, not for
embedding/searching company evidence.

The implemented persistent response cache is patent-native JSON/text HTTP data
under `data/cache/patent_native_http/`. Its key uses response kind and URL hash;
the wrapper records URL, cached_at and payload. The default relative path resolves
against the process working directory (launchers use the application directory).
The current reader does not enforce TTL or parser-version invalidation.
General HTML, PDF, parsed-passage, sitemap and search-result caches are not
implemented. Broader cache architecture is planned, not a current requirement.

## 8. Attribution and technical evidence

`company_attribution.py` distinguishes `scan_target_company_id` from
`attributed_company_id`. Discovery provenance is not source ownership. Attribution
can use official/approved domains, explicit company identities, approved source
assignees and recognized corporate affiliation evidence. Ambiguous short aliases
such as GM do not independently establish third-party identity. Personal initials
and bibliography-only collisions are rejected as company anchors.

Unattributed useful technical content can be background evidence but is excluded
from target-company scoring/mappings. `evidence_context.py` performs deterministic
technical extraction, opportunity/patent analysis, locality and semantic checks.
Quantization used for ordinary signal encoding is not neural quantization; an
ECU mention in a manual is not neural deployment. Related model, target and
workflow evidence must concern the same engineering context, not unrelated
company-wide keywords.

There are two relevant-evidence routes:

- Accepted mapping/applicability evidence with required eligibility/context
  checks and company attribution.
- Accepted `nnc_opportunity_evidence` with its opportunity gate; an actual NNC
  mapping is not required for this route.

`relevant_evidence_builder.py` also permits accepted applicability-class evidence
that meets its checks without requiring every item to be used by a published
mapping. Thus the old universal `used_by_published_mapping` requirement is not
an accurate description of the current publication predicate.

Not every Relevant Evidence record has a numeric score. Records with
`nnc_use_case_scoring` expose their use-case score; unscored opportunity records
can contribute zero and legacy mapping records can expose `eligible`. Relevant
Evidence is source-grouped; evidence records, sources, use cases and mappings
are different counts.

## 9. Product-fit scoring and mappings

The v1.10 scorer in `nnc_scoring.py` uses cumulative neural-application, edge and
workflow points, capped at 100. It does not sum every source's score.

| Component | Declared classifications and points |
| --- | --- |
| Neural application | Actually used estimator 55; operational embodiment 50; explicitly claimed estimator 45; connected optional method 35; generic ML estimator 20; indirect physical estimator candidate 15; generic NN mention 5; absent 0 |
| Edge | Deployed MCU/ECU/SoC 25; selected target 22; explicit controller implementation 18; real-time onboard 15; implementable controller 10; physical adjacency 5; undisclosed 0 |
| Workflow | ONNX + generated code 20; ONNX + edge 17; generated C/C++ 15; ONNX adoption 12; confirmed compatible handover/exportability 10; conversion/toolchain 8; likely-exportable framework 5; undisclosed 0 |

These are declared level dictionaries, not a claim that every level is selected
by the present classifier. For example, `score_patent_use_case()` currently
selects operational embodiment at 50 rather than the 55 level, and its edge
branches top out at 18. `_workflow_level()` does not currently emit the
10-point confirmed-exportability level. Heuristics and exact conditions in
those functions, not illustrative prose, determine the result.

Mapping class selection in this scorer is:

- neural >=45, edge >=15, workflow >=12: `nnc_maximum_workflow_fit`;
- neural >=45, edge >=15: `nnc_deployment_fit`;
- neural >=45: `nnc_influence_opportunity`;
- otherwise no scoring-derived NNC mapping class.

The label `nnc_maximum_workflow_fit` is not a claim that the score is 100.
Portfolio grounding remains a separate condition for published positive
mappings. Generic ML or a sensorless physical estimator can score below mapping
threshold without being represented as confirmed neural adoption.

`aggregate_company_scores()` groups scored accepted evidence by use-case class,
ignores source-ID-like case names, favors specific classes over the generic
indirect-sensing umbrella, and assigns a multi-class item to its alphabetically
first remaining class. It retains the best score per group and up to three
ranked supporting source IDs.

```text
base = highest distinct use-case score
breadth = 10 if at least two use cases score >=40, else 0
        + 5 if at least three use cases score >=40, else 0
company score = min(100, base + breadth)
```

Bands are >=85 maximum potential fit, >=65 high, >=40 medium, >=20 emerging ML,
otherwise low. This measures potential fit, not a probability of purchase or
proof of NNC/ONNX adoption. Readiness and commercial-toolchain status are reported
separately; edge/workflow points still form part of technical fit.

If no scored use cases exist, `pipeline.py` retains the legacy
`score_nnc_applicability()` fallback: neural 30, target 25, workflow 20,
constraints up to 15 and evidence quality up to 10, with role/cloud/neural caps.
If Relevant Evidence is empty, the final score is explicitly reset to zero,
display use cases are cleared and no report mappings are published. Intermediate
score-component diagnostics can still reflect the pre-reset calculation.

Mappings are created from configured applicability rules and portfolio retrieval
then consolidated to at most three use-case-level report mappings. The old
claim that edge + workflow disclosure is mandatory for every positive mapping
is superseded by the implemented influence-opportunity path.

## 10. ChromaDB portfolio ingestion and grounding

| Item | Implemented value |
| --- | --- |
| Collection name | `nnc_portfolio_documents` |
| Persistent directory | `data/dspace_portfolio_runtime/chroma_db` |
| Input PDF directory | `data/dspace_portfolio_documents/` |
| Embedding model/provider | `bge-large` / Ollama |
| Dimension / distance | 1024 / cosine |

The PDF directory name is deliberately unchanged: it is **not** the collection
identifier. The current implementation does not create or use a
`company_evidence_archive` collection. All collection names in collection
manifests and portfolio retrieval records are `nnc_portfolio_documents`.

`portfolio_index.ingest()` resolves document-to-item aliases, parses pages,
creates deterministic chunks/IDs, embeds chunks in batches of 16, upserts them,
handles unchanged/updated/removed documents and writes document/collection
manifests. It uses an ingestion lock. Preflight checks active documents,
collection metadata/dimension/count and sample chunk retrievability.

`retrieve()` embeds the query, filters Chroma by `dspace_portfolio_item_id`, and
records returned candidates, distances, similarity and selection. Its default
top_k is 8; the CLI default is 5. Current selection requires similarity >=0.35,
excludes `overview` chunks, and caps selections at two per page and three per
section. This is deterministic filtering of vector-search results, not an LLM
grounding decision.

`pipeline.py` checks selected portfolio chunks before publishing positive
applicability mappings. Index preflight/grounding failures are not silently
replaced by generic portfolio marketing text. Retrieval audit retains query,
collection, model, candidate chunk IDs and selection evidence.

## 11. Optional local summary and prompt contract

At most one **company-summary generation attempt** is made per company after
deterministic assessment. In the normal pipeline, no Relevant Evidence or no
scored use-case entries causes an early deterministic guard, without calling
Gemma:

```yaml
llm_summary_status: skipped_no_scored_evidence
llm_failure_code: no_scored_use_case_evidence
narrative_source: deterministic_template
llm_fallback_used: true
```

The `mandatory_attempt: true` configuration flag does not override this guard.
The implementation uses list presence, not a separate numeric-positive filter.
An optional prewarm request can precede generation when eligible; therefore
"at most one summary attempt" is not "at most one HTTP request to Ollama".
There is no second summary/revision request on failure.

Model: `gemma2:9b`; current configuration uses temperature 0.2, num_ctx 8192,
max output 1800 tokens, hard timeout 480 seconds and soft warning at 360 seconds.
The prompt fitter estimates tokens conservatively from characters; it is not
an exact tokenizer guarantee. It includes external prompt/schema overhead,
reserved output and safety allowance, and can reduce ranked use cases and
nonessential context. Context normally prioritizes three strongest use cases
and up to two sources per use case, with bounded portfolio excerpts.

`fit_complete_prompt()` executes inside the protected optional-summary path.
If fitting fails:

```yaml
llm_summary_status: skipped_prompt_budget
llm_failure_code: llm_prompt_budget_exceeded
narrative_source: deterministic_template
llm_fallback_used: true
```

Deterministic results remain available and report generation continues. Invalid
prompt bundles, runtime failures, invalid JSON/schema, truncation and substantive/
ownership validation failures also use deterministic fallback. Empty string list
items are normalized before schema validation; substantive grounding still must
pass. No information gaps should be encoded as `[""]`; use `[]`.

Narrative context distinguishes target-company facts from dSPACE-owned product
capabilities. The narrative should emphasize supported high-ranked use cases,
uncertainties and qualification actions, not infer customer ownership/adoption
from portfolio text. Raw response, runtime metadata, prompt/context metrics and
validation artifacts record the outcome. Acceptance by these deterministic
validators is not proof that an LLM can never make an unsupported statement.

## 12. Performance implementation and durability

| Mechanism | Actual scope and compatibility |
| --- | --- |
| `execution_resources.py` HTTP pool | Async clients scoped to an event loop; isolated by provider/settings and closed on scope exit |
| Ordered download workers | Same configured concurrency, bounded reorder window of twice concurrency, results consumed in original order |
| PDF budget allocation | Serial ranked-order parsing; completion timing does not allocate pages |
| Patent-only retrieval | Serial execution with existing 0.8-second pacing |
| Incremental PDF hashing | Historical hex-text SHA256 retained in `content_hash`; raw-byte SHA256 added as `raw_content_hash` |
| Explicit hash encoding | `content_hash_encoding: hex-text-sha256-v1` in PDF audit metadata |
| Bounded text joining | Equivalent to the old joined-text prefix without building the entire intermediate string; page text retained |
| Portfolio resource scope | Shared store, validation and sync HTTP client per company run; ingestion/manifest generation checks guard stale reuse |
| Portfolio query prefetch | Deduplicated embedding work in batches <=8; original ordered Chroma queries/filters retained; failed batches fall back to individual requests |
| Provider overlap | Only eligible independent non-metered Semantic Scholar work alongside DDGS for the same query; quotas reserved before scheduling and results merged in original order |

Fallback query chains are not speculatively parallelized. Native patent requests
retain their own pacing/retries. Sitemap, crawler and PDF-link providers use
operation-scoped clients. Universal shared per-domain semaphores and randomized
pacing are not implemented.

These changes preserve configured query span, ordering, quotas, retry policy,
selection rules and PDF budgets; they do not increase guaranteed provider recall.
Selected-chunk equivalence tests use deterministic mocked embeddings. Live model
numerical equivalence and elapsed-time speedup have not been established by
those tests and must not be presented as measured results.

`audit_journal.py` writes `discovery_events.jsonl`. Discovery events are appended,
flushed and fsynced per event. Compatibility snapshots `search_execution.json`,
`provider_results.json` and `search_queries.json` checkpoint after ten updates
or five seconds **on activity**, and finalize on normal or exceptional exit.
There is no background timer guaranteeing a snapshot during an idle request.

Hard termination may leave snapshots stale. `replay_journal()` reconstructs
committed update deltas and ignores only an incomplete final line. Independent
provider lifecycle/result events remain diagnostic events until ordered merging;
they are not all automatically converted into snapshot records by replay.
The journal is opened exclusively for a fresh discovery directory; automatic
resume of the same directory is not implemented. Other artifacts use their
existing persistence paths; not every application write is journaled or fsynced.

## 13. Output identity, files and reports

Three timestamps serve different purposes:

| Purpose | Example |
| --- | --- |
| Company run directory, local system time | `output/companies/general-motors/3 August 2026, 15-08-00 UTC+02-00/` |
| Run/artifact identity, compact UTC | `general-motors_20260803T130800Z_final_assessment.json` |
| PDF generation time, independently captured UTC | `General-Motors_Sales-Assessment_2026-08-03_13-12-20_UTC.pdf` |

`local_run_directory_timestamp()` uses system local timezone/locale, including
the actual offset; it is not hardcoded UTC+2 and may show a different winter
offset. Windows-safe hyphens replace time colons. PDF identity is generated by
`report_identity()` and uses sanitized company capitalization, not the lowercase
run slug. Cycle IDs/directories use `cycle_<compact-UTC>` and batch directories
use the compact UTC timestamp.

Main assessment artifacts have `<slug>_<timestamp>_` prefixes, including:

```text
company_sources.json             company_attribution.json
background_technology_evidence.json
context_bundles.json             evidence_records.json
company_assessment.json          relevant_evidence.json
retrieval_records.json           dspace_portfolio_assessment.json
applicability_mappings.json      final_assessment.json
llm_summary_context.json         effective_prompt_manifest.json
llm_response_metadata.json       narrative_validation.json
run_manifest.json               llm_raw_response.txt
```

The suffix list above must be combined with the prefix. For example:
`general-motors_20260803T130800Z_retrieval_records.json` and
`general-motors_20260803T130800Z_dspace_portfolio_assessment.json`.
Discovery also writes unprefixed working/audit files; prefixed final copies of
search queries, provider results, search execution and other discovery data are
written later by the pipeline. Not all files are prefixed.

Unprefixed patent/identity audits include:

```text
source_assignee_registry.json       patent_assignee_registry.json
patent_enumeration_manifest.json    patent_provider_quality.json
patent_metadata_corpus.jsonl        patent_term_coverage.json
patent_metadata_rankings.json       patent_family_expansion.json
patent_full_text_manifest.json      discovery_events.jsonl
```

Company manifests record runtime versions, status/quality, provider errors,
counts, score, LLM outcome and report filename. `output/run_registry.jsonl` is
the append-only run index. Cycle files include `cycle_snapshot.json`,
`cycle_manifest.json`, `cycle_summary.json`, `cycle_summary.md` and provider state.

The report section order is:

1. OVERALL ASSESSMENT.
2. Use-Case Product Fit: human-readable use case, up to three source IDs, score.
3. Search Coverage, including patent-search gaps.
4. Relevant Evidence: internal Source ID, evidence description, stable URL.
5. Applicability Mappings: use case, customer evidence/readiness, potential NNC capability.
6. Authoritative dSPACE Portfolio Sources.

Mapping display separates possible NNC capability from proven customer ONNX or
generated-code adoption. Source IDs are not use-case names. Relevant Evidence
descriptions use titles, patent publication identifiers and sentence-aware
abstract/passage summaries, preserving a complete long statement rather than
forcing a mid-sentence ellipsis.

Patent report links prefer stable USPTO application-detail URLs when an application
number exists, otherwise Google publication URLs. Signed retrieval URLs remain
transport/audit information, not durable report links. Missing patent identifiers
can cause a generic portal link; do not invent identifiers or titles.

## 14. CLI and launchers

Standard launch: `Run-BDA.cmd`. Fast launch: `Run-BDA-Fast.cmd`, selecting
`fast_iteration`. Both use `data/Companies.xlsx`. The fast profile deliberately
reduces scope via configuration; resource-reuse optimizations do not themselves
reduce whichever profile is selected.

The installed `bda` console entry point is `bd_agent_neural_net_coder.cli:app`.
Implemented commands and important interfaces are:

```text
validate-config
validate-models
validate-installation
validate-search-providers
validate-free-search-config
show-search-credentials
show-search-quota
reconcile-search-quota
test-search-provider --provider <id>
execute-query --provider <id> --query <text>
discover-company-sources --company <name> [--official-domain <domain>]
scan-company <company> --official-domain <domain> [--country <country>] [--seed-url <url>]
scan-registry [--workbook <path>] [--run-profile standard|fast_iteration]
batch [--workbook <path>]                         # deprecated alias
validate-registry [--workbook <path>]
list-registry-selection [--workbook <path>]
compare-runs <run_a> <run_b>
ingest-dspace-portfolio [--source <directory>] [--rebuild]
validate-portfolio-index
inspect-portfolio-index
retrieve-portfolio --query <text> --portfolio-item-id neural_net_coder [--top-k <n>]
test-patent-discovery --company <exact-selected-name> [--workbook <path>]
benchmark-models [--hardware-profile <name>]
```

`compare-runs` accepts directories containing prefixed final assessments and
prints score/mapping-count differences. It is not a full evidence-diff tool.
`test-patent-discovery` requires exactly one matching selected workbook company
and performs a patent-only retest, without ordinary web search, LLM or PDF report.
`benchmark-models` currently prints a validation-only profile message; it does
not measure latency/quality or benchmark alternative models.

`ingest-dspace-portfolio` also exposes an `incremental` parameter, but the wrapper
does not forward it; actual behavior is controlled by `rebuild` and ingestion's
unchanged-document handling. `reconcile-search-quota` reports the conservative
local ledger, not remote provider billing reconciliation. Some diagnostic
commands perform network requests or write diagnostics; they are not all offline.

Unavailable CLI capabilities include `inspect-cycle`, `inspect-search-run`,
`show-provider-cycle-state`, `export-tuning-dataset` and `rebuild-cache`. Their
names in older design examples do not make them executable commands.

`verify_cycle_launch.py` requires successful child exit, exactly one newly
generated cycle manifest with fresh timestamps, a completed status, a nonempty
selected-company set and complete company results. A unique receipt is then
checked by CMD. Old manifests cannot prove success. Degraded completion and
pending workbook updates produce warnings. Endpoint-security termination is not
circumvented by the launcher; it causes completion verification to fail.

## 15. Security, validation and proposed follow-up work

Credentials load from local `.env` without overriding supplied environment
variables. Keep credentials, company workbooks, private portfolio PDFs, cached
responses, signed transport URLs, indexes and run data out of source publication.
The current `.gitignore` should be reviewed for all runtime paths: in particular,
the broad `data/cache/` directory needs an explicit exclusion before indiscriminate
staging. This documentation change does not modify `.gitignore`.

Existing tests cover attribution false positives, opportunity/scoring rules,
workbook updates, prompts/reports, provider quotas, native discovery and execution
optimizations. `tests/unit/test_execution_optimization.py` checks mocked selected-
chunk equivalence, ranked PDF budgets, hashes, resource lifecycle, cancellation,
journal replay and limited provider overlap. The reviewed application passed
120 unit tests during the preceding publication verification; that is not proof
of a fresh live scan, a full integration-suite pass or guaranteed patent recall.

Acceptance of this documentation revision is a static code-to-document check:
identifiers/paths, CLI registration, score formulas, workbook positions, artifact
naming, LLM guards and explicit implementation-status labels must match source.
No absent capability becomes a software requirement merely by remaining in an
older design document elsewhere in `docs/`.

Proposed follow-up work, **not implemented by this revision**:

- Pass workbook industry into the runtime profile explicitly.
- Align declarative flags/score levels with the branches that actually consume them.
- Declare and validate the XML parser backend used by PDF-link discovery.
- Add TTL/parser-aware caching, cache hygiene and explicit cache exclusion policy.
- Implement real patent neighborhood expansion and EPO OPS only as separately scoped work.
- Consider one cross-retrieval-call budget if a strict whole-company page ceiling is desired.
- Add exact-token/live-model prompt and embedding equivalence checks plus measured timings.
- Add dedicated inspection/export CLIs, journal recovery tooling and crash-resume support.
- Tighten publication/scoring schema consistency and verify the distinction between accepted
  scored evidence and source-grouped published evidence across all edge cases.

## 16. Reconciliation record and implementation-status table

The 20 requested corrections have been incorporated by topic: identity/status/
versions (introduction), collection and grounding (10), module/configuration layout
(2–3), LlamaIndex/embeddings (2, 7), LLM condition (11), caching/concurrency/audits
(7, 12), timestamp and artifact names (13), workbook columns (4), CLI (14) and
the status table below. The input PDF directory was intentionally not renamed.
Additional corrections document current scoring/report behavior, source counters,
assignee inputs, launcher verification and known configuration/implementation gaps.

| Capability | Status | Actual implementation | Specification treatment |
| --- | --- | --- | --- |
| NNC semantic gates | Implemented | company_attribution.py, evidence_context.py, nnc_domain.py | Separate attribution, neural evidence, context and opportunity paths |
| ChromaDB portfolio grounding | Implemented | pipeline.py + portfolio_index.py | One `nnc_portfolio_documents` collection; positive mapping grounding required |
| General document cache | Not implemented | Patent-native response cache only | Planned, not current behavior |
| Company-evidence BGE retrieval | Not implemented | Deterministic company extraction/classification | No company vector-search claim |
| LlamaIndex orchestration | Not implemented | Unused optional `vector` extra | No implemented orchestration claim |
| Universal per-domain HTTP throttling | Partial/local controls only | Native lock/pacing and bounded workers | Universal shared controls remain planned |
| Exactly-one LLM call for empty evidence | Not implemented | Early no-scored-evidence guard | At most one summary attempt; eligible prewarm separate |
| Cycle inspection CLI | Not implemented | Manifests exist; no inspect-cycle command | Planned tooling |
| Scoped resource reuse | Implemented | execution_resources.py, portfolio_index.py | Per-loop/per-company lifetimes, not universal/global clients |
| Batched portfolio queries | Implemented | Prefetch <=8; original ordered Chroma queries | Mocked equivalence tested; live numerical check pending |
| Append-only discovery journal | Implemented | audit_journal.py | Fsynced events; periodic/final snapshots; limited replay |
| Provider concurrency | Limited | Eligible DDGS/Semantic Scholar overlap | Not broad parallel query execution |
| Native patent enumeration | Implemented, bounded | USPTO, Google Patents, Justia | Coverage can degrade; nested audits govern interpretation |
| EPO OPS | Not implemented | Disabled configuration entry only | Planned |
| Family/citation expansion | Placeholder audit only | Empty expansion records | Do not claim neighborhood discovery |
| Automatic assignee validation | Not implemented | Workbook/runtime operator-validated identities | Missing identities cause degraded native search |
| Workbook industry propagation | Partial | Snapshot field read; profile not passed that value | Explicit current limitation |
| Numeric score for every relevant source | Not universal | Scored and legacy/unscored records coexist | Use-case aggregation, not source-score summation |
| Actual benchmarking | Not implemented | benchmark-models message only | CLI is a stub, not performance evidence |
| Automatic OCR | Not implemented | ocr_required status | No OCR coverage claim |
| Verified launcher completion | Implemented | verify_cycle_launch.py + CMD receipt | Fresh completed nonempty cycle required |
