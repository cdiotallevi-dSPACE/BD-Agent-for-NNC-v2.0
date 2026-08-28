# BD Agent for Neural Net Coder

## Authoritative Implementation Specification for Codex

**Repository:** `BD-Agent-for-NNC-v2.0`  
**PyPI distribution:** `bd-agent-for-nnc-v2`  
**Application version:** `2.0.0`  
**Python import package:** `bd_agent_neural_net_coder`  
**Application directory:** `C:\Users\ClaudioD\Desktop\BD-Agent-for-NNC-v2.0`  
**Company registry workbook:** `data\Companies.xlsx`  
**Domain ID:** `tiny_edge_ai`  
**Terminal dSPACE portfolio item:** `Neural Net Coder`  
**Product alias:** `ONNX-2-Target`  
**Document status:** New-system implementation specification  
**Design document version:** `1.8.0`  
**Runtime compatibility tag:** `1.8`  
**Date:** `2026-08-04`

This document defines a new Business Development Agent for finding and assessing
companies that develop neural-network applications for low-power or
resource-constrained embedded targets. It intentionally mirrors the architecture,
controls, artifacts, evidence model, and operational behavior of the Power
Electronics BDA Version 1.26 while replacing the domain-specific taxonomy,
engineering needs, applicability rules, product grounding, prompts, and regression
fixtures with those required for Neural Net Coder.


## Version 1.1 false-positive correction

Version 1.1 tightens the evidence-locality, ambiguity, mapping, and report-promotion
contracts after two General Motors false positives:

1. an OBD diagnostic PDF in which `linear quantization` described signal-value
   encoding rather than neural-network weight or activation quantization; and
2. a vehicle owner's manual in which `ABS electronic control unit` established
   only the existence of an ordinary ECU, while unrelated GM documents supplied
   the neural-network and deployment terms.

The corrected design prohibits company-wide keyword aggregation from satisfying
an applicability mapping. A published NNC mapping now requires a traceable
**context bundle** in which neural-model, embedded-target, and model-deployment
evidence are locally related to the same technical application, project, system,
or named model. Generic manuals may remain searchable candidate sources, but
they SHALL not become mapping evidence or `Relevant Evidence` unless they contain
explicit, locally connected neural-model deployment evidence.


## Version 1.2 company-attribution correction

Version 1.2 adds a mandatory **target-company identity and attribution gate**
after a third General Motors false positive. A technically relevant TinyML paper,
`TinyML for Small Microcontrollers`, was returned by the query `"GM" neural
network microcontroller`. The paper discusses EmbedIA, TensorFlow Lite Micro,
CMSIS-NN, neural networks, constrained MCUs, memory, and inference, but the
research belongs to Universidad Nacional de La Plata and does not establish any
relationship to General Motors. The string `G.M.` occurs only as personal
initials in a bibliography editor name and SHALL NOT satisfy the `GM` company
alias.

The corrected design therefore distinguishes **search-target provenance** from
**source-to-company attribution**. A search result discovered while scanning a
company is only a candidate for that scan; it SHALL NOT automatically become
`target_company` evidence. Before technical evidence extraction, every retrieved
document SHALL pass a deterministic company-identity gate based on a strong
company anchor, an official/approved domain, or an explicit documented
relationship.

Short or ambiguous aliases such as `GM` are discovery hints by default. They MAY
be used to generate search queries, but they SHALL NOT independently establish
company identity in a third-party source. Punctuation variants, author initials,
bibliography entries, citation lists, and provider query matching SHALL not be
used as company-attribution evidence.

A technically useful source that fails this gate MAY be retained separately as
`general_industry_background`, but it SHALL contribute zero target-company
applicability points, SHALL support no target-company mapping, SHALL not enter
`Relevant Evidence`, and SHALL not be represented to the Local LLM as a fact
about the scanned company.


## Version 1.3 opportunity-evidence and academic-discovery correction

Version 1.3 corrects a false negative found during the Mahindra & Mahindra scan.
The SAE technical paper `2019-26-0019`, authored by researchers affiliated with
Mahindra Research Valley, describes a supervised machine-learning model for
real-time vehicle loading-condition recognition using vehicle-driving and
telematics data. The public abstract does not disclose a neural-network
architecture, execution on an MCU/ECU, ONNX, generated C/C++ code, or constrained
target resource requirements. Under Version 1.2, this meant that the paper could
be accepted as a company fact but could not enter `Relevant Evidence` because
`Relevant Evidence` was incorrectly restricted to mapping-eligible evidence.

Version 1.3 separates **company-specific NNC opportunity evidence** from
**mapping-supporting NNC applicability evidence**. A source MAY now be published
in `Relevant Evidence` when it establishes a genuine target-company ML project
that is technically adjacent to NNC's deployment domain, even when the public
source does not yet prove a neural model or embedded execution target. Such
evidence SHALL be labeled `nnc_opportunity_evidence`, SHALL contribute zero
deterministic NNC product-fit points, and SHALL NOT satisfy an applicability
mapping until the neural-model, embedded-target, and deployment-workflow gates
pass.

The change also broadens discovery beyond neural-network-specific vocabulary.
Every company scan SHALL execute academic/applied-ML query families using
`machine learning`, `supervised learning`, `data-driven`, vehicle/system
applications, technical-paper terms, SAE Mobilus, and DOI-oriented search. The
BDA SHALL NOT depend on Semantic Scholar alone for academic discovery.

Author affiliations such as `Mahindra Research Valley` SHALL be resolved through
a generic corporate-organizational-unit rule. A publisher-supplied affiliation
that contains a distinctive target-company brand token plus an R&D/engineering
organizational-unit pattern MAY establish company attribution; ambiguous brand
tokens require independent corroboration from an official target-company source.
This rule is company-independent and is not a Mahindra-specific hard-coded alias.

The Mahindra SAE regression test SHALL pass without an explicit seed URL. The
acceptance test SHALL fail if success depends on a company-specific seed.


## Version 1.4 use-case-led discovery and retrieval-priority correction

Version 1.4 corrects a second Mahindra false negative: the MathWorks/MATLAB EXPO
presentation `Intelligent System for Battery Health Monitoring` is strongly
relevant to NNC opportunity discovery, but it was not discovered at all. The
source identifies Mahindra Research Valley and Mahindra & Mahindra, describes
battery state-of-health prediction, and uses an adaptive neuro-fuzzy classifier
whose adaptive parameters are trained with a neural-network mechanism. The title
and high-level metadata are application-led (`battery health monitoring`, `SOH`,
`prognostics`) rather than NNC-led (`ONNX`, `MCU`, `code generation`).

The failure demonstrates that company scans SHALL NOT rely primarily on
product-vocabulary queries. Search must cover the *customer application
vocabulary* even when a title or search snippet does not disclose the model
architecture or deployment target.

Version 1.4 therefore adds a mandatory **use-case-led discovery layer** generated
from the NNC use-case taxonomy. For each company, the BDA SHALL select the most
relevant use-case families for the company's industry and execute a deterministic
query ladder containing:

1. company + use-case terms without a model constraint;
2. company + use-case + broad ML/neural terms;
3. company + use-case + engineering-publication terms;
4. company + use-case on approved technical-publisher domains.

The use-case-only rung is mandatory because technically valuable publications
often use titles such as `Battery Health Monitoring`, `State Estimation`,
`Virtual Sensor`, `Remaining Useful Life`, or `Condition Monitoring` without
mentioning `neural network`, `TinyML`, `ONNX`, or `MCU` in the title.

Candidate ranking is also changed. A candidate containing a strong target-company
identity signal plus a high-value NNC use-case signal on a primary technical
publisher SHALL receive retrieval priority even if the provider snippet lacks an
explicit neural-network term. Neural/model terms increase priority but are not a
precondition for retrieval.

The design adds technical-publisher profiles for engineering ecosystems such as
MathWorks and SAE. These profiles are discovery aids only. A MathWorks, SAE, IEEE,
university, or partner-hosted source SHALL still pass the Version 1.2
target-company attribution gate after retrieval.

The Mahindra Battery Health Monitoring regression fixture SHALL pass without an
explicit seed URL. The acceptance test SHALL fail if discovery depends on a
company-specific seed.

## Version 1.5 professional-publication discovery correction

Version 1.5 corrects a false negative in professional technical-publication
discovery. The SAE paper `Methodology to Recognize Vehicle Loading Condition -
An Indirect Method Using Telematics and Machine Learning` is valid Mahindra
Research Valley evidence and qualifies as NNC opportunity evidence, but a
production scan may still fail to discover it when publisher-specific queries
are over-constrained or when one search provider returns zero results.

The source category is broader than `SAE paper`. The generic category is:

```yaml
source_category:
  professional_applied_ml_publication
```

It includes peer-reviewed or professional technical papers, conference papers,
technical presentations, proceedings, application papers, and customer
engineering case studies that satisfy:

1. an established target-company affiliation or explicit target-company role;
2. a concrete physical-system, control, sensing, estimation, diagnostics,
   prognostics, autonomy, or embedded-adjacent application;
3. an explicit ML, neural, data-driven, or adaptive-model method.

These documents are high-value BDA discovery targets even when they do not
mention `ONNX`, `MCU`, `TinyML`, or code generation.

Version 1.5 makes three changes:

- adds semantic use-case terms for indirect/virtual sensing and physical-state
  recognition such as vehicle load/payload/operating-condition estimation;
- replaces complex publisher Boolean queries with a mandatory set of small
  atomic query variants;
- introduces a zero-result provider fallback contract for high-value publisher
  query families.

A zero-result response from DDGS SHALL NOT be treated as successful completion
of a mandatory professional-publication query family. The same atomic query, or
a semantically equivalent simplified variant, SHALL be attempted with the next
available configured provider until the provider-success condition is met or all
eligible providers are exhausted.

## Version 1.6 patent-discovery and patented-ML opportunity correction

Version 1.6 corrects a patent-discovery false negative demonstrated by
`US12246700B2`, `Machine learning-based tractive limit and wheel stability
status estimation`. In the referenced GM scan the patent did not enter provider
results or the candidate queue, so it was never retrieved, attributed, or
classified.

The failure was caused primarily by a patent query that required `neural
network` and `embedded`. Patent titles and abstracts frequently use broader
method terminology such as `machine learning`, `regression`, `classification`,
`estimation`, `prediction`, `state estimation`, or the physical application
name. The specific neural architecture may appear only in dependent claims or
the detailed description.

Version 1.6 therefore establishes **patented applied-ML discovery** as a
mandatory, independently budgeted discovery family. Patent discovery SHALL
search from all of these directions:

1. target company / validated assignee + broad ML terminology;
2. target company / validated assignee + NNC-relevant use-case terminology;
3. target company / validated assignee + estimation / regression /
   classification terminology;
4. patent-host-restricted queries on Google Patents and Justia;
5. optional patent-classification terms such as `G06N20/00` and
   industry-specific CPC/IPC classes.

A patent SHALL NOT need `neural network`, `TinyML`, `ONNX`, `MCU`, `ECU`, or
`embedded` in its title or provider snippet in order to be selected for
retrieval.

Patent-assignee attribution is also separated from ordinary ambiguous-alias
matching. A validated patent assignee is a strong corporate-identity anchor.
Short aliases such as `GM` remain insufficient by themselves, but a validated
assignee such as `GM Global Technology Operations LLC` may establish target
company attribution.

Finally, Version 1.6 distinguishes an explicitly **claimed neural-network
embodiment** from a confirmed implemented/selected neural architecture. A
dependent patent claim that says a regression algorithm *may be a neural
network* is strong NNC opportunity evidence, but SHALL NOT by itself create a
confirmed NNC applicability mapping.

## Version 1.7 battery virtual-measurement and predictive-control patent correction

Version 1.7 corrects a second patent-discovery false negative demonstrated by
`US20240302440A1`, `Dynamic and predictive control of battery charging`.

The patent is strongly attributable to the target company through a validated
patent assignee and contains several NNC-relevant patterns:

- real-time estimation of internal battery performance variables that are not
  directly measured;
- calculated/virtual quantities such as anode potential, electrolyte
  concentration, capacity loss, and other electrochemical states;
- predictive charging control and model-based optimization;
- data-driven estimation including neural networks;
- hybrid model-based/data-driven estimation;
- a neural-network learning agent used to update charging calibration;
- execution in an onboard charging module, rechargeable-energy-storage
  controller, battery-management controller, or dedicated processing component.

The title does not contain `neural network`, `virtual sensor`, `BMS`, `MCU`, or
`embedded`. Consequently, a discovery strategy centered on neural terminology
will miss it.

Version 1.7 introduces a generic **latent/virtual physical-variable estimation**
taxonomy and extends patented applied-ML discovery so that patent queries are
generated from industry-specific use-case families, not only from product
terminology.

The design remains company-independent. `US20240302440A1` is a regression
fixture only. Production discovery SHALL work from generic company identity,
validated patent assignees, industry taxonomy, patent classifications, and
use-case terminology. No company-specific seed URL or patent number is required.

## Version 1.8 patent-native corpus discovery and coverage correction

Version 1.8 corrects the remaining search-process failure demonstrated by the
fact that neither `US12246700B2` nor `US20240302440A1` was discovered after the
Version 1.6/1.7 query and taxonomy improvements.

The decisive weakness is architectural: the BDA still treats patents mainly as
ordinary web-search results. Ordinary search engines return a small ranked
sample, may place the desired patent below the first page, and may return
non-patent pages for a nominal patent query. More query strings alone do not
provide adequate patent-corpus recall.

Version 1.8 therefore makes **patent-native assignee enumeration** the primary
patent discovery mechanism. General web search becomes a supplemental channel.

The normative patent workflow is:

```text
Validated target-company patent assignee
        ↓
Enumerate patent metadata from patent-native sources
        ↓
Normalize and validate patent records
        ↓
Build a bounded local assignee patent corpus
        ↓
Apply every required use-case synonym locally
        ↓
Rank metadata by NNC taxonomy and patent classifications
        ↓
Reserve retrieval slots by use-case family
        ↓
Retrieve complete text for the highest-ranked records
        ↓
Expand through CPC/IPC, patent family, citations, and related applications
        ↓
Company attribution, evidence classification, and reporting
```

The implementation SHALL NOT represent a generic web-search adapter as a
dedicated patent provider. A patent-native provider must enumerate or search a
patent corpus and return normalized patent records.

Version 1.8 adds:

1. direct assignee-based metadata enumeration;
2. a strict patent-result quality contract;
3. fallback based on usable patent results, not merely non-empty results;
4. complete required-synonym coverage for each patent use-case family;
5. pagination and a separate patent metadata/full-text budget;
6. use-case-family retrieval reservations;
7. local metadata ranking before expensive full-text retrieval;
8. CPC/IPC, patent-family, cited/citing, and related-application expansion;
9. new run artifacts and acceptance tests for patent coverage;
10. a dual regression requiring both GM patents to be found without production
    seeds, publication numbers, or exact URLs.

# 0. Instructions for Codex

## 0.1 Specification precedence

This document is authoritative for the new repository
`BD-Agent-for-NNC-v2.0`. The Power Electronics Version 1.26 specification is the
architectural baseline, but this document governs all Tiny-AI, Edge-AI,
microcontroller, neural-network, and Neural Net Coder semantics.

Where an implementation detail is not changed explicitly here, Codex SHALL retain
the corresponding Version 1.26 behavior. Where a Power Electronics term,
taxonomy category, scoring rule, example, product, or report statement conflicts
with this document, this document SHALL prevail.

## 0.2 Required architectural equivalence

Codex SHALL preserve the following Version 1.26 architecture:

1. deterministic Python pipeline before Local-LLM narrative generation;
2. one company processed at a time, with sequential registry processing;
3. YAML configuration validated against versioned JSON Schemas;
4. public-source discovery through additive multi-provider search;
5. accepted and rejected evidence with full provenance;
6. canonical-URL, document, passage, and evidence deduplication;
7. ChromaDB as the mandatory persistent vector store;
8. `bge-large` embeddings for portfolio-document retrieval;
9. `gemma2:9b` for one mandatory final company-summary attempt;
10. deterministic applicability mapping and scoring;
11. authoritative dSPACE-document grounding for every recommendation;
12. deterministic PDF and Markdown reporting;
13. Companies.xlsx input and atomic rating update;
14. run-level and cycle-level manifests;
15. degraded-run status that never masquerades as a completed no-fit assessment;
16. prompt assets loaded from external, versioned, hashed files;
17. product-ownership validation before publishing an LLM narrative;
18. zero-cost-only provider mode by default;
19. protected explicit seed handling before candidate-budget filtering;
20. automated unit and integration tests for every changed contract.

## 0.3 Domain-specific mandatory behavior

The NNC BDA SHALL:

1. identify target-company products, projects, research, prototypes, embedded
   systems, and engineering activities involving neural networks;
2. distinguish generic AI/ML evidence from confirmed neural-network evidence;
3. distinguish embedded/edge execution from cloud-only or workstation-only
   execution;
4. distinguish microcontroller-class or constrained ECU targets from high-power
   GPU, server, or datacenter targets;
5. distinguish a target company's technology from the dSPACE product Neural Net
   Coder;
6. derive neutral deployment, optimization, verification, resource, safety, and
   integration needs;
7. map those needs to verified Neural Net Coder capabilities;
8. assess the target company as a potential customer, ecosystem partner,
   silicon/toolchain partner, or competitor;
9. score applicability without claiming that the company currently uses or
   intends to buy Neural Net Coder;
10. preserve uncertainty when the model type, ONNX path, target MCU, resource
    envelope, or deployment stage is not disclosed;
11. establish the target-company relationship of every retrieved document before
    extracting any `target_company` technical evidence;
12. distinguish the company being scanned from the company actually established
    by the source, so provider/search provenance never becomes company attribution;
13. retain unrelated but technically useful Tiny-AI material only as separately
    labeled `general_industry_background`, with no score, mapping, or Relevant
    Evidence contribution;
14. distinguish `nnc_opportunity_evidence` from `nnc_mapping_evidence`, so a
    genuine company ML application may be visible in `Relevant Evidence` without
    being misrepresented as confirmed neural-network deployment;
15. discover applied ML research even when titles and abstracts omit `neural
    network`, `MCU`, `ONNX`, or code-generation terminology;
16. resolve corporate R&D-center and engineering-unit author affiliations using
    generic organizational-unit rules rather than requiring every unit name to
    be pre-entered as a workbook alias.

## 0.4 Non-negotiable semantic gates

The pipeline SHALL implement these gates in Python:

- **Target-company attribution gate:** before any technical gate is evaluated,
  the retrieved document SHALL establish a relationship to the company being
  scanned through a strong company anchor, official/approved domain, or explicit
  documented relationship. Search query text, provider ranking, candidate
  registration, an ambiguous short alias, or a bibliography-only name match SHALL
  NOT satisfy this gate.
- **Neural-network gate:** generic `AI`, `machine learning`, `analytics`, or
  `algorithm` language is insufficient. Strong applicability requires explicit
  neural-network evidence or a model architecture that is unambiguously neural.
- **Embedded-target gate:** strong applicability requires evidence of execution
  or intended execution on an MCU, ECU, embedded processor, bare-metal target,
  RTOS target, or similarly constrained control unit.
- **Deployment-workflow gate:** evidence of model training alone is insufficient;
  the company must face, or plausibly face, a model-to-embedded-software handover.
- **Company-role gate:** silicon vendors, deployment-tool vendors, and direct
  code-generation competitors SHALL not be scored like end-user engineering
  organizations.
- **Portfolio-grounding gate:** no recommendation may be published without
  authoritative Neural Net Coder document chunks retrieved from ChromaDB.
- **Ownership gate:** Neural Net Coder is a dSPACE product. The target company
  SHALL never be described as owning, supplying, developing, or using it unless
  explicit evidence supports that statement.
- **Evidence-locality gate:** the neural-model, embedded-target, and
  model-deployment/workflow gates SHALL be satisfied by one locally coherent
  evidence context. The pipeline SHALL NOT combine unrelated passages or
  documents merely because they belong to the same company.
- **Mapping-promotion gate:** an evidence item that proves only a generic ECU,
  microcontroller, RAM/ROM/stack/watchdog diagnostic, or signal encoding SHALL
  not support an NNC mapping. Mapping support remains subject to all Version 1.1
  locality gates.
- **Opportunity-evidence promotion gate:** a genuine target-company ML project
  MAY enter `Relevant Evidence` without mapping eligibility when it passes the
  company-attribution gate and the `nnc_opportunity_evidence` gate defined in
  Section 16.4. Opportunity evidence SHALL be explicitly marked as unconfirmed
  NNC applicability, SHALL contribute zero product-fit score, and SHALL not be
  used to complete neural-model, embedded-target, or deployment-workflow gates.

## 0.5 Product-boundary controls

The system SHALL NOT describe Neural Net Coder as:

- a neural-network training tool;
- a cloud inference platform;
- an embedded operating system;
- an MCU, DSP, NPU, GPU, accelerator, or runtime library;
- proof that an application is certified;
- guaranteed support for every ONNX operator or target architecture;
- guaranteed generation of accelerator-specific kernels;
- a replacement for target compiler qualification, system-level safety
  engineering, or application validation.

The system MAY describe verified capabilities such as deterministic C/C++ code
generation from supported ONNX networks, static memory behavior, early resource
forecasting, post-training optimization, and back-to-back verification only when
the authoritative portfolio corpus supports them.

## 0.6 Implementation identifiers

```json
{
  "design_document_version": "1.2.0",
  "specification_version": "1.2",
  "application_version": "2.0.0",
  "distribution_name": "bd-agent-for-nnc-v2",
  "python_package": "bd_agent_neural_net_coder",
  "domain_id": "tiny_edge_ai",
  "portfolio_item_id": "neural_net_coder"
}
```

Normative language:

- **SHALL** and **MUST** indicate mandatory behavior.
- **SHOULD** indicates a strong recommendation.
- **MAY** indicates optional behavior.
- Code blocks marked `Example` are illustrative unless explicitly declared
  normative.


# 1. Purpose

The BD Agent for Neural Net Coder is a local, evidence-driven Business
Development application. It processes one target company at a time, discovers
public evidence about the company's neural-network applications and embedded-AI
engineering, derives neutral deployment and validation needs, assesses whether
those needs align with Neural Net Coder, and generates an explainable Sales
Assessment Report.

The system is intended to support:

- account discovery and qualification;
- identification of embedded neural-network projects;
- technical meeting preparation;
- prioritization of companies for NNC campaigns;
- identification of relevant departments and roles;
- traceable explanation of why NNC may or may not fit.

It is not an autonomous sales authority. It does not prove purchase intent,
budget, technical compatibility, certification status, or active use of dSPACE
products.


# 2. Core Design Principles

### REQ-CORE-001 — Evidence first

Every technical conclusion SHALL be traceable to:

1. at least one public target-company passage;
2. one normalized target-company entity;
3. one explicit neutral engineering need;
4. one deterministic applicability relation; and
5. at least one authoritative Neural Net Coder portfolio passage.

### REQ-CORE-002 — Facts, inferences, and unknowns are separate

The system SHALL distinguish:

- observed company fact;
- verified dSPACE capability;
- inferred engineering need;
- inferred NNC applicability;
- inferred commercial opportunity;
- missing or unsupported information.

### REQ-CORE-003 — Deterministic logic before LLM narrative

Python SHALL perform configuration loading, validation, search planning,
provider execution, retrieval, parsing, lexical matching, local-context checks,
co-occurrence checks, exclusions, deduplication, entity normalization, scoring,
applicability selection, portfolio retrieval, ownership validation, artifact
persistence, file naming, and report layout.

The Local LLM SHALL generate only narrative fields after the deterministic
assessment is complete.

### REQ-CORE-004 — Discover company activity before inferring NNC need

The authoritative workflow is:

```text
Target-company project, product, research, or engineering activity
        ↓
Confirmed or cautiously inferred embedded neural-network deployment need
        ↓
Verified Neural Net Coder capability
        ↓
Neural Net Coder applicability assessment
```

A page that mentions an MCU, AI, or an application such as predictive
maintenance is not sufficient by itself. The relevant relationship must be
constructed explicitly.

### REQ-CORE-005 — YAML is authoritative configuration

Human-maintained domain configuration SHALL use YAML. Runtime-normalized
configuration MAY use JSON. Every YAML file SHALL be schema-validated before a
production scan.

### REQ-CORE-006 — Explicit semantic scopes

Every normalized entity SHALL use exactly one scope:

```yaml
entity_scope:
  - target_company
  - neutral_engineering_need
  - dspace_portfolio
```

Cross-scope generic fields such as `product_name`, `product_candidate`, or
`recommended_product` are prohibited. Use explicit names such as
`target_company_entity_id` and `dspace_portfolio_item_id`.


### REQ-CORE-007A — Search target is not evidence attribution

The company selected for a scan and the company established by a retrieved
source are distinct data concepts:

```yaml
company_provenance:
  scan_target_company_id: company requested by the current run
  attributed_company_id: company established from retrieved source content/domain
  attribution_status:
    - established
    - review_required
    - not_established
    - contradicted
```

Candidate registration SHALL populate `scan_target_company_id` only. It SHALL
NOT copy the scan target into `attributed_company_id`, `company_name`,
`entity_scope: target_company`, or any equivalent factual field before the
attribution gate passes.

### REQ-CORE-007B — Company attribution precedes technical extraction

For target-company assessment, document-level company attribution SHALL be
evaluated before neural, MCU/ECU, deployment, resource, verification, or safety
term extraction. If attribution is `not_established` or `contradicted`, technical
matches MAY be classified as background technology evidence but SHALL NOT be
emitted as target-company facts.

### REQ-CORE-007 — Company-role awareness

The system SHALL classify the company's role before final scoring:

```yaml
company_role:
  - end_user_or_oem
  - tier1_or_system_supplier
  - embedded_software_supplier
  - engineering_service_provider
  - research_institution
  - semiconductor_vendor
  - toolchain_or_runtime_vendor
  - direct_competitor
  - mixed_role
  - unknown
```

Role changes commercial interpretation but does not erase technical evidence.

### REQ-CORE-008 — Auditability and reproducibility

Every run SHALL persist the exact inputs, configuration hashes, prompt hashes,
model identifiers, generated and executed queries, provider responses, candidate
URLs, content hashes, accepted and rejected evidence, scoring trace, retrieved
portfolio chunks, LLM status, narrative validation, and workbook update status.

### REQ-CORE-009 — Negative evidence is retained

Cloud-only, non-neural, research-only, high-power-only, competitor-only, and
silicon-capability-only evidence SHALL be retained as rejected or non-applicable
evidence when it contributes to the final decision.

### REQ-CORE-010 — No silent target compatibility assumption

An MCU family name does not prove that Neural Net Coder supports the exact
target, compiler, operator set, precision, or accelerator. Such compatibility
SHALL remain a qualification item unless confirmed by authoritative dSPACE
documentation.


# 3. Supported Technology Stack

The production stack SHALL match the Power Electronics BDA Version 1.26 unless
this document states otherwise:

- Python 3.11 or later;
- ChromaDB, used directly as the persistent vector store;
- Ollama for local model and embedding execution;
- `gemma2:9b` for final narrative generation;
- `bge-large` for portfolio-document and semantic retrieval embeddings;
- DDGS as a mandatory public-search provider;
- optional Brave Search API, SerpAPI, Serper, Semantic Scholar, and GitHub;
- `httpx.AsyncClient` for bounded asynchronous retrieval;
- `pydantic` and/or `jsonschema` for runtime validation;
- `PyYAML` or `ruamel.yaml`;
- `PyMuPDF` and/or `pypdf` for PDF parsing;
- BeautifulSoup and `lxml` for HTML/XML parsing;
- ReportLab for deterministic PDF generation;
- a spreadsheet library compatible with the existing Companies.xlsx contract.

Core dependencies SHALL be declared in `pyproject.toml`.

```toml
[project]
name = "bd-agent-for-nnc-v2"
version = "2.0.0"
requires-python = ">=3.11"

[project.optional-dependencies]
vector = ["llama-index>=0.11"]
```

`llama-index` remains optional. Production ingestion and retrieval SHALL use
ChromaDB directly.

Canonical search-provider environment variables remain:

```text
BRAVE_SEARCH_API_KEY
SERPAPI_API_KEY
SERPER_API_KEY
SEMANTIC_SCHOLAR_API_KEY
GITHUB_TOKEN
```

No secret SHALL appear in configuration files, artifacts, reports, logs, URLs,
or exception text.


# 4. Repository Structure

```text
BD-Agent-for-NNC-v2.0/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── docs/
│   ├── BD_AGENT_NNC_IMPLEMENTATION_SPEC.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── DATA_DICTIONARY.md
├── config/
│   ├── domains/
│   │   └── tiny_edge_ai/
│   │       ├── company_domain_taxonomy.yaml
│   │       ├── company_domain_layers.yaml
│   │       ├── engineering_need_taxonomy.yaml
│   │       ├── use_case_taxonomy.yaml
│   │       ├── hardware_target_taxonomy.yaml
│   │       ├── model_and_framework_taxonomy.yaml
│   │       ├── search_profiles.yaml
│   │       ├── query_templates.yaml
│   │       ├── exclusions.yaml
│   │       ├── scoring_rules.yaml
│   │       ├── page_relevance.yaml
│   │       └── schemas/
│   ├── dspace_portfolio/
│   │   ├── dspace_portfolio_index.yaml
│   │   ├── dspace_portfolio_profiles.yaml
│   │   ├── dspace_portfolio_aliases.yaml
│   │   ├── applicability_mapping_rules.yaml
│   │   └── schemas/
│   ├── search_providers.yaml
│   ├── schemas/
│   └── runtime/
│       ├── company_registry.yaml
│       ├── hardware_profiles.yaml
│       ├── models.yaml
│       └── model_benchmarks.yaml
├── data/
│   ├── Companies.xlsx
│   ├── backups/
│   ├── company_inputs/
│   ├── company_source_profiles/
│   ├── nnc_reference_use_cases/
│   ├── dspace_portfolio_documents/
│   ├── dspace_portfolio_runtime/
│   │   └── chroma_db/
│   ├── search_runtime/
│   │   └── patents/
│   │       ├── assignee_registry/
│   │       ├── metadata_cache/
│   │       ├── classification_cache/
│   │       └── family_graph_cache/
│   └── cache/
├── prompts/
│   ├── company_summary_system_v3.txt
│   ├── company_summary_user_template_v3.txt
│   ├── company_summary_output_schema_v3.json
│   ├── company_summary_prompt_manifest_v3.yaml
│   ├── ownership_contract_v1.yaml
│   └── optional_ambiguous_evidence_review_v1.txt
├── src/
│   └── bd_agent_neural_net_coder/
│       ├── cli.py
│       ├── config_manager.py
│       ├── pipeline.py
│       ├── portfolio_index.py
│       ├── workbook.py
│       ├── prompt_loader.py
│       ├── llm_context_builder.py
│       ├── narrative_ownership_validator.py
│       ├── brave_provider.py
│       ├── ddgs_provider.py
│       ├── github_provider.py
│       ├── internal_crawler_provider.py
│       ├── patent_provider.py
│       ├── pdf_link_provider.py
│       ├── semantic_scholar_provider.py
│       ├── serpapi_provider.py
│       ├── serper_provider.py
│       ├── sitemap_provider.py
│       └── <remaining flat runtime/support modules>
├── output/
│   ├── companies/
│   └── cycles/
└── tests/
    ├── unit/
    └── integration/
        └── test_pipeline.py
```

The source package SHALL remain a consolidated flat package. Provider adapters
SHALL be located directly under `src/bd_agent_neural_net_coder/`; a
`search_providers/` package or agentic-loop subpackage is not required.

Core responsibilities remain consolidated:

`patent_provider.py` SHALL NOT be a generic employment/web-search adapter. It
MAY orchestrate multiple patent-native backends in the consolidated flat module,
but each backend capability SHALL be represented in the provider manifest.

Required capability identifiers:

```yaml
patent_provider_capabilities:
  - assignee_enumeration
  - paginated_metadata_search
  - patent_record_normalization
  - patent_identifier_validation
  - assignee_metadata_extraction
  - abstract_or_summary_extraction
  - classification_extraction
  - patent_family_expansion
  - cited_and_citing_expansion
  - full_text_location_resolution
```

A configured backend that does not support any patent-native capability SHALL
not be labeled `patent_provider`.


| Module | Responsibility |
|---|---|
| `pipeline.py` | scan orchestration, retrieval flow, taxonomy processing, deterministic assessment, applicability, LLM invocation, fallback, artifact coordination |
| `portfolio_index.py` | PDF chunking, embeddings, ChromaDB ingestion, validation, and NNC portfolio retrieval |
| `workbook.py` | Companies.xlsx loading, validation, backup, pending updates, atomic rating updates |
| `config_manager.py` | YAML/JSON configuration and schema validation |
| `prompt_loader.py` | external prompt loading, version and hash validation |
| `llm_context_builder.py` | curated context construction and prompt-budget enforcement |
| `narrative_ownership_validator.py` | dSPACE ownership, attribution, unsupported-claim validation |
| `patent_provider.py` | patent-native assignee enumeration, pagination, normalized patent metadata, provider-quality validation, local corpus construction, patent-family/classification expansion, and handoff of selected full-text patent candidates |


# 5. Run Identity, File Naming, and Persistence

Every company scan SHALL create a unique UTC-timestamped directory:

```text
output/companies/<company_slug>/<YYYYMMDDTHHMMSSZ>/
```

Every machine-readable artifact SHALL use:

```text
<company_slug>_<run_timestamp>_<artifact_name>.<extension>
```

Required artifacts include:

```text
<company_slug>_<timestamp>_run_manifest.json
<company_slug>_<timestamp>_search_queries.json
<company_slug>_<timestamp>_provider_execution.json
<company_slug>_<timestamp>_patent_assignee_registry.json
<company_slug>_<timestamp>_patent_enumeration_manifest.json
<company_slug>_<timestamp>_patent_provider_quality.json
<company_slug>_<timestamp>_patent_metadata_corpus.jsonl
<company_slug>_<timestamp>_patent_term_coverage.json
<company_slug>_<timestamp>_patent_metadata_rankings.json
<company_slug>_<timestamp>_patent_family_expansion.json
<company_slug>_<timestamp>_patent_full_text_manifest.json
<company_slug>_<timestamp>_candidate_sources.json
<company_slug>_<timestamp>_company_attribution.json
<company_slug>_<timestamp>_general_industry_background.json
<company_slug>_<timestamp>_retrieval_results.json
<company_slug>_<timestamp>_accepted_evidence.json
<company_slug>_<timestamp>_rejected_evidence.json
<company_slug>_<timestamp>_company_assessment.json
<company_slug>_<timestamp>_applicability_assessment.json
<company_slug>_<timestamp>_final_assessment.json
<company_slug>_<timestamp>_narrative_validation.json
<company_slug>_<timestamp>_sales_assessment.md
<Company-Safe-Name>_Sales-Assessment_<readable-UTC-timestamp>.pdf
```

No existing historical run directory or production report SHALL be overwritten.

Patent artifacts SHALL distinguish:

- assignee identity validation;
- patent metadata enumeration;
- metadata-record validation;
- local taxonomy matching;
- full-text selection;
- full-text retrieval;
- evidence extraction.

A patent shall not first appear only in `candidate_sources.json`. Every patent
candidate originating from patent-native discovery SHALL be traceable to a
record in `patent_metadata_corpus.jsonl`.

The run manifest SHALL identify at minimum:

```json
{
  "specification_version": "1.1",
  "design_document_version": "1.1.0",
  "application_version": "2.0.0",
  "domain_id": "tiny_edge_ai",
  "portfolio_item_id": "neural_net_coder",
  "embedding_model": "bge-large",
  "summary_model": "gemma2:9b"
}
```

A technical failure of search, retrieval, portfolio grounding, deterministic
assessment, reporting, or workbook update SHALL be represented explicitly. It
SHALL not be converted into a no-fit score.


# 6. Deterministic Applicability Mapping vs. Semantic dSPACE Portfolio Retrieval

Two mechanisms SHALL remain separate.

## 6.1 Deterministic applicability mapping

YAML rules plus Python logic decide whether observed company evidence maps to a
neutral engineering need and whether that need is applicable to Neural Net Coder.

Deterministic mapping SHALL use:

- explicit term classes;
- co-occurrence windows;
- model-type classification;
- target-type classification;
- deployment-stage classification;
- resource-constraint evidence;
- verification and safety evidence;
- company-role classification;
- exclusions;
- confidence;
- source quality;
- evidence independence;
- compatibility unknowns.

The Local LLM SHALL not select Neural Net Coder or calculate the score.

## 6.2 Semantic portfolio retrieval

`bge-large` plus ChromaDB retrieve authoritative Neural Net Coder passages that
support the applicable capability.

Retrieval SHALL answer questions such as:

- Does NNC generate deterministic C/C++ from supported ONNX networks?
- Does NNC use static memory and avoid dynamic allocation?
- Which resource estimates are available?
- Which optimizations are supported?
- Which MIL/SIL/PIL or back-to-back checks are supported?
- What is the supported integration route?
- What limitations or prerequisites are stated?

Semantic similarity is not a scoring rule. A high-similarity chunk cannot
override deterministic exclusions or invent target support.

## 6.3 Required chain

```text
Company evidence
  -> normalized target-company entity
  -> neutral embedded-AI engineering need
  -> deterministic NNC capability mapping
  -> retrieved authoritative NNC chunks
  -> grounded applicability statement
```

If any mandatory link is missing, the mapping SHALL be conditional, weak, or
rejected according to the rules in this document.


# 7. End-to-End Workflow

The production workflow SHALL execute in this order:

1. load and validate configuration;
2. validate installation, models, prompts, portfolio index, and provider
   preflight;
3. load the selected company and metadata;
4. register explicit seeds in an immutable seed registry;
5. build deterministic query families;
6. persist query plan;
7. execute every enabled mandatory query on at least one configured provider;
8. add homepage, seed, search, sitemap, internal-link, PDF, publication,
   patent, GitHub, and research candidates;
9. canonicalize and deduplicate candidates;
10. reserve protected seed slots;
11. apply candidate budgets after seed reservation;
12. retrieve HTML and PDF content;
13. parse, normalize, hash, and cache documents and passages;
14. score page relevance;
15. identify and normalize target-company AI entities;
16. classify neural-network evidence;
17. classify target hardware and deployment context;
18. classify company role;
19. create accepted and rejected evidence objects;
20. deduplicate evidence while preserving provenance;
21. derive neutral engineering needs;
22. apply deterministic NNC rules and calculate score;
23. query the validated NNC portfolio index;
24. enforce the portfolio-grounding gate;
25. construct the deterministic final assessment;
26. build curated LLM context;
27. request exactly one mandatory Gemma company-summary attempt;
28. validate structure, length, ownership, attribution, and substantive content;
29. use deterministic fallback if the LLM output is invalid;
30. render Markdown and PDF;
31. persist all artifacts and manifests;
32. update Companies.xlsx atomically only for a complete eligible run;
33. finalize the cycle manifest and human-readable cycle summary.

Optional ambiguous-evidence review MAY be enabled explicitly. It SHALL be off by
default and SHALL never replace deterministic evidence acceptance or scoring.


# 8. Configuration Architecture

The configuration layers SHALL remain explicit:

```text
config/domains/tiny_edge_ai/
    What target-company evidence means in this domain.

config/dspace_portfolio/
    What Neural Net Coder is, what it supports, and how needs map to it.

config/search_providers.yaml
    Which discovery providers are enabled and how quotas are enforced.

config/runtime/
    Model, hardware, registry, timeout, and benchmark configuration.

prompts/
    Versioned and hashed Local-LLM instructions and output schema.
```

The Tiny-AI domain SHALL not contain unverified dSPACE product claims. The
dSPACE portfolio profile SHALL not contain target-company facts.

At minimum, every configuration object SHALL include:

```yaml
config_id: <stable_identifier>
config_version: <semantic_version>
schema_version: <semantic_version>
status: active
```

Cross-reference validation SHALL confirm that:

- every taxonomy term category exists;
- every engineering need used by a rule is defined;
- every applicability rule resolves to `neural_net_coder`;
- every required capability exists in the portfolio profile;
- every exclusion references a valid term or classification;
- every score component is bounded;
- every prompt manifest hash matches its file;
- every portfolio source listed in the index exists and is ingested.


# 9. Target-Company Tiny-AI / Edge-AI Taxonomy

The taxonomy SHALL describe what a target company develops, deploys, tests,
integrates, or researches. It SHALL not describe dSPACE products.

## 9.1 Top-level taxonomy

```yaml
target_company_taxonomy:
  embedded_ai_activity:
    - neural_network_application
    - virtual_or_soft_sensor
    - predictive_maintenance
    - anomaly_detection
    - classification
    - regression_or_estimation
    - computer_vision
    - audio_or_acoustic_ai
    - gesture_or_human_activity_recognition
    - health_or_condition_monitoring
    - smart_actuator_or_local_control
    - sensor_fusion
    - embedded_generative_or_sequence_model

  model_and_algorithm:
    - feedforward_neural_network
    - convolutional_neural_network
    - one_dimensional_cnn
    - recurrent_neural_network
    - lstm
    - gru
    - temporal_convolutional_network
    - autoencoder
    - transformer_or_attention
    - multi_layer_perceptron
    - neural_state_estimator
    - hybrid_physics_neural_model
    - unknown_neural_network

  deployment_target:
    - automotive_ecu
    - industrial_controller
    - microcontroller
    - arm_cortex_m
    - arm_cortex_r
    - bare_metal
    - rtos
    - low_power_soc
    - embedded_mpu
    - dsp_or_npu_assisted_mcu
    - unknown_embedded_target
    - non_constrained_edge_target
    - cloud_or_server_target

  deployment_workflow:
    - python_trained_model
    - tensorflow_model
    - pytorch_model
    - keras_model
    - onnx_model
    - model_conversion
    - embedded_c_or_cpp
    - manual_reimplementation
    - runtime_library
    - code_generation
    - compiler_or_toolchain
    - sil_validation
    - pil_validation
    - hil_validation
    - production_ecu_integration

  resource_constraint:
    - ram_limit
    - rom_or_flash_limit
    - stack_limit
    - execution_time_limit
    - hard_real_time
    - power_or_energy_limit
    - thermal_limit
    - static_memory_requirement
    - no_dynamic_allocation
    - model_size_limit
    - bandwidth_limit

  optimization:
    - post_training_quantization
    - quantization_aware_training
    - int8
    - int16
    - mixed_precision
    - pruning
    - sparsity
    - knowledge_distillation
    - operator_fusion
    - memory_planning
    - architecture_search
    - fixed_point
    - weight_compression

  verification_and_safety:
    - back_to_back_test
    - mil
    - sil
    - pil
    - numerical_equivalence
    - accuracy_degradation_check
    - mae
    - mse
    - rmse
    - misra_c
    - iso_26262
    - iso_pas_8800
    - functional_safety
    - deterministic_execution
    - traceability
    - certification_evidence

  organization_and_role:
    - ai_or_data_science_team
    - embedded_software_team
    - ecu_development_team
    - functional_safety_team
    - verification_and_validation_team
    - toolchain_team
    - innovation_or_research_team
    - semiconductor_vendor
    - software_tier1
    - engineering_service_provider
    - direct_deployment_tool_vendor
```

## 9.2 D·A·M and deployment-layer organization

The taxonomy SHALL incorporate the machine-learning systems view that Data,
Algorithm, and Machine constrain each other. For BDA purposes, the normalized
layers are:

```yaml
domain_layers:
  mission:
    - application_goal
    - real_time_requirement
    - safety_criticality
    - privacy_or_offline_requirement

  data:
    - sensor_signal
    - modality
    - sample_rate
    - training_data_source
    - calibration_data
    - deployment_distribution

  algorithm:
    - model_family
    - operator_set
    - parameter_count
    - precision
    - preprocessing
    - postprocessing

  machine:
    - silicon_vendor
    - mcu_or_processor_family
    - core_architecture
    - accelerator
    - ram
    - flash_or_rom
    - clock
    - power_budget

  deployment:
    - model_handover_format
    - generated_or_runtime_code
    - compiler
    - operating_environment
    - integration_stage

  verification:
    - reference_execution
    - generated_code_execution
    - target_execution
    - comparison_metric
    - acceptance_threshold

  lifecycle:
    - versioning
    - retraining
    - regression_test
    - release_process
    - field_update
    - monitoring
```

These layers SHALL be used to prevent a common false positive: finding an
interesting application without evidence about the algorithm or deployment
machine.

## 9.3 Use-case classes

The system SHALL recognize at least:

- virtual and soft sensors;
- battery state-of-charge and state-of-health estimation;
- battery health monitoring, battery aging/degradation estimation, capacity
  estimation, battery prognostics, remaining useful life, and BMS diagnostics;
- tire, brake, wheel-force, torque, pressure, temperature, piston-pressure, and
  other virtual measurement;
- predictive maintenance and remaining-useful-life estimation;
- vibration, acoustic, current, thermal, and multi-sensor anomaly detection;
- in-cabin audio and event detection;
- keyword spotting and speech-command recognition;
- person, object, occupancy, and gesture detection;
- health and wearable signal analysis;
- smart actuators and local control assistance;
- sensor fusion and condition monitoring;
- indirect sensing, latent-state estimation, and operating-condition recognition;
- vehicle load, payload, mass, loading-condition, and operating-state estimation;
- telematics-based inference from vehicle-driving behavior or operational signals;
- tire-road friction, tractive/traction-limit, wheel-slip, and wheel-stability estimation;
- road-surface/road-condition estimation and grip/adhesion estimation;
- vehicle-dynamics state estimation from onboard sensors;
- learned regression/classification models used to support drive, brake, yaw,
  traction, stability, or ABS control;
- latent or virtual electrochemical-variable estimation for batteries and other
  energy-storage systems;
- predictive charging, charging-limit estimation, charging-current optimization,
  and degradation-aware charging control;
- adaptive calibration or control updated by a neural-network or other learned
  agent;
- hybrid physics/data-driven estimation and control.

Every use-case class SHALL define a `discovery_lexicon` that is broader than its
acceptance terminology. The discovery lexicon is used to find company technical
material whose title or metadata describes the application but not the model
architecture.

Example:

```yaml
use_case_discovery_lexicon:
  battery_health_and_state_estimation:
    priority_by_industry:
      automotive: highest
      off_highway: high
      energy: high
      aerospace: high
      industrial: medium
    terms:
      - battery health
      - battery health monitoring
      - state of health
      - SOH
      - state of charge
      - SOC
      - battery state estimation
      - battery capacity estimation
      - battery aging
      - battery degradation
      - battery prognostics
      - remaining useful life
      - RUL
      - battery management system
      - BMS
      - cell health
    technical_action_terms:
      - estimate
      - estimation
      - predict
      - prediction
      - monitor
      - monitoring
      - diagnose
      - prognostics
      - classifier
      - estimator
```


Additional mandatory discovery lexicon:

```yaml
  indirect_physical_state_and_virtual_sensing:
    priority_by_industry:
      automotive: highest
      off_highway: highest
      industrial: high
      aerospace: high
      energy: medium
    terms:
      - indirect sensing
      - indirect measurement
      - virtual sensor
      - soft sensor
      - sensorless
      - sensorless estimation
      - state estimation
      - operating condition
      - operating-condition recognition
      - condition recognition
      - loading condition
      - vehicle loading condition
      - vehicle load estimation
      - payload estimation
      - vehicle mass estimation
      - driving behavior
      - telematics based inference
      - telematics machine learning
      - low-cost sensing
    technical_action_terms:
      - recognize
      - recognition
      - detect
      - detection
      - estimate
      - estimation
      - infer
      - inference
      - classify
      - classification
      - predict
      - prediction
```

`vehicle loading condition`, `payload estimation`, `operating-condition
recognition`, and similar phrases SHALL be treated as semantic neighbors of
virtual/soft sensing for discovery purposes even if the source does not use the
terms `virtual sensor` or `soft sensor`.


Additional automotive/off-highway vehicle-dynamics discovery lexicon:

```yaml
vehicle_dynamics_learned_estimation:
  priority_by_industry:
    automotive: highest
    off_highway: highest
    aerospace: low
    industrial: low
    energy: low
  terms:
    - tractive limit
    - traction limit
    - tire-road friction
    - tire road friction
    - road friction
    - friction coefficient
    - coefficient of friction
    - road condition estimation
    - road surface estimation
    - grip estimation
    - adhesion estimation
    - wheel stability
    - wheel stability status
    - wheel slip
    - slip ratio
    - tire saturation
    - tire force estimation
    - vehicle state estimation
    - vehicle dynamics estimation
    - vehicle motion state
    - traction control
    - yaw control
    - antilock braking
    - ABS
  model_action_terms:
    - regression model
    - classification model
    - machine learning regression
    - machine learning classification
    - learned estimator
    - learned model
    - state estimator
    - prediction model
  embedded_adjacent_terms:
    - onboard sensor
    - on-board sensor
    - onboard controller
    - on-board controller
    - programmable electronic control unit
    - dedicated electronic control unit
    - vehicle controller
    - data processor
```

These terms SHALL increase discovery and retrieval priority. They SHALL not
alone prove a neural network.


Additional battery/energy-storage latent-variable and predictive-control
discovery lexicon:

```yaml
battery_virtual_measurement_and_predictive_control:
  priority_by_industry:
    automotive: highest
    off_highway: high
    aerospace: high
    energy: highest
    industrial: medium

  use_case_terms:
    - battery charging
    - predictive charging
    - dynamic charging
    - fast charging
    - DC fast charging
    - charging control
    - charging limit
    - charge limit
    - charging current optimization
    - battery state estimation
    - battery health
    - battery health monitoring
    - state of health
    - state of charge
    - battery prognostics
    - battery degradation
    - battery aging
    - capacity loss
    - lithium plating

  virtual_or_latent_variable_terms:
    - virtual measurement
    - virtual measurements
    - calculated variable
    - calculated performance variable
    - dynamic performance variable
    - latent state
    - latent variable
    - internal battery state
    - electrochemical state
    - electrochemical variable
    - anode potential
    - anode voltage
    - electrolyte concentration
    - electrolyte ion concentration
    - capacity loss
    - aging parameter
    - plating limit
    - lithium plating limit

  learned_estimation_terms:
    - data-driven estimation
    - data driven estimation
    - data-driven estimator
    - data driven estimator
    - neural network estimator
    - machine learning estimator
    - hybrid data-driven
    - hybrid data driven
    - physics-informed
    - physics informed
    - model-based and data-driven
    - model based and data driven
    - learning agent
    - neural network learning agent
    - adaptive calibration

  control_terms:
    - model predictive control
    - predictive control
    - MPC
    - closed loop charging
    - closed-loop charging
    - current profile
    - target current profile
    - charging calibration
    - baseline calibration

  onboard_terms:
    - battery management controller
    - battery management system
    - BMS
    - rechargeable energy storage system
    - RESS
    - RESS controller
    - onboard charging module
    - on-board charging module
    - OBCM
    - charging control system
    - dedicated controller
    - processing device
```

For discovery purposes, `virtual measurement`, `calculated performance
variable`, `dynamic performance variable`, `latent state`, and equivalent terms
SHALL be semantic neighbors of `virtual sensor` / `soft sensor` when the source
describes estimation of an internal physical quantity from measured signals or
a learned/model-based estimator.

This semantic expansion affects discovery and opportunity classification only.
It SHALL NOT convert purely physics-based observers, EKFs, or model-predictive
controllers into neural-network evidence.

A use-case class is not proof of a neural network. Linear regression, Kalman
filters, statistical estimators, rules, and physical models SHALL remain
separate classifications. Use-case terms may raise *discovery and retrieval
priority* without increasing the deterministic NNC product-fit score.

## 9.4 Model terms

### Strong neural-network terms

```yaml
strong_neural_terms:
  - neural network
  - deep neural network
  - DNN
  - CNN
  - convolutional neural network
  - 1D CNN
  - RNN
  - recurrent neural network
  - LSTM
  - GRU
  - multilayer perceptron
  - MLP
  - autoencoder
  - transformer
  - attention network
  - temporal convolutional network
  - neural estimator
  - deep learning
  - ONNX model
```

### Generic but insufficient terms

```yaml
generic_ai_terms:
  - artificial intelligence
  - AI
  - machine learning
  - ML
  - intelligent algorithm
  - analytics
  - data-driven model
  - advanced algorithm
```

Generic terms MAY create discovery candidates but SHALL not pass the neural
network gate without stronger local context.

### Hybrid neural / adaptive-network terms

The following terms SHALL be recognized during discovery and evidence
classification because they contain or explicitly use a neural-network component,
but they SHALL NOT automatically prove direct NNC/ONNX compatibility:

```yaml
hybrid_neural_terms:
  - neuro-fuzzy
  - neuro fuzzy
  - adaptive neuro-fuzzy
  - adaptive neuro fuzzy
  - adaptive neuro-fuzzy inference system
  - ANFIS
  - adaptive neuro-fuzzy classifier
  - adaptive neuro fuzzy classifier
  - ANFC
  - artificial neural network
  - ANN

hybrid_neural_semantics:
  neural_component_confirmed_if:
    - source_explicitly_states_neural_network_adaptation
    - source_explicitly_models_the_method_as_an_artificial_neural_network
  direct_nnc_compatibility:
    default: unconfirmed
    requires:
      - exportable_supported_neural_subgraph_or_equivalent_ONNX_model
      - supported_operator_set
      - deployment_target_qualification
```

A hybrid neuro-fuzzy source may therefore qualify as
`nnc_opportunity_evidence` with `neural_component_status=confirmed` while
`mapping_eligible=false` until ONNX/operator and embedded-target requirements are
established.


### Neural-network evidence strength in patents

Patent language SHALL be classified by evidential strength:

```yaml
patent_neural_evidence_strength:
  confirmed_required_or_implemented:
    meaning: neural architecture is required by the relevant claim or explicitly described as the implemented embodiment
    mapping_gate_effect: may_satisfy_neural_gate_subject_to_other_gates

  claimed_optional_embodiment:
    meaning: a dependent claim explicitly names a neural network as one claimed alternative among multiple model choices
    mapping_gate_effect: does_not_confirm_selected_company_implementation
    opportunity_relevance: high

  mentioned_possible_method:
    meaning: neural network appears only as an illustrative option in description
    mapping_gate_effect: no
    opportunity_relevance: medium

  generic_machine_learning_only:
    meaning: ML is explicit but no neural method is disclosed
    mapping_gate_effect: no
    opportunity_relevance: potentially_high

  absent:
    mapping_gate_effect: no
```

`claimed_optional_embodiment` SHALL be stronger than a generic narrative
mention, but it SHALL still produce:

```yaml
neural_model_status: possible_but_not_selected_or_confirmed
mapping_eligible_from_neural_evidence_alone: false
```


### Neural subcomponent and learning-agent evidence

A source MAY contain a neural-network component even when the overall algorithm
is hybrid, model-predictive, neuro-symbolic, physics-based, or adaptive.

```yaml
neural_subcomponent_evidence:
  explicit_neural_estimator_embodiment:
    meaning: source explicitly permits or describes a neural network as the estimator for a physical variable
    neural_component_status: confirmed_as_embodiment
    mapping_gate_effect: no_by_itself
    opportunity_relevance: high

  explicit_neural_learning_agent:
    meaning: source explicitly describes a neural-network-based learning agent that updates calibration, parameters, limits, or another control artifact
    neural_component_status: confirmed_as_embodiment
    mapping_gate_effect: no_by_itself
    opportunity_relevance: high

  hybrid_physics_data_driven_estimator:
    meaning: source explicitly combines a physics/model-based estimator with a data-driven component
    neural_component_status: confirmed_only_if_neural_is_explicit
    mapping_gate_effect: no_by_itself
    opportunity_relevance: high
```

The BDA SHALL preserve the role of the neural component. A neural estimator, a
neural learning agent, and a neural controller are different technical roles and
SHALL not be collapsed into a generic `neural_network` label.

If the source explicitly describes one of these neural embodiments in an
onboard/embedded-adjacent target-company application but does not disclose ONNX,
supported operators, generated C/C++, or the deployed production architecture:

```yaml
relevance_class: nnc_opportunity_evidence
relevant_evidence: true
mapping_eligible: false
score_contribution: 0
```

### Non-neural or ambiguous model terms

```yaml
adjacent_non_neural_terms:
  - linear regression
  - logistic regression
  - decision tree
  - random forest
  - support vector machine
  - SVM
  - gradient boosting
  - XGBoost
  - Kalman filter
  - extended Kalman filter
  - Gaussian process
  - lookup table
  - physical model
  - observer
  - rule-based
```

These terms are useful for negative classification and hybrid-model analysis.

## 9.5 Hardware and target terms

The hardware taxonomy SHALL include generic and named MCU/embedded families,
including but not limited to:

```yaml
hardware_families:
  nxp:
    - S32K3
    - S32K344
    - S32K5
    - S32K566
    - i.MX RT
    - i.MX RT1170
    - MPC5746R
  infineon:
    - AURIX
    - AURIX TC4x
    - PSoC Edge
  renesas:
    - RH850
    - RH850 U2B
    - RA8
    - RA8D1
  stmicroelectronics:
    - Stellar P3E
    - STM32N6
    - STM32U5
  texas_instruments:
    - C2000
    - Sitara AM62A-Q1
  ambiq:
    - Apollo4 Blue
    - Apollo5
    - Apollo510
  espressif:
    - ESP32-S3
  nordic:
    - nRF54L
    - nRF54LM20B
  silicon_labs:
    - xG24
    - MG24
  architectures:
    - Arm Cortex-M
    - Arm Cortex-R
    - PowerPC
    - RISC-V MCU
```

Named hardware is evidence of a target, not of NNC support.

## 9.6 Framework, format, and toolchain terms

```yaml
framework_and_format_terms:
  training:
    - PyTorch
    - TensorFlow
    - Keras
    - MATLAB
    - Simulink
  interchange:
    - ONNX
    - Open Neural Network Exchange
  embedded_runtime_or_toolchain:
    - TensorFlow Lite Micro
    - TFLite Micro
    - CMSIS-NN
    - microTVM
    - ExecuTorch
    - Edge Impulse
    - NXP eIQ
    - STM32Cube.AI
    - X-CUBE-AI
    - Renesas Reality AI
    - Infineon DeepCraft
    - HighTec ONNX2C
    - MATLAB Coder
    - Embedded Coder
    - AUTOSAR code generation
```

Competitor or adjacent-tool terms SHALL support market context and role
classification, not automatic rejection. The system SHALL determine whether the
target company is a user, partner, supplier, or vendor.

## 9.7 Acronym and ambiguity controls

The taxonomy SHALL include deterministic disambiguation for:

- `SoC`: state of charge vs. system-on-chip;
- `SOH`: state of health;
- `NN`: neural network only in technical local context;
- `AI MCU`: MCU with AI capability, not proof of deployed AI;
- `edge`: edge computing, geometric edge, network edge, or business wording;
- `model`: ML model, physical model, product model, or document model;
- `inference`: neural inference vs. ordinary deduction;
- `sensor fusion`: algorithmic fusion, not necessarily ML;
- `virtual sensor`: may be physics-based, statistical, or neural.

The local-context validator SHALL require nearby supporting terms before
acceptance.

## 9.8 Target-company identity and attribution taxonomy

Company identity is an independent taxonomy dimension and a hard gate. It is not
an ordinary relevance keyword.

```yaml
company_identity_taxonomy:
  company_anchor_type:
    canonical_full_name:
      strength: strong
    registered_legal_name:
      strength: strong
    official_domain_ownership:
      strength: strong
    approved_affiliate_or_asset_domain:
      strength: strong
    employee_author_affiliation:
      strength: strong
      require_explicit_company_affiliation: true
    explicit_subject_relationship:
      strength: strong
      examples:
        - developed_by_target_company
        - deployed_by_target_company
        - target_company_case_study_subject
        - explicit_partner_collaboration_with_target_company
    validated_brand_or_subsidiary_relationship:
      strength: medium
      require_registry_relationship: true
    long_form_alias:
      strength: medium
    short_acronym_alias:
      strength: weak
      discovery_only_default: true
    search_query_token:
      strength: none
    search_result_snippet_only:
      strength: none
    bibliography_or_reference_only:
      strength: none
    personal_initials:
      strength: none

  attribution_status:
    - established
    - review_required
    - not_established
    - contradicted

  source_attribution_scope:
    - target_company
    - explicitly_related_partner
    - general_industry_background
    - unrelated_entity
```

Attribution is `established` when at least one strong anchor is present and no
contradictory ownership/affiliation evidence exists. A medium anchor MAY establish
identity only when supported by a second independent medium anchor or a validated
registry relationship. Weak/none anchors SHALL never establish identity alone.

### 9.8.1 Alias risk classes

Every company alias in `Companies.xlsx` or the company registry SHALL have an
alias class:

```yaml
company_alias_class:
  - canonical_name
  - legal_name
  - brand_name
  - long_unambiguous_alias
  - short_acronym
  - ambiguous_short_acronym
```

Default policy:

```yaml
alias_policy:
  canonical_name:
    query_allowed: true
    attribution_anchor: strong
  legal_name:
    query_allowed: true
    attribution_anchor: strong
  brand_name:
    query_allowed: true
    attribution_anchor: medium
  long_unambiguous_alias:
    query_allowed: true
    attribution_anchor: medium
  short_acronym:
    query_allowed: true
    attribution_anchor: weak
    independent_attribution_allowed: false
  ambiguous_short_acronym:
    query_allowed: true
    query_priority: low
    attribution_anchor: none
    independent_attribution_allowed: false
```

Aliases of three characters or fewer SHALL default to `short_acronym` or
`ambiguous_short_acronym` unless an explicit configuration override documents why
the alias is uniquely identifying. `GM` SHALL be configured as an ambiguous short
alias for General Motors in third-party document attribution.

### 9.8.2 Personal-initial and bibliography collision rule

The following SHALL NOT satisfy a company alias match:

- punctuation-separated personal initials such as `G.M.`;
- initials occurring as part of an author/editor name;
- bibliography, References, Works Cited, or citation-list occurrences alone;
- DOI metadata, author metadata, or citation metadata that does not identify the
  target company as an author affiliation, subject, partner, or owner;
- search-provider snippets when the retrieved content does not confirm the same
  relationship.

The implementation SHALL preserve the lexical match for audit purposes with a
reason code, but set its attribution strength to zero.

### 9.8.3 General industry background

A source may be highly relevant to the Tiny-AI/NNC technology domain while being
unrelated to the scanned company. Such a document SHALL be represented as:

```yaml
source_attribution_scope: general_industry_background
company_attribution_status: not_established
mapping_eligible: false
score_contribution: 0
relevant_evidence_eligible: false
```

Background sources MAY support taxonomy maintenance, query expansion, market
education, or separate research artifacts. They SHALL NOT support claims about
the target company's activities, engineering needs, deployment status, or sales
opportunity.


# 10. Search Profiles and Provider Execution Policy

Search profiles SHALL combine company identity, domain terms, use-case terms,
target terms, deployment terms, and evidence-type terms.

## 10.1 Mandatory query families

Every production scan SHALL prepare queries from these families:

1. company plus neural-network application;
2. company plus embedded AI or edge AI;
3. company plus TinyML or microcontroller;
4. company plus ONNX;
5. company plus neural-network code generation;
6. company plus virtual sensor or soft sensor;
7. company plus predictive maintenance or anomaly detection;
8. company plus MCU/ECU family terms;
9. company plus quantization, INT8, pruning, or resource optimization;
10. company plus RAM, ROM, flash, stack, latency, power, or execution time;
11. company plus MIL, SIL, PIL, back-to-back, or equivalence;
12. company plus ISO 26262, ISO/PAS 8800, MISRA, or functional safety;
13. company plus publications, white papers, research, patents, careers, or
    technical presentations;
14. site-restricted official-domain queries;
15. PDF-focused queries;
16. **use-case-led discovery** generated from the industry-weighted NNC use-case
    taxonomy, including at least one query that does not require an ML/NN term;
17. **engineering-ecosystem publisher discovery** for approved technical
    publishers, conferences, customer-story repositories, and proceedings;
18. **patented applied-ML discovery** using patent-native assignee
    enumeration, local use-case taxonomy matching, patent classifications,
    company legal names/brands, validated patent assignees, and supplemental
    patent-host-restricted web queries.

At least one enabled provider SHALL execute every mandatory query family. The
use-case-led family SHALL receive a reserved share of the query budget and SHALL
not be dropped merely because direct NNC queries consume the general query cap.

Default query-budget allocation SHOULD be:

```yaml
query_budget_allocation:
  direct_nnc_and_deployment: 0.30
  use_case_led_discovery: 0.25
  engineering_publisher_discovery: 0.15
  patented_applied_ml_discovery: 0.20
  research_careers_and_other: 0.10
```

The implementation MAY rebalance unused general-web slots, but ordinary web
queries SHALL be supplemental to patent-native enumeration.

The patent budget SHALL be separate from the general-web query budget:

```yaml
patent_discovery_budget:
  maximum_metadata_records_per_assignee: 500
  maximum_metadata_records_per_native_source: 500
  maximum_pages_per_assignee_source: 20
  maximum_results_per_supplemental_web_query: 50
  maximum_pages_per_supplemental_web_query: 5
  maximum_full_patents_retrieved_per_company: 100
  maximum_family_expansion_records: 200
  maximum_citation_expansion_records: 100
```

Metadata enumeration is inexpensive relative to complete patent retrieval and
SHALL not consume the ordinary webpage/PDF retrieval budget.

A normal company scan SHALL still execute supplemental patent queries, but
success of the patent family SHALL be determined primarily by patent-native
corpus coverage and result quality.

## 10.2 Profile tiers

```yaml
search_profile_tiers:
  tier_1_direct:
    description: Explicit NN plus embedded target or ONNX evidence
    priority: highest
  tier_2_application:
    description: High-value use cases likely to contain deployable neural models
    priority: high
  tier_3_resource_and_verification:
    description: Resource, code-generation, target, safety, and verification evidence
    priority: high
  tier_4_research_and_organization:
    description: Research papers, patents, jobs, teams, and collaborations
    priority: medium

  tier_2b_professional_applied_ml_publication:
    description: Target-company-authored or affiliated professional technical publications with concrete applied ML use cases
    priority: high
    source_category: professional_applied_ml_publication

  tier_2c_target_company_patent:
    description: Target-company or validated-assignee patent with concrete ML/data-driven physical-system application
    priority: high
    source_category: target_company_patent
  tier_5_adjacent_and_negative:
    description: Generic AI, cloud-only, non-neural, competitor, or silicon-capability context
    priority: lower
```

## 10.3 Additive discovery

Candidate discovery SHALL combine, never choose between:

- explicit seeds;
- official homepage;
- DDGS;
- Brave;
- SerpAPI;
- Serper;
- official sitemaps;
- internal crawling;
- official publication hubs;
- discovered PDFs;
- Semantic Scholar;
- GitHub;
- patent-native assignee enumeration;
- patent-native metadata and classification search;
- general-web patent discovery;
- approved third-party technical sources.

## 10.4 Company source profile

A company-specific source profile MAY declare:

```yaml
company_id: example_mobility
official_domains:
  - example.com
approved_asset_domains:
  - assets.example.com
publication_hubs:
  - https://example.com/research
  - https://example.com/technology
seed_urls: []
known_hardware_terms:
  - S32K3
known_use_case_terms:
  - battery state of charge
known_research_partners: []
validated_patent_assignees:
  - assignee_name: Example Mobility Global Technology Operations LLC
    validation_status: established
patent_discovery_profile:
  enabled: true
  industry_baseline: automotive
  preferred_native_sources:
    - google_patents
    - justia_patents
    - uspto_patent_data
    - epo_ops
```

Seeds SHALL be registered before budget filtering and SHALL receive protected
retrieval priority.


## 10.5 Patent-native discovery is primary

For companies with one or more validated patent assignees, the production scan
SHALL execute patent-native assignee enumeration before relying on ordinary
web-search ranking for patent discovery.

```yaml
patent_discovery_mode:
  primary: patent_native_assignee_corpus
  supplemental:
    - general_web_site_restricted_queries
    - specialist_search_provider_queries
```

If patent-native enumeration is technically unavailable, the run SHALL record a
degraded-mode reason. It SHALL not silently report patent discovery as complete.

## 10.6 Two-stage patent retrieval

Patent processing SHALL separate inexpensive metadata discovery from expensive
full-text retrieval.

### Stage A — metadata corpus

Enumerate and persist, when available:

```yaml
patent_metadata_record:
  source_provider: google_patents
  source_record_id: <provider-specific-id>
  patent_url: <recognized-patent-url>
  publication_number: <normalized-publication-number>
  application_number: <normalized-application-number-or-null>
  title: <title>
  abstract: <abstract-or-null>
  current_assignees: []
  original_assignees: []
  inventors: []
  filing_date: <date-or-null>
  publication_date: <date-or-null>
  grant_date: <date-or-null>
  legal_status: <status-or-null>
  classifications:
    cpc: []
    ipc: []
  patent_family_id: <family-id-or-null>
  cited_patent_ids: []
  citing_patent_ids: []
  related_application_ids: []
  metadata_complete: <boolean>
```

### Stage B — selected full text

After local ranking and family reservations, retrieve complete text only for
selected records:

- abstract;
- claims;
- detailed description;
- drawings captions where textually available;
- assignee and legal-status metadata;
- classifications;
- patent-family/related-application links.

The metadata corpus SHALL remain available for audit even when a record is not
selected for full-text retrieval.

## 10.7 Assignee enumeration sources

The design SHALL support configurable patent-native sources with capability
validation. Examples include:

```yaml
patent_native_sources:
  google_patents:
    required_capabilities:
      - assignee_enumeration
      - pagination_or_bounded_result_expansion
      - patent_metadata
      - full_text_location

  justia_patents:
    required_capabilities:
      - assignee_pages
      - pagination
      - patent_metadata

  uspto_patent_data:
    optional: true
    required_capabilities:
      - assignee_search
      - structured_patent_metadata

  epo_ops:
    optional: true
    required_capabilities:
      - bibliographic_search
      - patent_family_or_classification_data
```

Availability and exact backend implementation MAY vary. The BDA SHALL validate
capabilities at preflight rather than assume that a configured source is
functional.

A general search provider returning `patents.google.com` links is not equivalent
to assignee enumeration.

# 11. Query Generation and Provider Routing

Search-query generation and execution SHALL be separate and auditable.

## 11.1 Query object

```json
{
  "query_id": "QRY-00001",
  "family_id": "embedded_neural_network",
  "query_text": ""Example Mobility" neural network embedded ECU",
  "target_company_id": "example_mobility",
  "required": true,
  "preferred_providers": ["ddgs", "brave"],
  "generated_at_utc": "2026-07-28T12:00:00Z",
  "execution_status": "planned"
}
```

## 11.2 Deterministic templates

Example templates:

```yaml
query_templates:
  direct_nn:
    - '"{company_name}" ("neural network" OR "deep learning") (embedded OR ECU OR microcontroller)'
    - 'site:{official_domain} ("neural network" OR ONNX)'

  use_case:
    - '"{company_name}" ("virtual sensor" OR "soft sensor")'
    - '"{company_name}" ("predictive maintenance" OR "anomaly detection") AI'

  hardware:
    - '"{company_name}" ({hardware_term}) ("neural network" OR AI)'
    - 'site:{official_domain} ({hardware_term}) filetype:pdf'

  deployment:
    - '"{company_name}" (ONNX OR "code generation") (C OR C++)'
    - '"{company_name}" (quantization OR INT8 OR RAM OR ROM OR stack OR latency)'

  verification:
    - '"{company_name}" ("back-to-back" OR MIL OR SIL OR PIL)'
    - '"{company_name}" ("ISO 26262" OR "ISO/PAS 8800" OR MISRA) AI'

  patent_applied_ml:
    - '"{company_legal_name}" patent "machine learning"'
    - '"{company_search_brand}" patent "machine learning"'
    - '"{company_search_brand}" patent "state estimation"'
    - '"{company_search_brand}" patent regression classification'
    - 'site:patents.google.com/patent "{company_legal_name}" "machine learning"'
    - 'site:patents.google.com/patent "{validated_patent_assignee}" "machine learning"'
    - 'site:patents.google.com/patent "{validated_patent_assignee}" "{selected_high_priority_use_case_term}"'
    - 'site:patents.justia.com "{validated_patent_assignee}" "machine learning"'

  research:
    - '"{company_name}" ("neural network" OR TinyML) (paper OR publication OR patent OR thesis)'

  applied_ml_research:
    - '"{company_search_brand}" ("machine learning" OR "supervised learning" OR "data-driven") (vehicle OR automotive OR telematics OR ADAS OR estimator OR "virtual sensor" OR "soft sensor")'
    - '"{company_search_brand}" ("machine learning" OR "data analytics" OR AI) ("technical paper" OR paper OR publication OR conference OR DOI)'
    - 'site:saemobilus.sae.org "{company_search_brand}" ("machine learning" OR "data analytics" OR telematics OR ADAS)'
    - 'site:sae.org "{company_search_brand}" ("machine learning" OR "data analytics" OR telematics OR ADAS)'
    - '"{company_search_brand}" ("machine learning" OR AI) DOI'

  use_case_led_battery:
    - '"{company_search_brand}" ("battery health" OR "state of health" OR SOH OR "battery prognostics" OR "remaining useful life")'
    - '"{company_search_brand}" ("battery health" OR "state of health" OR SOH OR "battery management" OR BMS) ("machine learning" OR AI OR "neural network" OR "deep learning" OR ANFIS OR "neuro-fuzzy")'
    - '"{company_search_brand}" ("battery capacity" OR "battery aging" OR "battery degradation") (estimation OR prediction OR prognostics)'
    - '"{company_search_brand}" ("state of charge" OR SOC OR "state of health" OR SOH) (estimator OR estimation OR prediction)'

  use_case_led_virtual_sensing:
    - '"{company_search_brand}" ("virtual sensor" OR "soft sensor" OR "sensorless estimation")'
    - '"{company_search_brand}" ("virtual sensor" OR "soft sensor") ("machine learning" OR "neural network" OR "deep learning")'

  use_case_led_condition_monitoring:
    - '"{company_search_brand}" ("condition monitoring" OR prognostics OR "remaining useful life" OR "predictive maintenance")'
    - '"{company_search_brand}" ("condition monitoring" OR prognostics) ("machine learning" OR "neural network" OR AI)'

  engineering_publisher_mathworks:
    - 'site:mathworks.com "{company_search_brand}" ("battery health" OR "state of health" OR "virtual sensor" OR "soft sensor" OR prognostics)'
    - 'site:mathworks.com/content/dam "{company_search_brand}" (battery OR estimator OR monitoring OR prediction)'
    - 'site:mathworks.com/company/user_stories "{company_search_brand}"'
    - 'site:mathworks.com "{company_search_brand}" ("MATLAB EXPO" OR "Automotive Conference")'

  engineering_publisher_sae:
    - 'site:saemobilus.sae.org "{company_search_brand}" ("machine learning" OR battery OR estimator OR "virtual sensor" OR telematics)'
    - 'site:sae.org "{company_search_brand}" ("machine learning" OR battery OR estimator OR "virtual sensor" OR telematics)'

  company_affiliation_research:
    - '"{company_search_brand}" (research OR R&D OR engineering) ("machine learning" OR AI) (paper OR SAE OR conference)'
```

## 11.3 Query expansion


### REQ-SEARCH-PATENT-INDUSTRY-001 — Industry baseline patent families

Patent discovery SHALL not depend solely on previously discovered company
evidence. Each industry profile SHALL provide baseline NNC-relevant patent
use-case families that are always considered.

```yaml
industry_baseline_patent_use_cases:
  automotive:
    minimum_selected_families: 5
    families:
      - battery_virtual_measurement_and_predictive_control
      - vehicle_dynamics_learned_estimation
      - indirect_physical_state_and_virtual_sensing
      - condition_monitoring_and_prognostics
      - perception_classification_and_detection
      - occupant_driver_cabin_sensing

  off_highway:
    minimum_selected_families: 4
    families:
      - vehicle_dynamics_learned_estimation
      - indirect_physical_state_and_virtual_sensing
      - battery_virtual_measurement_and_predictive_control
      - condition_monitoring_and_prognostics

  energy:
    minimum_selected_families: 4
    families:
      - battery_virtual_measurement_and_predictive_control
      - condition_monitoring_and_prognostics
      - anomaly_detection
      - virtual_and_soft_sensing

  aerospace:
    minimum_selected_families: 4
    families:
      - battery_virtual_measurement_and_predictive_control
      - indirect_physical_state_and_virtual_sensing
      - condition_monitoring_and_prognostics
      - perception_classification_and_detection
```

Company-specific accepted evidence MAY increase or reorder these families but
SHALL NOT eliminate the industry baseline.

This prevents a company such as an automotive OEM from receiving no battery
patent queries merely because the current scan has not yet discovered a battery
program.


### REQ-SEARCH-PATENT-TERM-COVERAGE-001 — Required term coverage

The implementation SHALL NOT select only the first term from a use-case family.

Each patent use-case family SHALL distinguish:

```yaml
term_coverage:
  required_core_terms: []
  optional_expansion_terms: []
  semantic_only_terms: []
```

Rules:

1. every `required_core_term` SHALL be applied independently to the local patent
   metadata corpus;
2. every `required_core_term` SHALL have its execution and match count persisted
   in `patent_term_coverage.json`;
3. supplemental web/native searches SHALL rotate through all required terms;
4. a family is incomplete when any required core term was skipped without an
   explicit budget or capability reason;
5. semantic similarity MAY supplement but SHALL NOT replace exact/synonym term
   coverage.

Default automotive required terms include:

```yaml
patent_required_core_terms:
  vehicle_dynamics_learned_estimation:
    - tractive limit
    - traction limit
    - wheel stability
    - wheel slip
    - tire saturation
    - tire-road friction
    - regression model
    - classification model

  battery_virtual_measurement_and_predictive_control:
    - predictive charging
    - dynamic charging
    - charging control
    - virtual measurement
    - calculated performance variable
    - anode voltage
    - anode potential
    - electrolyte concentration
    - lithium plating
    - neural network learning agent
```

Plural, hyphenation, spelling, and normalized lexical variants SHALL be applied
deterministically.

### REQ-SEARCH-PATENT-ASSIGNEE-001 — Validated patent-assignee profiles

The BDA SHALL maintain patent-assignee identity separately from general company
aliases.

```yaml
validated_patent_assignees:
  - assignee_name: GM Global Technology Operations LLC
    attributed_company_id: general_motors
    validation_status: established
    validation_basis:
      - authoritative_patent_metadata
      - validated_corporate_relationship
    allowed_for:
      - patent_query_generation
      - patent_company_attribution
    short_alias_rule_override: patent_assignee_context_only
```

This example is a regression fixture, not a GM-only production rule.

For every company, assignee names SHALL be stored in a validated company/source
profile rather than hard-coded into query templates.

The system SHALL support progressive assignee discovery:

```text
company legal name / brand
        ↓
patent-host search
        ↓
candidate assignee names from patent metadata
        ↓
deterministic company-relationship validation
        ↓
validated_patent_assignee
        ↓
expanded assignee-specific patent queries
```

A patent assignee MAY establish target-company attribution only when the
assignee-to-company relationship is `established`. A short acronym occurring
inside an unrelated assignee name SHALL not bypass the Version 1.2 company
identity gate.

Recommended validation evidence, in descending order:

1. official company page or corporate/legal document linking the assignee;
2. authoritative patent metadata plus a distinctive corporate-name relationship
   and corroborating patent-family/company evidence;
3. previously approved company source profile.

Unvalidated assignee suggestions MAY generate discovery queries at low priority
but SHALL NOT establish company attribution.


Expansion SHALL use normalized aliases but avoid combinatorial explosion.
Queries SHOULD combine at most:

- one company identifier;
- one primary technical concept;
- one deployment, hardware, use-case, or evidence-type modifier.

The pipeline SHALL cap generated queries according to the configured budget.

`company_search_brand` is a discovery-only identifier derived deterministically
from the canonical/legal company name and approved brand aliases. It MAY be
broader than an attribution anchor. For example, a distinctive brand token may
be used to find papers whose author affiliation names a corporate research
center rather than the legal entity. Discovery use of `company_search_brand`
SHALL never by itself establish source attribution.

The `applied_ml_research` family SHALL be mandatory for every production company
scan. At least one SAE/technical-publication-oriented query and one generic
applied-ML query SHALL be executed through DDGS or another enabled general web
provider even when Semantic Scholar is available. A Semantic Scholar 429, quota
exhaustion, or provider outage SHALL NOT suppress these web-search fallbacks.

### REQ-SEARCH-USECASE-001 — Use-case query ladder

For each selected high-priority use-case family, the BDA SHALL execute a bounded
query ladder. The first rung SHALL not require a neural/ML term:

```yaml
use_case_query_ladder:
  rung_1_application_only:
    required: true
    example: '"{company_search_brand}" "battery health monitoring"'
  rung_2_application_plus_ml:
    required: true
    example: '"{company_search_brand}" ("battery health" OR SOH) ("machine learning" OR "neural network" OR ANFIS)'
  rung_3_application_plus_publication:
    required: true
    example: '"{company_search_brand}" ("battery health" OR SOH) (paper OR presentation OR conference OR pdf)'
  rung_4_publisher_restricted:
    required_for_configured_publishers: true
    example: 'site:mathworks.com "{company_search_brand}" ("battery health" OR SOH)'
```

This ordering is mandatory because search-engine titles and snippets frequently
expose the application but omit the model family.

The number of selected use-case families SHALL be bounded by company industry:

```yaml
use_case_query_selection:
  maximum_families_per_company: 6
  minimum_families_per_company: 3
  maximum_queries_per_family: 4
  select_by:
    - company_industry
    - known_products_and_systems
    - previously accepted company evidence
    - NNC reference-use-case priority
```

No company-specific URL is required.

Short aliases SHALL be query-discovery aids only. For every query generated from
`short_acronym` or `ambiguous_short_acronym`, the query object SHALL record:

```yaml
company_identifier_type: ambiguous_short_acronym
company_identity_risk: high
requires_retrieved_document_identity_validation: true
```

A production scan SHALL also execute canonical/full-name query variants when the
company has a short alias. A result returned from `"GM" neural network
microcontroller`, for example, remains unverified until the retrieved source
establishes General Motors independently of the query text.

## 11.4 Provider routing

DDGS is mandatory. Optional providers SHALL be routed only when configured and
within quota. Missing credentials SHALL be detected once during cycle preflight,
not once per query.

A query persisted but not executed is not evidence of a completed search.
Unexecuted required queries SHALL produce an incomplete-search status.


Patent-search completeness SHALL additionally require:

```yaml
patent_search_acceptance:
  validated_assignee_available_or_degraded_reason_recorded: true
  native_assignee_enumeration_attempted: true
  metadata_pagination_state_recorded: true
  patent_provider_quality_validated: true
  required_term_coverage_complete_or_explained: true
  local_metadata_ranking_completed: true
  family_reservations_applied: true
  selected_full_text_patents_retrieved_or_failure_recorded: true
```

A company scan SHALL NOT report `patent_search_complete=true` when only ordinary
web-search patent queries were executed.


# 12. Search Provider Contract and Candidate Source Discovery

Every provider adapter SHALL return normalized result objects:

```json
{
  "provider_id": "ddgs",
  "query_id": "QRY-00001",
  "rank": 1,
  "title": "Example title",
  "url": "https://example.com/research/embedded-ai",
  "snippet": "Normalized search-result snippet",
  "retrieved_at_utc": "2026-07-28T12:01:00Z",
  "provider_metadata": {}
}
```

Provider adapters SHALL:

- preserve provider and query provenance;
- normalize URLs without losing the original;
- enforce timeouts, retry limits, cooldowns, and quota budgets;
- never return a successful empty result for an unimplemented adapter;
- never hide authentication, rate-limit, or parsing errors;
- avoid logging credentials;
- support cycle-shared rate-limit state where applicable.


### REQ-PATENT-PROVIDER-QUALITY-001 — Patent result validation

A result returned by a component labeled as a patent provider SHALL be accepted
as a patent result only when it contains sufficient patent identity.

```yaml
usable_patent_record:
  required_any_identifier:
    - normalized_publication_number
    - normalized_application_number
  required:
    - recognized_patent_document_or_record_url
    - title_or_abstract
  target_company_relevance_required_any:
    - validated_target_assignee
    - candidate_assignee_for_validation
  source_capability_required:
    - patent_native_enumeration_or_search
```

Recognized patent records MAY originate from configured patent-native databases
or official patent authorities. A job advertisement, career page, news page,
generic company page, or ordinary web result lacking patent identity SHALL be
rejected.

```yaml
provider_result_quality:
  status: unusable
  reason_code: non_patent_results_from_patent_provider
  fallback_required: true
```

The provider-quality artifact SHALL report:

```yaml
patent_provider_quality_metrics:
  raw_result_count: 0
  usable_patent_record_count: 0
  target_assignee_record_count: 0
  taxonomy_signal_record_count: 0
  rejected_non_patent_count: 0
  rejected_missing_identifier_count: 0
  pagination_complete: false
  capability_validation_status: pass_or_fail
```

An adapter returning only non-patent pages SHALL fail capability validation.

### REQ-PATENT-FALLBACK-QUALITY-001 — Quality-based fallback

A patent query or discovery route SHALL not be considered successful merely
because it returned one or more URLs.

For supplemental web queries, a result set is useful only when at least one
record satisfies:

```yaml
usable_supplemental_patent_result:
  recognized_patent_document: true
  target_assignee_signal: true
  application_or_taxonomy_signal: true
```

If DDGS returns ten irrelevant patents or non-patent pages, the result is
equivalent to zero useful results for that query family and SHALL trigger the
next configured provider.

For native assignee enumeration, success requires:

```yaml
native_enumeration_success:
  provider_capability_validated: true
  assignee_query_executed: true
  records_normalized: true
  pagination_terminated_by:
    one_of:
      - end_of_results
      - configured_budget
      - provider_limit
```

The BDA SHALL separately record `raw_results_returned` and
`usable_results_returned`.

Candidate registration SHALL keep scan provenance separate from source
attribution. The normalized candidate object SHALL contain, at minimum:

```json
{
  "candidate_id": "SRC-00001",
  "scan_target_company_id": "general_motors",
  "discovery_query_id": "QRY-00017",
  "discovery_company_identifier": "GM",
  "discovery_company_identifier_type": "ambiguous_short_acronym",
  "url": "https://example.edu/tinyml-paper.pdf",
  "company_attribution": {
    "status": "unverified",
    "attributed_company_id": null,
    "anchor_types": [],
    "reason_codes": []
  }
}
```

The implementation SHALL NOT unconditionally write the current scan's company
name into a source-level factual field. Legacy fields named `company_name` in
candidate artifacts SHALL either be renamed `scan_target_company_name` or
explicitly documented as scan provenance and SHALL never be consumed as
attribution evidence.

Search-provider return of a URL SHALL mean only `candidate_for_scan=true`.
Provider relevance, query-term matching, or provider snippets SHALL not establish
that the document belongs to or discusses the target company.

Candidate-source discovery SHALL assign one or more discovery channels:

```yaml
discovery_channel:
  - explicit_seed
  - homepage
  - search_result
  - sitemap
  - internal_link
  - publication_hub
  - discovered_pdf
  - semantic_scholar
  - github
  - patent
  - approved_third_party
```

Candidate ranking SHALL prioritize retrieval value, not merely host class.

After protected seed handling required by the inherited PwEl architecture,
ordinary candidates SHALL receive a deterministic pre-retrieval score based on
the search result title, snippet, URL/path, provider provenance, and query
family. The score is a retrieval-priority heuristic only; it SHALL NOT establish
company attribution or NNC applicability.

Recommended default components:

```yaml
candidate_retrieval_priority:
  target_company_identity_signal:
    canonical_or_legal_name_in_title_or_snippet: 35
    distinctive_brand_plus_r_and_d_unit: 30
    approved_official_domain: 25
    ambiguous_short_alias_only: 0

  use_case_signal:
    high_priority_nnc_use_case_in_title: 30
    high_priority_nnc_use_case_in_snippet: 20
    technical_action_term_in_title_or_snippet: 10

  model_signal:
    explicit_neural_or_deep_learning: 25
    patent_claimed_optional_neural_embodiment: 22
    hybrid_neural_term_ANFIS_ANFC_neuro_fuzzy: 22
    generic_machine_learning: 10
    regression_plus_classification_physical_estimation: 15
    neural_learning_agent_or_neural_estimator: 25
    hybrid_physics_data_driven_estimator: 18
    virtual_or_latent_physical_variable_estimation: 20
    predictive_battery_charging_or_battery_health_control: 20

  embedded_signal:
    ECU_or_MCU_or_onboard_or_real_time: 15

  source_type_signal:
    explicit_target_company_author_affiliation_in_search_metadata: 35
    professional_applied_ml_publication: 30
    primary_technical_paper_or_presentation: 25
    customer_story_or_engineering_case_study: 18
    conference_or_proceedings_pdf: 18
    target_company_patent_with_validated_assignee: 30
    active_granted_patent: 10
    patent: 12

  technical_publisher_signal:
    configured_engineering_ecosystem_publisher: 20

  negative_priority:
    owner_or_operator_manual: -25
    generic_annual_report_without_technical_signal: -15
    generic_marketing_aggregator: -20
```

A source such as `Intelligent System for Battery Health Monitoring` can therefore
rank highly from `company identity + battery/SOH use case + technical
presentation + engineering publisher` even before the provider snippet reveals
`ANFIS` or `neural network`.

The selector SHALL also enforce diversity quotas so broad corporate documents
cannot consume the whole retrieval budget:

```yaml
candidate_selection_diversity:
  minimum_if_available:
    use_case_led_candidates: 6
    primary_technical_publications_or_presentations: 4
    engineering_publisher_candidates: 3
    target_company_patent_candidates_from_native_corpus: 10
  maximum_share:
    owner_service_operator_manuals: 0.10
    annual_reports_and_generic_corporate_pages: 0.20
```

These are default policy values and MAY be tuned through validated YAML.

A candidate URL limit SHALL be applied only after additive discovery,
canonicalization, deduplication, protected-seed reservation, scoring, and
diversity-slot allocation.


## 12.1 Engineering-ecosystem publisher profiles

The search configuration SHALL support publisher profiles that describe
high-yield repositories for applied engineering evidence. Publisher profiles do
not imply target-company attribution.

Example:

```yaml
engineering_publisher_profiles:
  mathworks:
    domains:
      - mathworks.com
    path_patterns:
      - /company/user_stories/
      - /content/dam/
      - /company/events/
      - /solutions/
    evidence_types:
      - customer_story
      - technical_presentation
      - conference_material
      - application_note
    query_terms:
      - MATLAB EXPO
      - Automotive Conference
      - customer story
      - case study
    retrieval_priority_bonus: 15

  sae:
    domains:
      - saemobilus.sae.org
      - sae.org
    preferred_search_paths:
      - saemobilus.sae.org/papers
    evidence_types:
      - technical_paper
      - conference_paper
      - professional_publication
    source_category: professional_applied_ml_publication
    retrieval_priority_bonus: 20
    query_policy:
      atomic_queries_required: true
      nested_boolean_queries_preferred: false
      zero_result_provider_fallback: true
```

Other engineering publishers MAY be configured using the same schema. The
publisher profile SHALL be global and reusable across companies.

A publisher-domain bonus SHALL never bypass `company_attribution.status ==
established`.


### Patent-host profiles

```yaml
patent_source_profiles:
  google_patents:
    domains:
      - patents.google.com
    source_category: target_company_patent
    retrieval_priority_bonus: 25
    parse_fields:
      - publication_number
      - title
      - current_assignee
      - original_assignee
      - inventors
      - filing_date
      - publication_date
      - legal_status
      - prior_art_keywords
      - classifications
      - abstract
      - description
      - claims

  justia_patents:
    domains:
      - patents.justia.com
    source_category: target_company_patent
    retrieval_priority_bonus: 20
    parse_fields:
      - patent_number
      - title
      - assignee
      - inventors
      - abstract
      - classifications
      - patent_history
```

Patent-host status does not establish target-company attribution. The parsed
assignee must pass the validated patent-assignee relationship gate.


### Patent-classification expansion

Patent classification metadata SHALL be used as a secondary discovery channel.
The following examples SHALL be configurable taxonomy mappings rather than
hard-coded company rules:

```yaml
patent_classification_taxonomy:
  battery_monitoring_and_control:
    codes:
      - B60L58/10
      - B60L58/12
      - B60L58/16
      - G01R31/36
      - G01R31/367
      - G01R31/392
      - H02J7/84
      - H02J7/90
      - G05B13/048
    maps_to:
      - battery_health_and_state_estimation
      - battery_virtual_measurement_and_predictive_control

  machine_learning:
    codes:
      - G06N20/00
    maps_to:
      - generic_machine_learning
```

When a retrieved target-company patent has a high-value classification, the BDA
SHOULD enqueue bounded sibling searches using:

```text
"{validated_patent_assignee}" "<classification-code>"
site:patents.google.com/patent "{validated_patent_assignee}" "<classification-code>"
```

Sibling discovery SHALL be bounded by the patent query and candidate budgets and
shall not require any seed URL.


### Patent-native assignee corpus construction

For every validated assignee, the BDA SHALL create a deduplicated metadata
corpus before full-text retrieval.

```yaml
patent_assignee_corpus:
  attributed_company_id: <company-id>
  validated_assignee_names: []
  enumeration_sources: []
  records_before_deduplication: 0
  records_after_deduplication: 0
  patent_families: 0
  earliest_publication_date: null
  latest_publication_date: null
  enumeration_complete: false
  degraded_reasons: []
```

Deduplication SHALL use publication/application number, patent-family identity,
and normalized title/assignee/date metadata. Different jurisdictions and family
members SHALL retain provenance even when collapsed for ranking.

### Local patent metadata ranking

All normalized patent metadata SHALL be searched and ranked locally before
complete patent retrieval.

The authoritative pre-retrieval rank SHALL be deterministic and may combine:

```yaml
local_patent_rank:
  exact_required_use_case_term: 30
  synonym_or_normalized_variant: 24
  title_match: 20
  abstract_match: 15
  validated_assignee_exact_match: 35
  explicit_machine_learning_term: 18
  explicit_neural_network_term: 24
  regression_or_classification_model: 15
  onboard_or_controller_context: 15
  high_value_CPC_or_IPC_match: 15
  active_or_pending_status: 5
  same_family_duplicate_penalty: -20
```

`bge-large` semantic similarity MAY be used as a secondary rank or recall aid,
but exact required-term coverage and deterministic scores SHALL remain
auditable and SHALL not be replaced by an opaque semantic rank.

### Family-specific full-text reservations

The patent full-text retrieval budget SHALL reserve capacity by use-case family
so one popular category cannot consume all patent slots.

Default automotive reservations for a maximum of 100 full patents:

```yaml
patent_full_text_reservations:
  battery_virtual_measurement_and_predictive_control: 20
  vehicle_dynamics_learned_estimation: 20
  indirect_physical_state_and_virtual_sensing: 15
  condition_monitoring_and_prognostics: 15
  perception_classification_and_detection: 10
  occupant_driver_cabin_sensing: 5
  cross_family_highest_ranked: 15
```

Unused family slots MAY flow to the cross-family pool. A family reservation
SHALL select distinct patent families where possible.

### Patent-family and neighborhood expansion

After a high-ranking target-assignee patent is found, the BDA SHALL perform
bounded expansion through patent-native relationships:

```yaml
patent_neighborhood_expansion:
  channels:
    - same_patent_family
    - related_applications
    - continuations_or_divisionals
    - cited_patents
    - citing_patents
    - same_assignee_same_CPC
    - same_assignee_neighboring_CPC
  target_company_filter:
    same_assignee_required_for_primary_company_evidence: true
  budgets:
    maximum_family_members_per_seed_record: 10
    maximum_cited_records_per_selected_patent: 10
    maximum_citing_records_per_selected_patent: 10
    maximum_neighboring_class_records_per_family: 20
```

The word `seed` in the internal graph-expansion sense means a selected corpus
record, not a user-supplied production seed URL. Regression acceptance SHALL
continue to prohibit use of the known GM URLs or publication numbers as
production discovery inputs.

Cited third-party patents MAY be retained as technology background but SHALL
not become target-company evidence unless their own assignee attribution passes.

### Target-company patent classification

A retrieved patent MAY be classified as:

```yaml
source_category: target_company_patent

qualification:
  patent_assignee_attribution: established
  applied_method_any:
    - machine_learning
    - regression_model
    - classification_model
    - neural_network
    - hybrid_neural
    - learned_estimator
  application_context_any:
    - sensing_or_estimation
    - control
    - diagnostics
    - prognostics
    - condition_monitoring
    - vehicle_dynamics
    - battery_or_energy_state
    - embedded_adjacent
    - onboard_processing
```

Patent status SHALL affect retrieval/display priority, not whether the technical
evidence exists:

```yaml
patent_status_priority:
  active_granted: highest
  pending_published_application: high
  expired_or_lapsed_but_technically_relevant: medium
  abandoned_application: low
```

If a patent confirms a target-company ML method and embedded/onboard application
but the neural network is only an optional claimed embodiment:

```yaml
relevance_class: nnc_opportunity_evidence
relevant_evidence: true
mapping_eligible: false
score_contribution: 0
```

The report SHOULD state that a neural-network option is explicitly claimed while
the selected production implementation remains unconfirmed.

### Professional applied-ML publication classification

After retrieval and attribution, a source MAY be classified as:

```yaml
source_category: professional_applied_ml_publication

qualification:
  target_company_attribution: established
  applied_method:
    one_of:
      - machine_learning
      - neural_network
      - deep_learning
      - hybrid_neural
      - data_driven_model
  application_context:
    one_or_more:
      - physical_system
      - sensing_or_estimation
      - control_or_ADAS
      - diagnostics
      - prognostics
      - condition_monitoring
      - vehicle_dynamics
      - embedded_adjacent
      - telematics
```

This category SHALL receive high candidate/retrieval priority. It is not by
itself mapping-eligible NNC evidence.

If the method is only generic ML and no neural architecture or embedded
execution is disclosed:

```yaml
relevance_class: nnc_opportunity_evidence
relevant_evidence: true
mapping_eligible: false
score_contribution: 0
```

# 13. URL and Document Deduplication

The system SHALL deduplicate at four levels:

1. URL;
2. retrieved document;
3. passage;
4. evidence object.

Canonical URL processing SHALL:

- lowercase host names;
- remove fragments;
- remove known tracking parameters;
- normalize default ports;
- resolve safe relative links;
- preserve query parameters that change document identity;
- retain original URL and discovery provenance.

Document deduplication SHALL use normalized-content hashes in addition to URL
identity. Mirrored PDFs and duplicate official/asset-domain copies MAY be
collapsed while retaining all source URLs.

Passage deduplication SHALL use exact and near-duplicate checks. Evidence
deduplication SHALL preserve the strongest source, all supporting sources, and
the provenance of merged candidates.


# 14. Web and PDF Retrieval

The retriever SHALL support HTML, XML, plain text, and PDF.

HTML parsing SHALL extract:

- title;
- canonical URL;
- headings;
- main text;
- tables where feasible;
- metadata;
- publication date where available;
- links to approved internal and asset domains.

PDF parsing SHALL:

- download within configured file-size limits;
- validate content type and file signature;
- compute a binary hash;
- extract page-aware text;
- preserve page number;
- identify embedded URLs where feasible;
- create deterministic passages;
- record parser and parser-version metadata.

The normal retriever SHALL parse web-discovered PDFs; PDF discovery is not
sufficient without PDF retrieval and parsing.

Failures SHALL be represented as:

```yaml
retrieval_status:
  - success
  - blocked
  - timeout
  - rate_limited
  - not_found
  - invalid_content
  - unsupported_format
  - parse_failed
  - file_too_large
```

A retrieval failure SHALL not invalidate immutable seed registration.


# 15. Page Relevance Determination

Page relevance SHALL be calculated deterministically before evidence extraction.

## 15.1 Relevance dimensions

Company identity SHALL be evaluated as a **hard precondition**, not as a
weighted relevance feature that stronger technical keywords can compensate for.

```yaml
page_relevance_preconditions:
  target_company_attribution:
    gate: hard
    required_for_target_company_evidence: true

page_relevance_dimensions_after_identity_gate:
  neural_network_specificity:
    weight: 0.22
  embedded_target_specificity:
    weight: 0.17
  deployment_workflow_specificity:
    weight: 0.17
  use_case_specificity:
    weight: 0.11
  resource_or_optimization_specificity:
    weight: 0.11
  verification_or_safety_specificity:
    weight: 0.11
  source_quality:
    weight: 0.11
```

The technical relevance weights SHALL be configurable and sum to 1.0. A failed
company-attribution gate SHALL prevent target-company evidence extraction no
matter how high the technical relevance score would otherwise be.

## 15.1.1 Document-level company-attribution gate

Before page/passages are scored for NNC relevance, Python SHALL determine the
source-to-company relationship.

```yaml
target_company_attribution_gate:
  pass_if_any:
    - retrieved_host_is_official_company_domain
    - retrieved_host_is_approved_affiliate_or_asset_domain
    - canonical_or_legal_company_name_in_substantive_content
    - explicit_target_company_author_affiliation
    - explicit_target_company_as_subject_or_deployer
    - explicit_validated_partner_relationship_to_target_company
  never_sufficient_alone:
    - query_contains_company_name_or_alias
    - provider_returned_result_for_company_query
    - candidate_registered_during_company_scan
    - search_result_snippet_only
    - ambiguous_short_alias
    - personal_initials
    - bibliography_or_reference_occurrence_only
    - generic_product_or_industry_similarity
```

For third-party academic papers and proceedings, the canonical/legal company name
or an explicit company relationship SHALL appear in substantive content,
author-affiliation metadata, acknowledgements, project description, or reliable
publication metadata. An ambiguous short alias alone SHALL fail.

### 15.1.1 Corporate organizational-unit affiliation resolution

Author-affiliation metadata SHALL be evaluated before rejecting a third-party
technical publication. The BDA SHALL support corporate research centers, design
centers, software centers, laboratories, engineering centers, and similarly
named organizational units even when the exact unit name is absent from
`Companies.xlsx`.

```yaml
corporate_organizational_unit_resolution:
  recognized_unit_patterns:
    - research valley
    - research centre
    - research center
    - research and development
    - R&D
    - advanced research
    - technology centre
    - technology center
    - technical centre
    - technical center
    - engineering centre
    - engineering center
    - innovation centre
    - innovation center
    - design studio
    - design center
    - design centre
    - software defined vehicle centre
    - software defined vehicle center
    - laboratory
    - labs
  pass_if:
    - distinctive_company_brand_token_present_in_affiliation_and_unit_pattern_present
    - exact_unit_relationship_confirmed_by_official_company_source
    - publisher_metadata_explicitly_links_unit_to_target_legal_entity
  ambiguous_brand_behavior:
    require_official_company_corroboration: true
  output_anchor_type: corporate_organizational_unit_affiliation
  attribution_strength: strong
```

A distinctive company brand token is one whose alias-risk policy is not
`ambiguous_short_acronym` and whose match is a lexical organization name, not
personal initials. Thus an affiliation such as `Mahindra Research Valley` can be
resolved generically from the distinctive `Mahindra` brand token plus the
`research valley` organizational-unit pattern. An affiliation such as `GM Lab`
would still require independent corroboration because `GM` is an ambiguous short
acronym.

Failure behavior:

```yaml
company_attribution_gate_failure:
  set_company_attribution_status: not_established
  set_source_attribution_scope: general_industry_background
  emit_target_company_evidence: false
  mapping_eligible: false
  score_contribution: 0
  relevant_evidence_eligible: false
  reason_code: target_company_not_established
```

## 15.2 Co-occurrence and context-bundle rules

High relevance requires local semantic co-occurrence, not company-wide term
aggregation. The implementation SHALL construct a `context_bundle` around a
single named technical subject, such as a model, function, ECU feature, virtual
sensor, research project, product subsystem, or deployment workflow.

A mapping-eligible context bundle SHALL contain all three mandatory dimensions:

1. **neural-model evidence** — an explicit neural network, deep-learning
   architecture, ONNX neural graph, or unambiguous neural model;
2. **embedded-target evidence** — an MCU, ECU, Cortex-M/R, bare-metal/RTOS
   controller, or similarly constrained embedded target; and
3. **deployment/workflow evidence** — inference on target, model conversion,
   generated or implemented C/C++, runtime integration, resource optimization,
   model-to-code verification, or a clearly stated embedded deployment intent.

Permitted locality modes, in descending strength, are:

```yaml
context_locality_modes:
  passage_local:
    description: all mandatory dimensions occur in one passage or table row
    max_normalized_tokens: 800
  section_local:
    description: dimensions occur under the same heading and refer to the same named subject
    max_normalized_tokens_between_first_and_last: 1600
    max_pdf_page_span: 3
  document_project_local:
    description: dimensions occur in one document and are joined by the same stable project/system/model anchor
    require_shared_anchor: true
    max_pdf_page_span: 10
  cross_document_project_linked:
    description: exceptional mode for two primary sources explicitly naming the same project/system/model
    require_exact_or_validated_anchor_match: true
    require_explicit_relationship: true
    default_enabled: false
```

`document_project_local` SHALL NOT mean that arbitrary terms anywhere in a long
document can be combined. Shared company ownership, a common domain, or a generic
word such as `vehicle`, `ECU`, `AI`, or `system` is not a valid anchor.

Examples of mapping-eligible patterns:

```yaml
high_relevance_patterns:
  - must_cooccur_in_context_bundle:
      - neural_network_term
      - mcu_or_ecu_term
      - deployment_workflow_term
  - must_cooccur_in_context_bundle:
      - onnx_term
      - embedded_target_term
      - code_generation_or_embedded_c_term
  - must_cooccur_in_context_bundle:
      - neural_network_term
      - resource_constraint_term
      - target_execution_term
  - must_cooccur_in_context_bundle:
      - neural_network_term
      - mil_sil_pil_or_back_to_back_term
      - embedded_target_term
```

The following combinations SHALL fail locality:

- `AI` in one company publication plus `ECU` in an unrelated owner's manual;
- a neural-network research paper plus a separate generic RAM/ROM diagnostic
  document with no shared project or system anchor;
- `embedded OnStar app` in search-result text plus `ABS electronic control unit`
  in the retrieved manual;
- `quantization` in a signal-diagnostics table plus neural evidence from another
  source.

A page with `AI` in the header and `MCU` in an unrelated footer SHALL not qualify.

## 15.3 Relevance penalties

```yaml
page_relevance_penalties:
  generic_ai_marketing_only: -0.25
  cloud_only: -0.30
  gpu_server_only: -0.25
  non_neural_model_only: -0.20
  semiconductor_capability_without_company_use_case: -0.15
  direct_competitor_product_page: -0.10
  no_target_company_relationship: hard_reject_for_target_company_evidence
  ambiguous_short_alias_only: hard_reject_for_target_company_evidence
  bibliography_initials_alias_collision: hard_reject_for_target_company_evidence
  provider_query_match_without_source_identity: hard_reject_for_target_company_evidence
  duplicate_or_syndicated: -0.10
  generic_owner_manual: -0.35
  generic_obd_diagnostic_manual: -0.35
  target_only_without_neural_context: -0.40
  cross_document_gate_mixing: -0.60
  signal_quantization_not_model_quantization: -0.50
```

## 15.4 Page classification

```yaml
page_class:
  - company_product_or_solution
  - company_research_or_publication
  - company_technical_article
  - company_career_or_team
  - company_patent
  - target_company_patent
  - partner_case_study
  - academic_publication
  - semiconductor_reference_design
  - tool_vendor_case_study
  - news_or_press_release
  - vehicle_owner_manual
  - obd_or_diagnostic_manual
  - service_or_repair_manual
  - generic_market_content
  - irrelevant
```

The classification SHALL influence source quality and interpretation but SHALL
not replace evidence-level validation.

## 15.5 Source-type promotion controls

Vehicle owner manuals, OBD diagnostic manuals, service manuals, repair manuals,
and generic controller diagnostic documents MAY remain in the candidate-source
queue because they can contain useful technical evidence. They SHALL use the
following default promotion policy:

```yaml
source_promotion_policy:
  vehicle_owner_manual:
    candidate_allowed: true
    mapping_evidence_default: false
    relevant_evidence_default: false
    override_requires:
      - explicit_neural_model_term
      - explicit_embedded_target_term
      - explicit_deployment_workflow_term
      - context_bundle_gate_pass
  obd_or_diagnostic_manual:
    candidate_allowed: true
    mapping_evidence_default: false
    relevant_evidence_default: false
    override_requires:
      - explicit_neural_model_term
      - explicit_embedded_target_term
      - explicit_deployment_workflow_term
      - context_bundle_gate_pass
  service_or_repair_manual:
    candidate_allowed: true
    mapping_evidence_default: false
    relevant_evidence_default: false
    override_requires:
      - context_bundle_gate_pass
```

An ordinary statement that a vehicle contains an `electronic control unit`,
`microcontroller`, `ASIC`, `RAM`, `ROM`, `stack`, `watchdog`, `CPU`, or `ADC` is
valid platform or diagnostic context, but it is not NNC applicability evidence.


# 16. Evidence Model

Evidence objects SHALL preserve facts, context, uncertainty, and provenance.

## 16.1 Required evidence object

```json
{
  "evidence_id": "EVD-00001",
  "scan_target_company_id": "example_mobility",
  "attributed_company_id": "example_mobility",
  "company_attribution": {
    "status": "established",
    "source_attribution_scope": "target_company",
    "anchor_types": ["canonical_full_name", "official_domain_ownership"],
    "matched_text": ["Example Mobility"],
    "reason_codes": ["target_company_identity_established"]
  },
  "entity_scope": "target_company",
  "source": {
    "canonical_url": "https://example.com/embedded-ai",
    "original_url": "https://example.com/embedded-ai?source=x",
    "source_type": "official_company_page",
    "title": "Embedded battery estimator",
    "published_date": null,
    "retrieved_at_utc": "2026-07-28T12:10:00Z",
    "content_hash": "sha256:...",
    "page_number": null
  },
  "passage": {
    "text": "Normalized source passage",
    "start_offset": 1234,
    "end_offset": 1510,
    "heading_path": ["Technology", "Battery estimator"]
  },
  "normalized_entity": {
    "target_company_entity_id": "TCE-00001",
    "entity_type": "neural_network_application",
    "use_case_class": "battery_soc_soh_estimation",
    "model_class": "lstm",
    "target_class": "automotive_ecu",
    "hardware_family": "S32K3",
    "deployment_stage": "prototype_on_target"
  },
  "assessment": {
    "status": "accepted",
    "fact_class": "confirmed_embedded_neural_network",
    "confidence": 0.91,
    "relevance_score": 0.88,
    "reason_codes": [
      "explicit_neural_architecture",
      "explicit_mcu_family",
      "embedded_execution"
    ]
  },
  "context": {
    "context_bundle_id": "CTX-00001",
    "subject_anchor": "battery SOC neural estimator",
    "locality_mode": "passage_local",
    "document_id": "DOC-00001",
    "pdf_page_span": [12, 13]
  },
  "mapping_eligibility": {
    "eligible": true,
    "neural_dimension": true,
    "embedded_target_dimension": true,
    "deployment_workflow_dimension": true,
    "source_promotion_override": false,
    "reason_codes": ["complete_local_context_bundle"]
  }
}
```

## 16.2 Fact classes

```yaml
accepted_fact_classes:
  - confirmed_neural_network_use_case
  - confirmed_embedded_inference
  - confirmed_microcontroller_or_ecu_target
  - confirmed_onnx_handover
  - confirmed_c_or_cpp_implementation
  - confirmed_code_generation
  - confirmed_runtime_library
  - confirmed_resource_constraint
  - confirmed_quantization_or_optimization
  - confirmed_mil_sil_pil_activity
  - confirmed_back_to_back_verification
  - confirmed_functional_safety_requirement
  - confirmed_company_role
  - confirmed_target_hardware
  - confirmed_model_framework
  - confirmed_research_activity
  - confirmed_generic_controller_presence
  - confirmed_signal_encoding_or_scaling
```

```yaml
inference_classes:
  - strong_inferred_model_to_embedded_handover_need
  - strong_inferred_resource_fit_need
  - strong_inferred_verification_need
  - plausible_onnx_conversion_prerequisite
  - plausible_cross_silicon_portability_need
  - plausible_safety_workflow_need
  - commercial_opportunity_inference
```

```yaml
rejection_or_limitation_classes:
  - generic_ai_only
  - neural_network_not_confirmed
  - embedded_target_not_confirmed
  - microcontroller_constraint_not_confirmed
  - cloud_or_server_only
  - gpu_only
  - non_neural_model_only
  - silicon_capability_only
  - unrelated_company
  - target_company_not_established
  - ambiguous_company_alias_only
  - bibliography_initials_alias_collision
  - provider_result_not_company_evidence
  - search_query_not_attribution
  - general_industry_background_only
  - duplicate
  - insufficient_local_context
  - research_only_no_deployment_target
  - direct_competitor_evidence
  - unsupported_or_unknown_onnx_path
  - unsupported_or_unknown_target_compatibility
  - target_only_no_neural_context
  - deployment_only_no_neural_context
  - cross_document_gate_mixing
  - generic_vehicle_manual
  - generic_obd_diagnostic_context
  - signal_quantization_not_model_quantization
  - linear_quantization_diagnostic_value
  - incomplete_context_bundle
  - evidence_not_mapping_eligible
```

## 16.3 Evidence acceptance and mapping-eligibility rules

Evidence acceptance and mapping eligibility are separate decisions. A passage
may be factually accepted while remaining ineligible for an NNC mapping.

Evidence SHALL be accepted as a factual company statement only when:

- the document-level company-attribution gate has status `established`;
- `attributed_company_id` equals the current `scan_target_company_id`;
- the target-company relationship is explicit or established by an approved official/affiliate domain;
- the quoted passage supports the normalized fact;
- local context passes ambiguity checks;
- source quality is sufficient for the claim strength;
- no exclusion overrides the claim;
- confidence meets the configured threshold.

Evidence SHALL be `mapping_eligible: true` only when:

- it belongs to a validated context bundle;
- the bundle satisfies neural-model, embedded-target, and deployment/workflow
  dimensions;
- the dimensions refer to the same named technical subject;
- the source-type promotion policy permits mapping use; and
- no negative-context override applies.

Therefore:

- `ABS electronic control unit` in an owner's manual MAY be accepted as
  `confirmed_generic_controller_presence`, but SHALL be `mapping_eligible: false`;
- RAM/ROM/stack/watchdog diagnostics MAY be accepted as controller diagnostics,
  but SHALL NOT derive static-memory, resource-estimation, or portability needs;
- `linear quantization` in a diagnostic signal table MAY be accepted as signal
  encoding, but SHALL NOT be normalized as neural-model quantization.

A third-party source MAY establish a fact when it names the company and project
clearly. Strong commercial conclusions SHOULD prefer official or primary
sources.

## 16.3.1 Quantization disambiguation

The token `quantization` SHALL have zero standalone neural relevance. It SHALL
count as `confirmed_quantization_or_optimization` only when local context
contains at least one model object and at least one precision/optimization cue.

```yaml
model_quantization_positive_context:
  model_objects:
    - neural_network
    - model
    - weights
    - activations
    - tensors
    - layers
    - onnx_graph
    - inference_model
  precision_or_method_cues:
    - INT8
    - INT16
    - FP16
    - FP32
    - low_precision
    - post_training_quantization
    - PTQ
    - quantization_aware_training
    - QAT
    - calibration_dataset
    - weight_quantization
    - activation_quantization
  require:
    - one_model_object
    - one_precision_or_method_cue
    - same_context_bundle
```

Negative contexts SHALL override the generic word `quantization` unless explicit
neural-model context is present:

```yaml
quantization_negative_context:
  phrases:
    - linear_quantization
    - signal_quantization
    - sensor_value_quantization
    - diagnostic_value_quantization
    - lambda_signal
    - exhaust_gas_signal
    - adc_value
    - bit_encoding
    - scaling_factor
    - physical_value_resolution
    - min_max_conversion
  treatment: reject_as_model_quantization
  reason_code: signal_quantization_not_model_quantization
```

The exact phrase `linear quantization` SHALL default to signal/data encoding, not
neural optimization. It may be reclassified only when the same context explicitly
refers to neural-network weights, activations, tensors, layers, or model precision.

## 16.4 Evidence independence

Multiple pages repeating the same press release SHALL count as one independent
fact cluster. Independent evidence SHALL differ in source origin, underlying
project, publication, or technical content.

## 16.5 Display text vs persisted text

The full evidence description and passage SHALL remain in JSON. Markdown and PDF
may shorten only the visible description by approximately 50 percent, without
mutating internal evidence artifacts or schemas.

## 16.6 Evidence roles and context bundles

Every accepted evidence item SHALL have exactly one evidence role:

```yaml
evidence_role:
  - mapping_eligible
  - contextual_support_only
  - company_identity_only
  - role_classification_only
  - limitation_or_negative_evidence
  - general_industry_background
```

`contextual_support_only` facts may enrich the internal company profile but SHALL
not be cited by applicability mappings and SHALL not be promoted into `Relevant
Evidence`.


`general_industry_background` is not a target-company fact. It SHALL be stored in
a separate background collection or artifact, SHALL not be included in the
company assessment's accepted evidence IDs, and SHALL not be supplied to the
Local LLM as evidence about the target company. If background material is ever
included for market context, it SHALL be in a separately labeled prompt section
and SHALL be prohibited from supporting company-specific statements.

A context bundle SHALL be persisted as an auditable object:

```json
{
  "context_bundle_id": "CTX-00001",
  "target_company_id": "general_motors",
  "company_attribution_status": "established",
  "subject_anchor": "named embedded neural application",
  "locality_mode": "section_local",
  "document_ids": ["DOC-00007"],
  "evidence_ids": ["EVD-00012", "EVD-00013", "EVD-00014"],
  "dimensions": {
    "neural_model": true,
    "embedded_target": true,
    "deployment_workflow": true
  },
  "gate_status": "pass",
  "mapping_eligible": true
}
```

Company-wide aggregate gates MAY be retained for search diagnostics and account
profiling, but SHALL NOT authorize a mapping, increase mapping strength, or
promote a source through the mapping-evidence path. A source may enter `Relevant
Evidence` through the separate opportunity-evidence path only if that source
itself passes Section 16.4; company-wide aggregation cannot satisfy that gate.


## 16.4 Company-specific NNC opportunity evidence

Version 1.3 introduces a relevance class for genuine target-company ML projects
that are commercially and technically worth surfacing even when public evidence
does not yet prove the full NNC deployment chain.

```yaml
evidence_relevance_class:
  - nnc_mapping_evidence
  - nnc_opportunity_evidence
  - contextual_company_evidence
  - general_industry_background
```

`nnc_mapping_evidence` retains all Version 1.1/1.2 requirements and is the only
class that may support deterministic NNC applicability mappings or product-fit
score.

`nnc_opportunity_evidence` SHALL pass when all mandatory conditions below are
satisfied:

```yaml
nnc_opportunity_evidence_gate:
  mandatory:
    company_attribution_status: established
    attributed_company_id: equals_scan_target_company_id
    source_attribution_scope: target_company_or_explicitly_related_partner
    source_quality_any:
      - official_company
      - peer_reviewed_or_professional_technical_publisher
      - patent_or_standardized_publication
    explicit_company_ml_activity_any:
      - machine_learning_model_developed
      - supervised_learning_model_developed
      - data_driven_estimator_or_classifier_developed
      - machine_learning_based_detection_or_recognition
      - virtual_sensor_or_sensorless_estimator
      - patented_machine_learning_regression_or_classification_method
      - patented_learned_estimation_or_control_method
      - patent_claims_neural_network_as_explicit_model_option
      - neural_network_estimator_embodiment
      - neural_network_learning_agent
      - hybrid_physics_data_driven_estimation
      - virtual_measurement_or_latent_physical_variable_estimation
      - predictive_battery_charging_control
    physical_or_embedded_adjacent_application_any:
      - vehicle_system
      - automotive_function
      - telematics
      - ADAS
      - control_or_estimation_function
      - condition_monitoring
      - predictive_maintenance
      - sensor_substitution
      - onboard_or_device_context
      - programmable_or_dedicated_electronic_control_unit
      - onboard_sensor_to_controller_inference
      - drive_brake_yaw_or_stability_control_support
      - battery_management_controller
      - rechargeable_energy_storage_controller
      - onboard_charging_module
      - dedicated_battery_or_charging_processor
    application_maturity_any:
      - real_time
      - deployed_or_trialed
      - prototype_or_experimental_system
      - measured_on_real_system_data
  neural_model_required: false
  confirmed_mcu_or_ecu_execution_required: false
  onnx_required: false
  mapping_eligible: false
  product_fit_score_contribution: 0
  relevant_evidence_eligible: true
  generate_qualification_questions: true
```

The gate SHALL NOT be satisfied by generic corporate statements such as `we use
AI`, by business analytics, cloud-only recommendation engines, generic data
science hiring, or a third-party ML paper that merely mentions the target
company. The source must describe a concrete ML model/application attributable
to the company.

### 16.4.1 Embedded-adjacent semantics

Terms such as `telematics unit`, `vehicle data`, `ADAS`, `sensorless`,
`real-time loading condition`, `virtual sensor`, or `soft sensor` SHALL be
classified as `embedded_adjacent_application_context`; they SHALL NOT by
themselves prove that inference executes on the embedded unit.

Therefore a source may simultaneously have:

```yaml
neural_model_status: unconfirmed
embedded_execution_status: unconfirmed
relevance_class: nnc_opportunity_evidence
mapping_eligible: false
relevant_evidence_eligible: true
```

This distinction is mandatory. The BDA may surface the opportunity while still
stating that the model family and execution target are unknown.

### 16.4.2 Cloud language

The presence of `cloud computing`, `cloud analytics`, or remote data processing
SHALL not automatically reject an otherwise valid company-specific ML
opportunity. A `cloud_only` negative override applies only when the retrieved
source explicitly establishes that inference/application execution is exclusively
cloud/server based and contains no physical-system, onboard, telematics, edge,
sensor, control, or embedded-adjacent use case.

### 16.4.3 Opportunity-evidence claim ceiling

Opportunity evidence passed to the Local LLM SHALL carry a deterministic claim
ceiling:

```yaml
claim_ceiling:
  allowed:
    - confirmed_target_company_ml_project
    - potential_nnc_qualification_opportunity
    - neural_architecture_not_disclosed
    - embedded_execution_not_disclosed
  prohibited:
    - confirmed_neural_network
    - confirmed_mcu_deployment
    - confirmed_onnx_workflow
    - confirmed_nnc_applicability_mapping
```


# 17. Company Assessment JSON

The company assessment SHALL describe the target company independently of NNC.

```json
{
  "target_company_id": "example_mobility",
  "company_name": "Example Mobility",
  "official_domain": "example.com",
  "country": "Germany",
  "company_role": {
    "primary": "tier1_or_system_supplier",
    "secondary": [],
    "confidence": 0.85,
    "evidence_ids": ["EVD-00007"]
  },
  "observed_entities": [
    {
      "target_company_entity_id": "TCE-00001",
      "name": "Battery SOC neural estimator",
      "entity_type": "neural_network_application",
      "use_case_class": "battery_soc_soh_estimation",
      "model_class": "lstm",
      "target_class": "automotive_ecu",
      "hardware_family": "S32K3",
      "deployment_stage": "prototype_on_target",
      "evidence_ids": ["EVD-00001", "EVD-00002"]
    }
  ],
  "domain_layers": {
    "mission": [],
    "data": [],
    "algorithm": [],
    "machine": [],
    "deployment": [],
    "verification": [],
    "lifecycle": []
  },
  "confirmed_facts": [],
  "cautious_inferences": [],
  "unknowns": [
    "Whether the model can be exported to supported ONNX",
    "Exact RAM, ROM, stack, and latency budget",
    "Target compiler and accelerator requirements"
  ],
  "rejected_or_non_applicable_evidence_ids": [],
  "source_coverage": {
    "official_company_sources": 3,
    "primary_partner_sources": 1,
    "academic_sources": 0,
    "other_sources": 1
  }
}
```

The assessment SHALL not include a dSPACE recommendation. It is an input to the
separate applicability stage.


# 18. dSPACE Portfolio Knowledge Base

The portfolio knowledge base SHALL contain authoritative Neural Net Coder
documentation and a validated commercial profile.

## 18.1 Portfolio item

```yaml
dspace_portfolio_item_id: neural_net_coder
commercial_name: Neural Net Coder
aliases:
  - NNC
  - ONNX-2-Target
owner: dSPACE GmbH
supplier: dSPACE
entity_scope: dspace_portfolio
relationship_to_target: external_dspace_product
```

## 18.2 Capability taxonomy

The profile SHALL use only capabilities supported by authoritative dSPACE
documents:

```yaml
capabilities:
  - capability_id: onnx_input
    description: Accept supported neural networks through ONNX as the handover format

  - capability_id: deterministic_c_cpp_generation
    description: Generate readable deterministic C/C++ implementation for embedded use

  - capability_id: static_memory_implementation
    description: Use static memory behavior and avoid dynamic allocation where documented

  - capability_id: resource_forecast
    description: Estimate RAM, ROM or flash, stack, and execution-time requirements

  - capability_id: post_training_optimization
    description: Apply documented post-training optimization such as weight quantization

  - capability_id: model_code_verification
    description: Compare reference ONNX execution with generated-code execution

  - capability_id: mil_sil_pil_workflow
    description: Support documented MIL, SIL, and PIL verification stages

  - capability_id: precision_metrics
    description: Evaluate documented metrics such as MAE, MSE, and RMSE

  - capability_id: safety_oriented_code
    description: Support a safety-oriented embedded implementation workflow with documented coding and traceability properties

  - capability_id: standalone_gui_cli
    description: Operate through stand-alone GUI or CLI workflows

  - capability_id: targetlink_integration
    description: Integrate with the TargetLink model-based development workflow where applicable
```

## 18.3 Portfolio limitations and prerequisites

The profile SHALL encode:

```yaml
limitations:
  - model must be a supported neural-network graph
  - ONNX export or conversion may be required
  - operator and layer coverage must be checked
  - exact target compiler and architecture support must be qualified
  - generated generic C does not imply optimized NPU or DSP kernels
  - resource estimates do not replace target measurement
  - verification does not by itself certify the application
  - training and dataset engineering are outside the product scope
```

## 18.4 Authoritative document corpus

`data/dspace_portfolio_documents/` SHALL include approved NNC product,
technical, value-proposition, workflow, verification, integration, and safety
documents. Every indexed document SHALL have:

```yaml
document_id: <stable_id>
commercial_product: Neural Net Coder
owner: dSPACE
supplier: dSPACE
document_title: <title>
document_version: <version_or_date>
status: approved
sha256: <hash>
```

Unapproved web summaries or competitor pages SHALL not be ingested as
authoritative dSPACE portfolio evidence.


# 19. ChromaDB Design

ChromaDB ingestion and retrieval are mandatory production capabilities.

## 19.1 Collection

```yaml
collection_name: dspace_neural_net_coder_portfolio
embedding_model: bge-large
distance_metric: cosine
persistence_path: data/dspace_portfolio_runtime/chroma_db
```

## 19.2 Chunk metadata

Each chunk SHALL include:

```json
{
  "chunk_id": "NNC-DOC-001-P003-C002",
  "document_id": "NNC-DOC-001",
  "page_number": 3,
  "section_title": "Resource estimation",
  "commercial_name": "Neural Net Coder",
  "owner": "dSPACE",
  "supplier": "dSPACE",
  "relationship_to_target": "external_dspace_product",
  "document_hash": "sha256:...",
  "chunker_version": "1.0.0",
  "embedding_model": "bge-large"
}
```

## 19.3 Ingestion

`ingest-dspace-portfolio` SHALL:

1. enumerate approved documents;
2. validate the portfolio index;
3. parse PDFs with page identity;
4. normalize text;
5. create deterministic overlapping chunks;
6. embed with `bge-large`;
7. upsert into the persistent collection;
8. validate counts and metadata;
9. write a collection manifest;
10. fail on missing mandatory documents, parser errors above threshold,
    embedding failure, or metadata-integrity failure.

No placeholder ingestion is permitted.

## 19.4 Retrieval

Every production scan SHALL:

- validate the collection manifest;
- confirm embedding-model compatibility;
- issue one or more capability-focused queries;
- retrieve top-k chunks;
- filter by product identity and approved status;
- require at least one relevant chunk for every published mapping;
- persist query, score, chunk ID, and rationale.

A retrieval failure SHALL produce `incomplete_portfolio_grounding`, not a low
or no-fit result.


# 20. Target-Company-to-dSPACE Applicability Mapping Logic

The only terminal portfolio item in this BDA is `neural_net_coder`. The system
still SHALL distinguish strong, conditional, weak, and rejected applicability.

## 20.1 Neutral engineering needs

```yaml
engineering_needs:
  - need_id: trained_model_handover
  - need_id: onnx_export_or_conversion
  - need_id: deterministic_embedded_code_generation
  - need_id: static_memory_implementation
  - need_id: resource_fit_estimation
  - need_id: post_training_optimization
  - need_id: accuracy_preservation
  - need_id: model_to_code_equivalence_verification
  - need_id: target_execution_verification
  - need_id: latency_budget_validation
  - need_id: memory_budget_validation
  - need_id: power_budget_validation
  - need_id: safety_oriented_ai_implementation
  - need_id: targetlink_integration
  - need_id: standalone_ai_to_c_workflow
  - need_id: ci_cd_automation
  - need_id: cross_silicon_portability
  - need_id: operator_compatibility_assessment
  - need_id: target_compiler_integration
```

## 20.2 Gate logic

Gates A, B, and C SHALL be evaluated per context bundle. They SHALL NOT be
satisfied by unrelated company-wide evidence items. A company may have a neural
research paper, many ECUs, and a separate embedded-software page without having
any mapping-eligible NNC application.

### Gate A — Neural model

Pass when at least one accepted evidence item confirms a neural network, deep
learning model, explicit neural architecture, or ONNX neural graph.

Fail when evidence supports only non-neural ML or generic AI.

### Gate B — Embedded deployment relevance

Strong pass when evidence confirms MCU, ECU, Cortex-M/R, bare metal, RTOS, or
resource-constrained controller deployment.

Conditional pass when an embedded ECU is mentioned but the processor or
resource envelope is undisclosed.

Weak pass when only a general edge processor is disclosed.

Fail for cloud-only, server-only, or workstation-only inference.

### Gate C — Model-to-software need

Pass when there is evidence of one or more of:

- manual rewrite;
- embedded C/C++ implementation;
- runtime adaptation;
- model conversion;
- code generation;
- target deployment;
- resource optimization;
- verification between model and target;
- safety or deterministic-code requirements.

A trained model with no deployment intent receives at most a research lead.

### Gate D — Product/role conflict

- end users, OEMs, Tier-1s, and system suppliers are normal prospects;
- engineering service providers may be prospects and/or partners;
- semiconductor vendors are primarily partner/ecosystem opportunities unless
  they have internal end-use projects;
- toolchain vendors require partner or competitor handling;
- direct competitors SHALL not receive an end-customer sales score.

### Gate E — Context locality

Pass only when Gates A, B, and C belong to the same validated context bundle and
refer to the same technical subject.

Fail when the implementation attempts to combine:

- neural evidence from one project with an ordinary ECU mention from another;
- a search-result snippet with an unrelated passage in the retrieved document;
- model optimization terms with generic hardware diagnostics;
- company-level evidence clusters that lack a shared project/system/model anchor.

### Gate F — Source and evidence promotion

Pass only when all evidence IDs attached to the mapping are `mapping_eligible`
and permitted by the source promotion policy. Generic manuals are blocked by
default.

## 20.3 Mapping rules

```yaml
applicability_rules:
  - rule_id: NNC-RULE-001
    name: Embedded ONNX neural model
    when:
      all:
        - neural_network_gate: pass
        - embedded_target_gate: strong_or_conditional
        - deployment_workflow_gate: pass
        - context_locality_gate: pass
        - mapping_evidence_promotion_gate: pass
        - has_any: [onnx_model, model_conversion, embedded_c_or_cpp]
    derive_needs:
      - deterministic_embedded_code_generation
      - resource_fit_estimation
      - model_to_code_equivalence_verification
    map_to:
      dspace_portfolio_item_id: neural_net_coder
    base_strength: high

  - rule_id: NNC-RULE-002
    name: Neural virtual sensor on MCU or ECU
    when:
      all:
        - use_case_class: virtual_or_soft_sensor
        - neural_network_gate: pass
        - embedded_target_gate: strong_or_conditional
        - deployment_workflow_gate: pass
        - context_locality_gate: pass
        - mapping_evidence_promotion_gate: pass
    derive_needs:
      - resource_fit_estimation
      - accuracy_preservation
      - target_execution_verification
    map_to:
      dspace_portfolio_item_id: neural_net_coder
    base_strength: high

  - rule_id: NNC-RULE-003
    name: Safety-critical neural ECU application
    when:
      all:
        - neural_network_gate: pass
        - embedded_target_gate: strong_or_conditional
        - deployment_workflow_gate: pass
        - context_locality_gate: pass
        - mapping_evidence_promotion_gate: pass
        - has_any: [iso_26262, iso_pas_8800, functional_safety, misra_c]
    derive_needs:
      - safety_oriented_ai_implementation
      - model_to_code_equivalence_verification
      - traceability
    map_to:
      dspace_portfolio_item_id: neural_net_coder
    base_strength: high

  - rule_id: NNC-RULE-004
    name: Generic embedded AI with NN unconfirmed
    when:
      all:
        - has_any: [embedded_ai, edge_ai, tinyml]
        - neural_network_gate: unknown
    outcome:
      account_signal: qualification_required
      publish_applicability_mapping: false
      score_contribution: 0
      relevant_evidence_promotion: false
    reason_code: neural_network_not_confirmed

  - rule_id: NNC-RULE-005
    name: Non-neural model only
    when:
      neural_network_gate: fail
    map_to:
      dspace_portfolio_item_id: neural_net_coder
    status: rejected
```

## 20.3.1 Mapping evidence contract

Every applicability mapping SHALL persist:

```yaml
mapping_evidence_contract:
  context_bundle_id: required
  subject_anchor: required
  locality_mode: required
  evidence_ids:
    minimum: 1
    all_must_be_mapping_eligible: true
  dimensions:
    neural_model: required
    embedded_target: required
    deployment_workflow: required
  prohibited_support:
    - company_global_gate_only
    - generic_ecu_or_mcu_presence_only
    - generic_ram_rom_stack_watchdog_diagnostics
    - signal_or_diagnostic_quantization
    - search_result_snippet_not_supported_by_retrieved_content
```

A mapping SHALL be rejected with `cross_document_gate_mixing` when its evidence
IDs do not resolve to one valid context bundle. The implementation SHALL not
repair the mapping by silently adding other company documents.

A published applicability mapping requires a passed neural-model gate. Generic
`embedded AI`, `edge AI`, or `TinyML` evidence with an unknown neural model may
create a qualification question or account signal but SHALL NOT create an NNC
applicability mapping or product-fit score contribution. It MAY enter `Relevant
Evidence` only when it independently satisfies the stricter company-specific
`nnc_opportunity_evidence` gate in Section 16.4; generic technology statements do
not satisfy that gate.


A published mapping also requires a passed company-attribution gate for every
target-company evidence ID used by the mapping. Each evidence item SHALL satisfy:

```yaml
mapping_company_attribution_requirements:
  company_attribution_status: established
  attributed_company_id: equals_scan_target_company_id
  source_attribution_scope: target_company_or_explicitly_related_partner
  ambiguous_alias_only: false
  bibliography_only_relationship: false
```

Technical evidence from `general_industry_background` SHALL never be combined
with genuine target-company evidence to complete a mapping gate.

## 20.4 Scoring

The deterministic score SHALL be a bounded integer from 0 to 100.

No score component derived from a mapping may be awarded unless both the
company-attribution gate and the mapping's context-locality gate pass. Generic
controller presence, diagnostic memory terms, ambiguous quantization, or
technically relevant material not attributable to the scanned company SHALL
contribute zero NNC applicability points.

Recommended component model:

| Component | Maximum |
|---|---:|
| Confirmed neural-network evidence | 20 |
| Confirmed constrained embedded target | 20 |
| Confirmed deployment/code-generation need | 15 |
| Confirmed resource or optimization constraint | 10 |
| Confirmed verification need | 10 |
| Confirmed safety/determinism need | 10 |
| Evidence quality and independence | 10 |
| Commercial role fit | 5 |
| **Total** | **100** |

Penalties:

| Condition | Penalty |
|---|---:|
| MCU/ECU target not disclosed | -10 |
| ONNX or conversion path unknown | -5 |
| research only | -10 |
| cloud/server deployment | -30 |
| non-neural model only | score capped at 15 |
| semiconductor/tool vendor only | customer score capped at 40 |
| direct competitor | customer score forced to 0; partner/competitor flag retained |
| target company not established for source | source contributes 0 points and cannot support mappings |
| ambiguous short alias is the only company match | source contributes 0 points |
| general industry background only | source contributes 0 points |
| portfolio grounding missing | no publishable score |

Rating bands:

```yaml
rating_bands:
  high: 75-100
  medium_high: 60-74
  medium: 40-59
  low: 20-39
  no_fit: 0-19
```

`no_fit` is valid only for a completed scan. Technical incompleteness SHALL not
be scored.


# 21. dSPACE Portfolio Assessment and Applicability Mapping JSON

```json
{
  "portfolio_assessment_id": "PAS-00001",
  "target_company_id": "example_mobility",
  "dspace_portfolio_item_id": "neural_net_coder",
  "commercial_name": "Neural Net Coder",
  "owner": "dSPACE",
  "supplier": "dSPACE",
  "relationship_to_target": "external_dspace_product",
  "status": "applicable",
  "score": 82,
  "rating": "high",
  "gates": {
    "neural_network": "pass",
    "embedded_target": "pass",
    "deployment_workflow": "pass",
    "company_role": "normal_prospect",
    "portfolio_grounding": "pass"
  },
  "mappings": [
    {
      "mapping_id": "MAP-00001",
      "target_company_entity_id": "TCE-00001",
      "neutral_engineering_need_id": "deterministic_embedded_code_generation",
      "dspace_capability_id": "deterministic_c_cpp_generation",
      "dspace_portfolio_item_id": "neural_net_coder",
      "strength": "high",
      "target_company_evidence_ids": ["EVD-00001"],
      "supporting_dspace_document_chunk_ids": [
        "NNC-DOC-001-P003-C002"
      ],
      "assumptions": [
        "The trained model can be exported or converted to a supported ONNX graph"
      ],
      "qualification_questions": [
        "Which operators and precision are used?",
        "Which compiler and target core are required?"
      ]
    }
  ],
  "score_trace": [],
  "risks_and_unknowns": [],
  "partner_or_competitor_context": null
}
```

Every mapping SHALL contain the complete scope-safe chain. The commercial name
SHALL come from the validated portfolio profile, never from transforming an
internal identifier.


# 22. Final Assessment JSON

The final assessment SHALL combine company facts, deterministic applicability,
portfolio grounding, narrative status, and report status without allowing the
LLM to regenerate deterministic data.

```json
{
  "target_company": {
    "company_id": "example_mobility",
    "company_name": "Example Mobility",
    "official_domain": "example.com",
    "country": "Germany"
  },
  "assessment_status": "complete",
  "overall_applicability": {
    "score": 82,
    "rating": "high",
    "dspace_portfolio_item_id": "neural_net_coder",
    "commercial_name": "Neural Net Coder"
  },
  "company_assessment_ref": "<prefixed-file>.json",
  "portfolio_assessment_ref": "<prefixed-file>.json",
  "applicability_mappings": [],
  "relevant_evidence_ids": [],
  "rejected_evidence_ids": [],
  "portfolio_chunk_ids": [],
  "narrative": {
    "source": "gemma2:9b",
    "status": "valid",
    "fields": {
      "overall_assessment": "",
      "engineering_relevance": "",
      "recommended_next_step": ""
    }
  },
  "narrative_validation": {
    "schema_valid": true,
    "ownership_valid": true,
    "attribution_valid": true,
    "substantive_valid": true,
    "length_valid": true
  },
  "report_status": {
    "markdown": "created",
    "pdf": "created"
  },
  "workbook_update_eligibility": true
}
```

The final JSON SHALL represent truncation, fallback, ownership violations,
portfolio-grounding failure, and degraded search consistently with the run
manifest and narrative-validation artifact.


# 23. Local LLM Roles

The Local LLM has one mandatory role: produce a concise, evidence-grounded
company assessment narrative after deterministic processing.

The LLM MAY:

- synthesize confirmed facts;
- explain the engineering relevance;
- state assumptions and limitations;
- describe why NNC may help;
- propose qualification questions and a practical next step.

The LLM SHALL NOT:

- plan or execute normal search;
- decide whether evidence is accepted;
- calculate scores;
- select NNC;
- invent model, MCU, ONNX, resource, or safety details;
- regenerate evidence IDs or portfolio chunk IDs;
- assign Neural Net Coder to the target company;
- claim certification or compatibility;
- change the workbook update decision.

Optional ambiguous-evidence review MAY be used only when explicitly enabled. Its
output SHALL be schema-validated and treated as advisory input to deterministic
Python, never as authoritative evidence.


# 24. Python Module Responsibilities

The consolidated flat package SHALL preserve the responsibility allocation of
the Version 1.26 architecture.

Additional NNC-specific deterministic responsibilities in `pipeline.py` include:

- neural-network gate;
- model-family classification;
- use-case classification;
- target-hardware normalization;
- embedded-target gate;
- company-role classification;
- NNC exclusion handling;
- neutral engineering-need derivation;
- NNC score calculation;
- qualification-question generation.

`config_manager.py` SHALL validate NNC taxonomy files and cross-references.
`portfolio_index.py` SHALL ingest only approved dSPACE NNC documents for this
BDA. `narrative_ownership_validator.py` SHALL recognize Neural Net Coder, NNC,
ONNX-2-Target, TargetLink, and dSPACE as protected ownership-sensitive names.


# 25. Reference Python Workflow

Illustrative orchestration:

```python
def scan_company(company: CompanyRecord, runtime: RuntimeContext) -> RunResult:
    run = create_run_identity(company, runtime)
    config = load_and_validate_all_config(runtime)
    validate_prompt_bundle(config.prompts)
    validate_portfolio_index(config.portfolio)

    seeds = register_explicit_seeds(company, config)
    queries = build_nnc_queries(company, config)
    persist_queries(run, queries)

    provider_results = execute_required_queries(queries, runtime.providers)
    candidates = additive_candidate_discovery(
        company=company,
        seeds=seeds,
        provider_results=provider_results,
        config=config,
    )
    candidates = canonicalize_and_deduplicate(candidates)
    selected = reserve_seeds_then_apply_budgets(candidates, config)

    documents = retrieve_candidates(selected, runtime.http)
    passages = parse_hash_cache_and_chunk(documents, config)

    attribution = establish_document_company_attribution(
        documents=documents,
        passages=passages,
        scan_target_company=company,
        alias_policy=config.company_alias_policy,
        source_profiles=config.company_source_profiles,
    )
    persist_company_attribution(run, attribution)

    company_passages = passages_from_established_target_company_sources(
        passages, attribution
    )
    background_passages = passages_from_unattributed_technical_sources(
        passages, attribution
    )
    persist_general_industry_background(run, background_passages)

    relevant_passages = score_page_and_passage_relevance(company_passages, config)

    evidence = extract_deterministic_nnc_evidence(
        relevant_passages,
        taxonomy=config.domain_taxonomy,
    )
    evidence = validate_context_classify_and_deduplicate(evidence, config)

    company_assessment = build_company_assessment(evidence, company, config)
    needs = derive_neutral_engineering_needs(company_assessment, config)
    applicability = evaluate_nnc_applicability(
        company_assessment=company_assessment,
        needs=needs,
        rules=config.applicability_rules,
    )

    portfolio_chunks = retrieve_authoritative_nnc_chunks(
        applicability=applicability,
        portfolio_index=runtime.portfolio_index,
    )
    enforce_portfolio_grounding(applicability, portfolio_chunks)

    final_assessment = build_deterministic_final_assessment(
        company_assessment,
        applicability,
        portfolio_chunks,
    )

    llm_context = build_curated_company_summary_context(final_assessment)
    llm_result = request_company_summary_once(llm_context, timeout_seconds=480)
    narrative = validate_or_fallback(llm_result, final_assessment, config)

    artifacts = persist_and_render(run, final_assessment, narrative)
    update_workbook_if_eligible(company, final_assessment, artifacts)
    finalize_run_manifest(run, artifacts)

    return RunResult.from_artifacts(artifacts)
```

All functions that decide evidence, score, applicability, file state, or
workbook state SHALL be deterministic and tested.


# 26. Logging Specification

Logs SHALL be structured and contain:

- timestamp;
- run ID and cycle ID;
- company ID;
- subsystem;
- event code;
- severity;
- provider or document ID where applicable;
- safe diagnostic message;
- retry/cooldown state;
- artifact path where applicable.

Required event families include:

```yaml
event_families:
  - config_validation
  - provider_preflight
  - query_generated
  - query_executed
  - seed_registered
  - candidate_discovered
  - candidate_selected
  - company_attribution_started
  - company_attribution_established
  - company_attribution_not_established
  - ambiguous_alias_collision
  - source_classified_general_industry_background
  - retrieval_attempt
  - retrieval_result
  - document_parsed
  - evidence_accepted
  - evidence_rejected
  - neural_gate
  - embedded_target_gate
  - role_classification
  - applicability_rule
  - score_component
  - portfolio_retrieval
  - portfolio_grounding
  - llm_request
  - narrative_validation
  - report_render
  - workbook_update
  - run_completion
```

Secrets, raw credentials, private headers, and unredacted personal data SHALL
never be logged.


# 27. PDF and Markdown Sales Assessment Report

The visible report SHALL use this order:

1. `Sales Assessment: <Company Name>`;
2. company domain;
3. company country;
4. overall applicability score and rating;
5. `Report generated on <readable UTC timestamp>`;
6. `OVERALL ASSESSMENT`;
7. company Tiny-AI / Edge-AI activity;
8. NNC applicability and rationale;
9. risks, assumptions, and qualification questions;
10. recommended next step and relevant roles;
11. `Applicability Mappings`;
12. `Relevant Evidence`.

## 27.1 Header

Immediately below the title, display the official web domain and country on two
separate, left-aligned lines in smaller type.

## 27.2 Overall assessment

The visible section formerly called `Narrative` SHALL be titled
`OVERALL ASSESSMENT`.

It SHALL distinguish:

- confirmed company facts;
- inferred engineering needs;
- verified NNC capabilities;
- missing information;
- commercial interpretation.

## 27.3 Applicability Mappings table

The table SHALL contain exactly two visible columns in this order:

| Matched dSPACE Product | Applicability Mapping |
|---|---|
| Neural Net Coder | `<target-company activity> → <engineering need> → <verified NNC capability>` |

Internal IDs and dSPACE chunk IDs MAY appear in machine-readable artifacts but
SHOULD not clutter the visible table.

## 27.4 Relevant Evidence table

Version 1.3 broadens this section from mapping evidence only to two explicit
publication paths. Every published source SHALL still be genuine target-company
evidence; general industry background remains excluded.

**Path A — mapping-supporting evidence** requires:

- `company_attribution.status == established`;
- `attributed_company_id == scan_target_company_id`;
- `assessment.status == accepted`;
- `relevance_class == nnc_mapping_evidence`;
- `mapping_eligibility.eligible == true`;
- a passed context bundle;
- use by a published applicability mapping.

**Path B — opportunity evidence** requires:

- `company_attribution.status == established`;
- `attributed_company_id == scan_target_company_id`;
- `assessment.status == accepted`;
- `relevance_class == nnc_opportunity_evidence`;
- a passed `nnc_opportunity_evidence_gate`;
- explicit uncertainty fields for neural architecture and embedded execution;
- zero deterministic NNC product-fit score contribution.

```yaml
relevant_evidence_promotion:
  common_requirements:
    require_target_company_attribution_established: true
    require_attributed_company_equals_scan_target: true
    reject_general_industry_background: true
    reject_contextual_support_only: true
    reject_company_identity_only: true
    reject_generic_manual_without_override: true
  path_a_mapping_evidence:
    require_relevance_class: nnc_mapping_evidence
    require_mapping_eligible_evidence: true
    require_published_mapping_reference: true
    require_passed_context_bundle: true
  path_b_opportunity_evidence:
    require_relevance_class: nnc_opportunity_evidence
    require_opportunity_gate_pass: true
    require_mapping_eligible_evidence: false
    require_published_mapping_reference: false
    require_zero_product_fit_score_contribution: true
    require_uncertainty_disclosure: true
```

The builder SHALL NOT promote every source that contributed to company-level
gates. It SHALL evaluate each source and each evidence item independently.
Opportunity evidence SHALL be rendered with a concise qualifier such as
`Opportunity evidence — neural architecture and embedded execution not disclosed`
so the visible report cannot be read as proof of current NNC deployability.

Examples that SHALL be omitted:

- a TinyML or neural-network paper returned by a company-alias query when the
  retrieved paper does not establish any relationship to the target company;
- an academic paper where `GM` is matched only through personal initials such as
  `G.M.` in a bibliography;
- an owner's manual that only mentions an ABS electronic control unit;
- an OBD diagnostic PDF that lists RAM, ROM, stack, watchdog, ASIC, CPU, or ADC;
- a diagnostic table using `linear quantization` for exhaust-gas or lambda values;
- a source used only to establish that the company manufactures vehicles with
  ECUs.

The visible table remains:

| No. | Evidence | URL |
|---:|---|---|

The visible Evidence text SHALL be shortened by approximately 50 percent.
Internal evidence JSON SHALL remain unchanged.

## 27.5 Report language controls

The report SHALL use cautious language:

- `The company publicly describes...`
- `This indicates...`
- `NNC may be applicable because...`
- `Applicability remains conditional on...`
- `The public evidence does not disclose...`

Prohibited language includes:

- `The company uses NNC` without evidence;
- `NNC supports this MCU` without authoritative confirmation;
- `The model is ONNX-compatible` unless confirmed;
- `The application is certified`;
- `This proves purchase intent`.

## 27.6 Deterministic rendering

Python SHALL determine:

- section order;
- title and metadata;
- score and rating display;
- table construction;
- line wrapping;
- visible evidence shortening;
- filename;
- timestamp;
- page breaks;
- fallback narrative.

The LLM SHALL not generate report layout or filenames.


# 28. Testing Requirements

The NNC BDA SHALL retain the Version 1.26 unit/integration architecture and add
NNC-specific contract tests.

## 28.1 Mandatory unit test areas

- taxonomy and schema validation;
- neural-network gate;
- generic-AI rejection;
- non-neural-model classification;
- SoC acronym disambiguation;
- MCU/ECU target normalization;
- embedded-target gate;
- cloud/GPU exclusion;
- company-role classification;
- direct-competitor handling;
- engineering-need derivation;
- applicability rule execution;
- score bounds and caps;
- NNC portfolio ingestion;
- NNC portfolio retrieval and grounding;
- ownership and attribution validation;
- report order and table column order;
- visible evidence shortening without JSON mutation;
- workbook update eligibility;
- seed registration and budget isolation;
- required-query execution;
- degraded-run behavior;
- prompt bundle hashing;
- deterministic fallback narrative;
- context-bundle construction and anchor validation;
- rejection of company-wide cross-document gate mixing;
- source-type promotion blocking for owner/OBD/service manuals;
- quantization positive-context and negative-context disambiguation;
- mapping-eligibility separation from factual evidence acceptance;
- two-path Relevant Evidence promotion: mapping evidence or qualified company-specific opportunity evidence;

- document-level company-attribution gate before technical extraction;
- candidate registration never stamps the scan target as the attributed company;
- short/ambiguous aliases cannot independently establish third-party attribution;
- `G.M.` personal initials do not satisfy the `GM` General Motors alias;
- bibliography-only alias collisions are rejected;
- technically relevant but unattributed sources are stored only as general
  industry background and contribute zero score/mappings;
- `nnc_opportunity_evidence` requires a concrete target-company ML application, not generic AI language;
- opportunity evidence contributes zero deterministic product-fit score and cannot satisfy an applicability mapping;
- SAE/technical-publication applied-ML queries execute independently of Semantic Scholar;
- corporate R&D-unit author affiliations resolve through generic organizational-unit rules;
- the Mahindra SAE regression fixture is discovered and promoted without an explicit seed URL;

## 28.2 Regression fixtures from the supplied use-case workbook

All 24 supplied use cases SHALL be imported into a versioned regression dataset.
Each fixture SHALL include the expected classifications for:

- industry;
- use-case class;
- model certainty;
- target certainty;
- hardware family;
- embedded/Tiny-AI status;
- NNC gate result;
- expected qualification questions.

Examples of required behavior:

- NXP/COMPREDICT S32K5 virtual wheel-force case: strong neural and target evidence;
- tire-wear cases with undisclosed MCU: embedded-target conditional;
- Coca-Cola virtual pressure sensor with unspecified Cortex-M: target family uncertain;
- Poclain soft sensor: model/deployment details must be checked rather than assumed;
- battery SOC/SOH cases: distinguish neural, hybrid, and non-neural estimators;
- Ambiq, ESP32-S3, nRF54L, xG24, STM32, Renesas, Infineon, and TI cases:
  normalize named hardware without assuming NNC support;
- Siemens industrial predictive-maintenance fixture with no MCU: do not classify as
  confirmed TinyML.

## 28.3 Acceptance tests

A production-ready implementation SHALL prove that:

1. a strong embedded NN case receives a grounded NNC mapping;
2. a generic AI page does not pass the neural gate;
3. a linear-regression-only case does not receive a normal NNC fit;
4. an MCU product page without a target-company application is not treated as
   end-user evidence;
5. a cloud-only neural application is rejected or heavily penalized;
6. portfolio retrieval failure prevents publication and workbook update;
7. an LLM ownership violation triggers deterministic fallback;
8. report metadata and section order match the contract;
9. historical artifacts are preserved;
10. a full registry cycle produces an atomic completion manifest;
11. `linear quantization` in an OBD signal table is classified as signal encoding,
    not neural-model optimization;
12. an owner's manual passage containing only `ABS electronic control unit` is
    accepted at most as contextual controller evidence and is not mapping eligible;
13. neural evidence from one company document cannot be combined with generic ECU
    evidence from another document to pass an NNC mapping;
14. generic owner and diagnostic manuals do not enter `Relevant Evidence` unless
    an explicit local neural-deployment override passes;
15. static-memory, resource-fit, and cross-silicon mappings cannot be derived from
    generic RAM/ROM/stack/watchdog or ECU terms alone.

## 28.4 Test count

The initial implementation SHOULD meet or exceed the audited Version 1.26
baseline of 50 passing tests. The number is a floor for coverage planning, not a
reason to combine unrelated requirements into weak tests.


# 29. Runtime Controls and Search Reliability

Runtime controls SHALL preserve Version 1.26 behavior while using NNC-specific
queries and evidence.

## 29.1 Default budgets

Illustrative production defaults:

```yaml
budgets:
  queries_per_company:
    min: 20
    max: 50
  candidate_urls:
    max_total: 250
    max_per_host: 80
    protected_seed_slots: unlimited_within_seed_validation
  internal_pages:
    max: 200
  discovered_pdfs:
    max: 60
  pdf_size_mb:
    max: 50
  passages_per_document:
    max: 500
  company_execution_minutes:
    max: 45
```

Exact defaults SHALL remain configurable and validated.

## 29.2 Concurrency

```yaml
concurrency:
  companies: 1
  total_network: 4
  ddgs: 1
  crawler: 3
  github: 1
  semantic_scholar: 1
  pdf_downloads: 2
```

Companies SHALL be processed sequentially. Bounded concurrency MAY be used
within one company.

## 29.3 Timeouts and retries

- network calls SHALL have connect, read, write, and pool timeouts;
- retries SHALL be bounded and use provider-aware backoff;
- the Gemma summary request SHALL have a 480-second hard timeout;
- portfolio embedding and retrieval SHALL have explicit timeouts;
- cancellation SHALL leave a valid incomplete manifest;
- unbounded retries are prohibited.

## 29.4 Cache identity

Parsed content cache keys SHALL include:

- canonical URL;
- content hash;
- parser identifier and version;
- passage/chunker version;
- domain-taxonomy hash where relevant;
- retrieval configuration hash.

A changed parser or chunker SHALL invalidate incompatible cached passages.

## 29.5 Provider degradation

One unavailable provider SHALL not disable:

- explicit seeds;
- homepage retrieval;
- DDGS when available;
- other configured providers;
- sitemap discovery;
- internal crawling;
- official PDF parsing;
- cached valid documents.

Provider degradation SHALL be recorded in the run and cycle manifests.

## 29.6 Search acceptance

A run SHALL not be search-complete unless:

- required query generation succeeded;
- every required query was submitted to an enabled provider;
- explicit seeds were registered;
- candidate selection completed after additive discovery;
- retrieval attempts were recorded;
- configured minimum source coverage was reached or a justified degraded status
  was recorded.

## 29.7 Source-coverage diagnostics

The manifest SHOULD report:

```yaml
coverage:
  official_domain_pages:
  official_pdfs:
  partner_or_primary_sources:
  research_sources:
  distinct_use_cases:
  distinct_hardware_families:
  confirmed_neural_cases:
  confirmed_embedded_targets:
  unconfirmed_model_cases:
  unconfirmed_target_cases:
```

A high result count with no confirmed neural or deployment evidence SHALL not be
presented as strong coverage.


# 30. Run Manifest JSON

The run manifest SHALL include:

```json
{
  "run_id": "RUN-...",
  "cycle_id": "CYCLE-...",
  "company_id": "example_mobility",
  "started_at_utc": "...",
  "completed_at_utc": "...",
  "status": "complete",
  "specification_version": "1.1",
  "design_document_version": "1.1.0",
  "application_version": "2.0.0",
  "domain_config_hashes": {},
  "portfolio_manifest_hash": "...",
  "prompt_bundle": {
    "bundle_id": "company_summary_v3.0",
    "schema_integrity_version": "3.2.0",
    "file_hashes": {}
  },
  "models": {
    "embedding": "bge-large",
    "summary": "gemma2:9b"
  },
  "search": {
    "queries_generated": 0,
    "required_queries": 0,
    "required_queries_executed": 0,
    "providers_available": [],
    "providers_degraded": [],
    "seeds_registered": true,
    "candidates_discovered": 0,
    "candidates_selected": 0,
    "retrieval_attempts": 0
  },
  "evidence": {
    "accepted": 0,
    "rejected": 0,
    "confirmed_neural_cases": 0,
    "confirmed_embedded_targets": 0
  },
  "applicability": {
    "portfolio_item_id": "neural_net_coder",
    "score": 0,
    "rating": "no_fit",
    "grounding_gate": "pass"
  },
  "narrative": {
    "attempted": true,
    "status": "valid_or_fallback"
  },
  "artifacts": {},
  "workbook_update": {
    "eligible": true,
    "status": "completed"
  },
  "degraded_reasons": []
}
```

`seeds_registered` SHALL be derived only from the immutable pre-budget seed
registry. It SHALL not change because of later retrieval failure.


# 30A. Registry Cycle Manifest and Completion Summary

Every `scan-registry` execution SHALL create:

```text
output/cycles/<cycle_id>/
    <cycle_id>_cycle_manifest.json
    <cycle_id>_cycle_summary.md
```

The cycle manifest SHALL be written atomically and report:

- selected workbook rows;
- skipped rows and reasons;
- company run IDs;
- complete, incomplete, failed, and cancelled counts;
- provider preflight status;
- shared provider quota and cooldown state;
- workbook backup path;
- pending rating updates;
- committed rating updates;
- degraded-mode reasons;
- cycle completion status.

The human-readable summary SHALL identify companies requiring rerun because of
search, retrieval, portfolio, LLM, report, or workbook failures.

An incomplete cycle SHALL still have a valid completion artifact describing the
partial state.


# 31. Recommended CLI

The CLI SHALL provide at least:

```text
python -m bd_agent_neural_net_coder validate-installation
python -m bd_agent_neural_net_coder validate-config
python -m bd_agent_neural_net_coder validate-search-providers
python -m bd_agent_neural_net_coder validate-free-search-config
python -m bd_agent_neural_net_coder show-search-quota
python -m bd_agent_neural_net_coder ingest-dspace-portfolio
python -m bd_agent_neural_net_coder validate-dspace-portfolio
python -m bd_agent_neural_net_coder scan-company
python -m bd_agent_neural_net_coder scan-registry
python -m bd_agent_neural_net_coder batch
```

`batch` MAY remain a deprecated compatibility alias for `scan-registry`.

Example standalone scan:

```powershell
python -m bd_agent_neural_net_coder scan-company `
  --company-name "Example Mobility" `
  --official-domain "example.com" `
  --country "Germany" `
  --seed-url "https://example.com/research/embedded-ai"
```

Example registry scan:

```powershell
python -m bd_agent_neural_net_coder scan-registry `
  --workbook "data\Companies.xlsx"
```

Additional useful commands MAY include:

```text
show-domain-taxonomy
show-engineering-needs
show-applicability-rules
explain-score
render-report
rebuild-cache
```

CLI validation SHALL fail with a nonzero exit code for invalid mandatory
configuration, missing production dependencies, invalid portfolio index,
incompatible models, or prompt-integrity failure.


# 32. Security, Legal, and Ethical Controls

The application SHALL use only sources and access methods permitted by applicable
law, terms, and operator policy.

It SHALL:

- respect robots directives where required by policy;
- enforce rate limits and polite crawling;
- avoid bypassing access controls;
- avoid collecting unnecessary personal data;
- redact secrets;
- retain only business-relevant public evidence;
- separate technical fit from purchase intent;
- avoid discriminatory or sensitive-person profiling;
- preserve source attribution and URL provenance;
- clearly label inference and uncertainty;
- require human review before commercial action.

Career pages MAY be used to infer organizational capabilities, but individual
employee data SHALL not be collected beyond what is necessary to identify a
relevant role category.


# 33. Example: Embedded Battery Neural Estimator

This example is illustrative and not a claim about a real company.

**Observed passage:** A company describes an LSTM-based battery state-of-charge
estimator deployed on an NXP S32K344 controller. The page mentions generated
embedded code and real-time execution but does not state that the model is
available in ONNX.

Deterministic processing:

```text
Observed company fact
  LSTM battery estimator on S32K344
        ↓
Normalized entity
  neural_network_application
  use_case = battery_soc_soh_estimation
  target = automotive_ecu / S32K3
        ↓
Neutral engineering needs
  deterministic_embedded_code_generation
  resource_fit_estimation
  accuracy_preservation
  target_execution_verification
        ↓
NNC capability candidates
  ONNX input
  C/C++ generation
  resource forecast
  back-to-back verification
        ↓
Qualification condition
  confirm supported ONNX export and operator coverage
```

Expected assessment:

- neural-network gate: pass;
- embedded-target gate: pass;
- deployment-workflow gate: pass;
- NNC fit: high but conditional;
- target compatibility: unconfirmed;
- ONNX handover: unconfirmed;
- recommended next step: technical qualification of model graph, precision,
  compiler, resource budget, and verification workflow.

The report SHALL not say that NNC supports S32K344 unless the portfolio corpus
explicitly confirms it.


# 34. Definition of Done

The initial NNC BDA is complete only when:

1. all configuration and schemas validate;
2. the NNC domain taxonomy is implemented;
3. all 24 use-case workbook rows exist as regression fixtures;
4. mandatory provider search executes;
5. HTML and PDF retrieval works;
6. accepted and rejected evidence are persisted;
7. neural, embedded-target, deployment, and role gates are deterministic;
8. NNC scoring is deterministic and tested;
9. approved NNC documents are ingested into ChromaDB;
10. every published mapping has retrieved NNC chunks;
11. the Local LLM is limited to one narrative attempt;
12. invalid narratives fall back deterministically;
13. Markdown and PDF match the report contract;
14. Companies.xlsx updates are backed up and atomic;
15. run and cycle manifests are complete;
16. no historical artifacts are overwritten;
17. automated tests pass;
18. implementation deviations are recorded in
    `docs/IMPLEMENTATION_NOTES.md`.


# 35. Decision Boundary

The system may conclude:

- strong NNC fit;
- medium-high fit;
- medium fit;
- low or exploratory fit;
- no fit;
- partner opportunity;
- competitor relationship;
- incomplete assessment.

It may not conclude that a company has purchase intent, budget, approved
technical compatibility, certification, or active NNC adoption unless explicit
evidence establishes that fact.


# 36. Hybrid Product-Fit Assessment Architecture

The NNC BDA combines deterministic and semantic components.

## 36.1 Deterministic components

Python/YAML control:

- taxonomy;
- source validation;
- co-occurrence;
- exclusions;
- model and target classification;
- engineering-need derivation;
- scoring;
- product selection;
- report layout;
- ownership validation.

## 36.2 Semantic components

Embeddings support:

- discovery-query expansion where bounded;
- related-passage ranking;
- NNC portfolio-document retrieval;
- clustering near-duplicate evidence.

The Local LLM supports only final narrative synthesis.

## 36.3 Why the hybrid design is necessary

Exact term matching alone misses cases where companies describe:

- estimated physical quantities without saying `virtual sensor`;
- learned observers without saying `neural network` in the title;
- target deployment in a diagram or PDF;
- constrained deployment through RAM/latency language;
- verification without using dSPACE terminology.

Pure semantic reasoning is also insufficient because it can:

- confuse generic AI with neural networks;
- confuse a semiconductor's capability with a customer's use;
- confuse a target-company product with Neural Net Coder;
- infer unsupported compatibility;
- ignore exclusions;
- invent commercial intent.

The hybrid design SHALL use semantic methods to find and rank relevant material,
then deterministic rules to decide what it means.

## 36.4 Confidence model

Each conclusion SHOULD carry:

```yaml
confidence_components:
  source_quality:
  statement_explicitness:
  company_relationship:
  local_context:
  evidence_independence:
  target_specificity:
  model_specificity:
```

Confidence and applicability score are distinct. A highly confident cloud-only
NN fact may have low NNC applicability.


# 37. Final Company Assessment and Local LLM Summary

The final narrative SHALL be generated from a curated deterministic context, not
the full raw assessment JSON.

Preferred visible structure:

1. **OVERALL ASSESSMENT** — one paragraph explaining the score and the strongest
   company facts;
2. **Engineering relevance** — one paragraph connecting embedded NN activities
   to neutral needs and verified NNC capabilities;
3. **Next step** — one paragraph with the most important qualification questions,
   roles, and risks.

The narrative SHOULD be approximately 160–260 words and SHALL remain within the
configured hard bounds. It SHALL retain at least three target-company evidence
sources when three or more are available.

The deterministic fallback SHALL produce the same three conceptual parts using
templates and persisted facts. Fallback use SHALL not change score, mappings,
evidence, grounding, or workbook eligibility.


# 38. Local LLM Prompt Engineering for Company Assessments

## 38.1 Prompt bundle

The active bundle SHALL retain the implemented Version 1.26 naming contract:

```text
prompts/company_summary_system_v3.txt
prompts/company_summary_user_template_v3.txt
prompts/company_summary_output_schema_v3.json
prompts/company_summary_prompt_manifest_v3.yaml
prompts/ownership_contract_v1.yaml
```

```yaml
bundle_id: company_summary_v3.0
schema_integrity_version: 3.2.0
```

All files SHALL be loaded at runtime, hashed, and recorded in the run manifest.
Hard-coded production prompts in `pipeline.py` are prohibited.

## 38.2 Curated context

The LLM SHALL receive only:

- company name, domain, country, and role;
- deterministic score and rating;
- strongest confirmed target-company facts;
- derived neutral engineering needs;
- deterministic NNC mappings;
- selected authoritative NNC capability summaries;
- assumptions and unknowns;
- qualification questions;
- up to a bounded set of source titles and URLs;
- product ownership metadata.

It SHALL not receive authority to modify any deterministic field.

## 38.3 System instruction contract

The system prompt SHALL state, in substance:

```text
You write a concise business-development assessment from supplied facts.
Neural Net Coder is a dSPACE product, not a target-company product.
Do not claim the target company uses, owns, supplies, develops, or selected it
unless the supplied evidence explicitly says so.
Do not invent an ONNX path, target support, model architecture, resource figure,
safety status, or purchase intent.
Separate confirmed facts from inferences and unknowns.
Explain the relationship:
company activity -> neutral engineering need -> verified NNC capability.
Return only JSON matching the supplied schema.
```

## 38.4 Output schema

The LLM response SHALL contain only rendered narrative fields:

```json
{
  "overall_assessment": "string",
  "engineering_relevance": "string",
  "recommended_next_step": "string"
}
```

The LLM SHALL not return:

- score;
- rating;
- applicability mappings;
- evidence IDs;
- portfolio chunk IDs;
- ownership fields;
- product decision;
- workbook decision.

## 38.5 Substantive validation

Python SHALL reject a narrative when it:

- assigns NNC or dSPACE capabilities to the target company;
- contradicts deterministic score or gates;
- omits the strongest confirmed evidence;
- invents a model, MCU, target, ONNX format, standard, or project;
- claims certification;
- describes generic benefits without connecting them to evidence;
- exceeds hard length limits;
- is truncated or structurally invalid;
- contains raw internal identifiers in visible prose;
- fails to state a material limitation for a conditional fit.

## 38.6 Ownership and first-mention rules

The first mention SHOULD use:

```text
dSPACE Neural Net Coder
```

or:

```text
Neural Net Coder, a dSPACE product
```

Later references may use `Neural Net Coder` or `NNC`.

Phrases such as `the company's Neural Net Coder`, `its NNC product`, or
`the company developed NNC` SHALL trigger a violation unless explicit target
company evidence proves the relationship.

## 38.7 Good narrative pattern

```text
The company publicly describes an LSTM-based estimator running on an automotive
ECU, which provides direct evidence of an embedded neural-network use case.
This creates a plausible need for deterministic code generation, resource-fit
checks, and model-to-code verification. dSPACE Neural Net Coder may address
those needs through its supported ONNX-to-C/C++ workflow and verification
features. Applicability remains conditional on ONNX operator coverage, target
compiler requirements, and the disclosed memory and latency budget.
```

## 38.8 Bad narrative pattern

```text
The company uses Neural Net Coder on its S32K controller and is fully compliant
with ISO 26262.
```

This is invalid unless both use and compliance are explicitly evidenced.

## 38.9 Output budget and timeout

The final-summary request SHALL have:

- hard timeout: 480 seconds;
- output token budget: 1,800 tokens;
- prompt target: substantially shorter valid JSON;
- one mandatory attempt;
- deterministic fallback after invalid or failed output.

A self-revision step MAY occur only inside the one logical request if supported
by the runtime contract; it SHALL not create an unbounded retry loop.


# 39. Companies.xlsx Company Registry, Cycle Selection, and Overall Product Match

The workbook contract SHALL match the Version 1.26 architecture.

## 39.1 Required sheet and headers

Sheet: `Companies`

Required headers by name:

```text
company_id
company_name
company_domain
country
industry
notes
scan_y_n
overall_product_match
```

The current column expectations remain:

- `Scan Y/N` in column G;
- `Overall Product Match` in column H;

but code SHALL validate headers by normalized name, not only by position.

## 39.2 Selection

Rows are selected when `scan_y_n` normalizes to `Y`.

Existing values in `overall_product_match` SHALL not cause automatic skipping.
A selected complete run recomputes and overwrites the rating according to the
atomic update contract.

## 39.3 Workbook metadata

Registry scans SHALL obtain official domain and country from the workbook.
Standalone `scan-company` SHALL accept `--official-domain` and `--country` and
map them to the same deterministic metadata fields.

## 39.4 Update value

The implementation SHALL write a human-readable rating, for example:

```text
High
Medium-High
Medium
Low
No Fit
Partner
Competitor
```

An incomplete run SHALL not overwrite the existing cell.

## 39.5 Safe update process

1. validate workbook path and headers;
2. fail safely if the workbook is locked;
3. create a timestamped backup;
4. write pending updates to `pending_rating_updates.json`;
5. update only eligible rows;
6. save to a temporary workbook;
7. validate the saved workbook;
8. replace atomically;
9. record backup, pending, and committed state in the cycle manifest.

The update SHALL not alter unrelated cells, formulas, formatting, worksheets, or
historical backups.


# 40. Version 1.0 Runtime, Model, Domain, and Regression Controls

This section consolidates the NNC-specific runtime baseline.

## 40.1 Models

```yaml
models:
  final_summary:
    provider: ollama
    model: gemma2:9b
    timeout_seconds: 480
    max_output_tokens: 1800
  embeddings:
    provider: ollama
    model: bge-large
```

A different local model MAY be evaluated only through the benchmark and approval
process. Production identifiers SHALL not change silently.

## 40.2 Domain runtime profile

```yaml
domain:
  domain_id: tiny_edge_ai
  taxonomy_version: 1.1.0
  engineering_need_version: 1.1.0
  scoring_version: 1.1.0
  page_relevance_version: 1.1.0
  regression_dataset_version: 1.1.0
```

## 40.3 Hardware baseline

CPU execution is the baseline for reproducibility. GPU or accelerated Ollama
execution MAY be enabled after validating:

- model availability;
- output-schema reliability;
- embedding equivalence;
- latency improvement;
- memory stability;
- no regression in ownership or factuality validation.

## 40.4 Regression controls

The domain regression suite SHALL include:

- positive embedded NN cases;
- NN with target unknown;
- target with NN unknown;
- ONNX but cloud-only;
- neural model on high-power edge SoC;
- non-neural virtual sensor;
- hybrid physical/NN estimator;
- silicon-vendor reference design;
- direct competitor tool page;
- research paper with no deployment target;
- safety-critical embedded NN case;
- generic AI marketing page.

Every scoring or taxonomy change SHALL execute the full suite and persist the
before/after score trace.


# 41. Semantic Scopes, Naming, and Applicability-Mapping Contract

The following naming rules are mandatory.

## 41.1 Target-company fields

Use:

```text
target_company_entity_id
target_company_entity_name
target_company_activity
target_company_evidence_ids
```

## 41.2 Neutral-need fields

Use:

```text
neutral_engineering_need_id
neutral_engineering_need_description
need_derivation_rule_id
```

## 41.3 dSPACE fields

Use:

```text
dspace_capability_id
dspace_portfolio_item_id
dspace_commercial_name
supporting_dspace_document_chunk_ids
```

## 41.4 Prohibited generic names

Do not use unscoped:

```text
product_id
product_name
product_candidate
recommended_product
owner
supplier
```

in cross-scope objects.

## 41.5 Mapping object

```yaml
mapping:
  target_company_entity_id: TCE-...
  target_company_evidence_ids: [EVD-...]
  neutral_engineering_need_id: resource_fit_estimation
  need_derivation_rule_id: NNC-NEED-RULE-...
  dspace_capability_id: resource_forecast
  dspace_portfolio_item_id: neural_net_coder
  supporting_dspace_document_chunk_ids: [NNC-DOC-...]
  strength: high
  assumptions: []
  qualification_questions: []
```

The mapping SHALL never skip the neutral-need or dSPACE-capability level.


# 42. Version 1.0 Directory, Workbook, and Cycle-Selection Contract

The default application directory is:

```text
C:\Users\ClaudioD\Desktop\BD-Agent-for-NNC-v2.0
```

The default company registry is:

```text
data\Companies.xlsx
```

The repository, PyPI distribution, application version, and import package are
distinct identifiers and SHALL not be conflated.

Registry processing SHALL:

- normalize `Y`, `y`, `yes`, and configured equivalents;
- reject duplicate company IDs;
- require company name, domain, and country for selected rows;
- process companies sequentially;
- create a unique run directory for each;
- preserve all prior run artifacts;
- finalize one cycle manifest.

The current `overall_product_match` value does not suppress rescanning a selected
row.


# 43. Version 1.0 Model Assignment Contract

Model assignment is fixed by responsibility:

| Task | Mechanism |
|---|---|
| YAML and schema validation | Python |
| Search planning | Python templates |
| Search execution | provider adapters |
| Evidence acceptance | Python |
| Taxonomy matching | Python/YAML |
| Applicability and score | Python/YAML |
| Portfolio semantic retrieval | `bge-large` + ChromaDB |
| Final narrative | `gemma2:9b` |
| Ownership validation | Python |
| Report layout | Python |

The LLM SHALL not perform routine search planning, evidence extraction,
deterministic scoring, product selection, or workbook updates.

Optional ambiguous-evidence review SHALL be disabled by default and use a
separate prompt and output schema.


# 44. Mandatory ChromaDB Portfolio Ingestion, Retrieval, and Grounding Implementation

## 44.1 Production requirement

The implementation SHALL contain real, working ingestion and retrieval. A CLI
command that prints setup guidance, returns no chunks, or creates a collection
without embeddings is not an implementation.

## 44.2 Ingestion inputs

The portfolio index YAML SHALL declare each approved Neural Net Coder document,
including:

- document ID;
- path;
- title;
- date/version;
- product identity;
- owner and supplier;
- status;
- expected hash or controlled hash-update process.

## 44.3 Deterministic chunking

Chunk identity SHALL be reproducible from document ID, page, normalized text,
and chunker version. Chunks SHOULD preserve headings and avoid combining
unrelated product capabilities.

## 44.4 Embeddings

The ingestion command SHALL call the configured `bge-large` embedding endpoint,
validate vector dimensions, and store vectors in ChromaDB. An embedding error
SHALL fail ingestion.

## 44.5 Manifest

The collection manifest SHALL include:

```json
{
  "collection_name": "dspace_neural_net_coder_portfolio",
  "portfolio_profile_version": "1.0.0",
  "embedding_model": "bge-large",
  "embedding_dimension": 0,
  "document_count": 0,
  "chunk_count": 0,
  "document_hashes": {},
  "chunker_version": "1.0.0",
  "created_at_utc": "...",
  "validated": true
}
```

The real dimension and counts SHALL be written by the implementation.

## 44.6 Retrieval queries

Retrieval queries SHALL be built from the selected neutral needs and capability
IDs, for example:

```text
Neural Net Coder ONNX to deterministic C/C++ code generation
Neural Net Coder RAM ROM stack execution-time estimation
Neural Net Coder static memory no dynamic allocation
Neural Net Coder post-training quantization optimization
Neural Net Coder ONNX Runtime generated code back-to-back verification
Neural Net Coder MIL SIL PIL
Neural Net Coder TargetLink integration
Neural Net Coder standalone GUI CLI
```

## 44.7 Grounding acceptance

For each applicability mapping, Python SHALL verify:

- chunk belongs to an approved NNC document;
- commercial product is Neural Net Coder;
- owner and supplier are dSPACE;
- chunk meaning supports the selected capability;
- similarity meets the configured threshold;
- no limitation in the same context contradicts the claim.

## 44.8 Failure semantics

Use explicit states:

```yaml
portfolio_status:
  - valid
  - collection_missing
  - manifest_invalid
  - embedding_model_mismatch
  - ingestion_failed
  - retrieval_failed
  - no_relevant_chunks
  - grounding_failed
```

Any state other than `valid` SHALL prevent a completed publishable assessment
and workbook overwrite.


# 45. Mandatory Multi-Provider Target-Company Search Implementation

## 45.1 DDGS

DDGS is mandatory. The adapter SHALL invoke `DDGS().text(...)` or the supported
equivalent and add returned URLs to the candidate queue.

## 45.2 Other providers

The zero-cost production profile SHALL support:

- Brave Search API;
- SerpAPI;
- Serper;
- Semantic Scholar;
- GitHub REST API;
- sitemaps;
- internal crawling;
- PDF-link discovery.

Provider adapters SHALL be functional, not placeholders.

## 45.3 Required NNC query coverage

Every selected company SHALL receive query execution across the key dimensions:

```yaml
query_dimensions:
  - neural_network
  - embedded_edge_tiny_ai
  - virtual_soft_sensor
  - predictive_maintenance
  - model_framework_onnx
  - mcu_ecu_hardware
  - resource_constraints
  - quantization_optimization
  - code_generation_runtime
  - verification_mil_sil_pil
  - safety_misra_iso
  - research_patents_jobs
```

The query plan SHALL include domain-specific aliases relevant to the company
industry and known hardware.

## 45.4 Official-domain discovery

The crawler SHALL:

- retrieve the homepage;
- attempt common sitemap locations;
- parse declared sitemaps;
- follow approved internal links;
- discover technical PDFs;
- respect per-domain and total budgets;
- prioritize pages whose URL/title contains AI, machine-learning, embedded,
  software, research, innovation, sensor, control, battery, maintenance,
  publication, or career signals.

## 45.5 Approved asset domains

Company-specific profiles MAY allow official asset/CDN domains. A PDF hosted on
an approved asset domain SHALL retain its relationship to the official company
source.

## 45.6 Specialist providers

Semantic Scholar and GitHub results SHALL enter the same candidate, retrieval,
evidence, and provenance pipeline. Search snippets alone SHALL not become
accepted evidence.

## 45.7 No audit-only implementation

The following SHALL fail acceptance:

- queries written to JSON but never submitted;
- a provider adapter returning empty success by design;
- a PDF link collected but never parsed;
- an internal crawler that retrieves only the homepage;
- a missing provider disabling all remaining channels;
- one candidate source chosen with fallback `or` logic instead of additive
  discovery.


# 46. Version 1.0 Cost-Free Search Configuration and Quota Enforcement

The default mode SHALL be:

```yaml
search_cost_mode: zero_cost_only
paid_overage: false
automatic_credit_purchase: false
automatic_plan_upgrade: false
```

Every API provider SHALL have a local quota policy:

```yaml
provider:
  enabled: true
  credential_env: <name>
  free_allowance:
    period: monthly_or_nonrenewing
    configured_limit: <operator-maintained>
  software_budget:
    per_company: <limit>
    per_cycle: <limit>
  retries:
    max_attempts: <bounded>
  paid_overage_allowed: false
```

The local quota ledger SHALL persist:

- provider;
- account/billing period where known;
- estimated calls consumed;
- confirmed remaining quota where available;
- last reconciliation time;
- response-header quota data;
- cooldown/reset time;
- operator adjustments.

No call that may incur a charge SHALL be made after the configured free
allowance or conservative software budget is exhausted.

A provider with missing credentials or exhausted quota SHALL be skipped once at
cycle preflight and recorded as degraded. Other cost-free channels SHALL remain
active.


# 47. Version 1.0 Gemma Runtime and Assessment-Report Contract

The mandatory final summary SHALL use:

```yaml
model: gemma2:9b
provider: ollama
timeout_seconds: 480
max_output_tokens: 1800
attempts: 1
```

The context builder SHALL prefer quality over volume and SHALL include:

- at least three relevant company sources when available;
- the strongest accepted neural and target evidence;
- deterministic score and mapping;
- authoritative NNC capability summaries;
- explicit ownership metadata;
- key unknowns and qualification questions.

The narrative output SHALL not be allowed to change report tables, score,
evidence, or applicability.

Timeout, malformed JSON, truncation, schema failure, ownership failure,
attribution failure, contradiction, or substantive failure SHALL trigger the
deterministic fallback and be represented consistently in all artifacts.


# 48. Version 1.0 Provider Credentials and PDF Presentation Contract

Credential commands SHALL report only status:

```text
configured
missing_credentials
invalid_credentials
available
quota_low
quota_exhausted
provider_error
```

They SHALL never echo secret values.

The PDF report SHALL:

- use the human-readable UTC filename contract;
- display company domain and country below the title;
- display generation timestamp;
- use `OVERALL ASSESSMENT`;
- place `Applicability Mappings` before `Relevant Evidence`;
- place `Matched dSPACE Product` first;
- shorten visible evidence text only;
- list canonical URLs;
- preserve historical PDFs;
- render a deterministic fallback when Gemma fails.

Automated report tests SHALL validate text order and table headers, not merely
file existence.


# 49. Version 1.0 dSPACE Product-Ownership and Narrative-Safety Contract

## 49.1 Protected entities

```yaml
protected_dspace_entities:
  - canonical_name: Neural Net Coder
    aliases: [NNC, ONNX-2-Target]
    owner: dSPACE
    supplier: dSPACE
  - canonical_name: TargetLink
    aliases: []
    owner: dSPACE
    supplier: dSPACE
  - canonical_name: dSPACE
    entity_type: company
```

## 49.2 Context metadata

Every NNC item supplied to the LLM SHALL carry:

```yaml
owner: dSPACE
supplier: dSPACE
commercial_name: Neural Net Coder
relationship_to_target: external_dspace_product
```

## 49.3 Deterministic checks

The validator SHALL detect:

- possessive attribution to the target company;
- target company as subject of `develops`, `offers`, `supplies`, `uses`, or
  `selected` when unsupported;
- ambiguous pronouns near product names;
- NNC capability described as a target-company capability;
- competitor tools mislabeled as dSPACE;
- target-company projects mislabeled as NNC features;
- first mention without clear dSPACE attribution;
- certification or target-support overclaims.

## 49.4 Consequence

An ownership or attribution violation invalidates only the LLM narrative. It
SHALL trigger deterministic fallback without changing:

- score;
- rating;
- mappings;
- evidence;
- portfolio chunks;
- workbook eligibility, provided all other gates pass.

The violation SHALL be recorded in `narrative_validation.json`.


# 50. Version 1.0 Degraded-Run Reliability and Observability Contract

Run status SHALL distinguish:

```yaml
run_status:
  - complete
  - complete_with_noncritical_degradation
  - incomplete_search
  - incomplete_retrieval
  - incomplete_portfolio_grounding
  - incomplete_assessment
  - incomplete_reporting
  - failed_configuration
  - failed_runtime
  - cancelled
```

A narrative fallback alone MAY still allow a complete assessment because the
deterministic result remains valid. Missing mandatory search execution or
portfolio grounding does not.

Provider-level errors SHALL be summarized by provider and reason. Optional
providers without credentials SHALL not generate one repeated error per query.

Semantic Scholar and GitHub rate-limit state SHALL be shared across all
companies in the active cycle.

Every cycle SHALL finish with a completion manifest even when interrupted.


# 51. Version 1.0 Seed Registration and Candidate-Budget Isolation Contract

Explicit seeds SHALL pass through distinct states:

```yaml
seed_state:
  - supplied
  - validated
  - registered
  - selected_for_retrieval
  - retrieval_attempted
  - retrieval_succeeded
  - retrieval_failed
  - evidence_accepted
  - evidence_rejected
```

Registration SHALL occur before:

- provider search;
- host caps;
- total candidate caps;
- third-party caps;
- type ranking;
- retrieval scheduling.

`seeds_registered` SHALL be true only when all valid explicit seeds have been
written to the immutable pre-budget seed registry.

Protected seed slots SHALL be reserved before ordinary candidate budgets.
Host and total caps SHALL not remove a valid explicit seed.

A registered seed that fails retrieval SHALL remain registered. Use
seed-specific failure codes rather than the generic mandatory-provider failure
code.


# 52. Version 1.1 Soft Lower-Bound Narrative-Length Contract

The narrative validator SHALL use a preferred range and a hard range.

Illustrative configuration:

```yaml
narrative_length:
  preferred_min_words: 160
  preferred_max_words: 260
  hard_min_words: 100
  hard_max_words: 320
```

A narrative below the preferred minimum MAY remain valid when:

- evidence is genuinely limited;
- all required substantive fields are present;
- limitations are explicit;
- no important confirmed fact is omitted.

A narrative below the hard minimum or above the hard maximum SHALL be invalid.

Length SHALL be calculated deterministically from rendered fields, excluding
JSON keys and URLs.


# 53. Version 1.2 Role-Aware Advisory Narrative-Length Contract

Narrative expectations SHALL adapt to company role and evidence coverage.

For an end user or Tier-1 with strong evidence, the narrative SHOULD explain:

- application;
- model and target;
- engineering bottleneck;
- NNC mapping;
- technical qualification step.

For a semiconductor vendor, it SHOULD explain:

- ecosystem relevance;
- whether evidence concerns internal use or customer enablement;
- potential integration/partner route;
- why normal end-user scoring is capped.

For a tool vendor or direct competitor, it SHOULD explain:

- overlapping workflow;
- differentiation or partnership boundary;
- why no ordinary sales-prospect score is assigned.

For research-only evidence, it SHOULD explain the transition required before NNC
becomes applicable.

The preferred word range is advisory. Substantive accuracy and role clarity take
precedence over padding.


# 54. Version 1.3 Substantive Gemma Assessment and Engineering-Need Contract

A valid narrative SHALL contain all of:

1. at least one confirmed company fact;
2. at least one neutral engineering need;
3. at least one verified NNC capability or an explicit no-fit explanation;
4. at least one material assumption, limitation, or unknown;
5. one practical qualification or next step.

For high or medium-high fit, the narrative SHALL explain the strongest mapping
chain.

For low or no fit, it SHALL explain which gate failed rather than provide generic
sales language.

The validator SHALL reject a paragraph that merely restates the score or lists
NNC features without connecting them to company evidence.


# 55. Version 1.4 dSPACE Application-Purpose Narrative Contract

When Neural Net Coder is applicable, the narrative SHALL explain its purpose in
the specific company context.

Acceptable purpose patterns include:

- converting a supported ONNX network into deterministic embedded C/C++;
- assessing RAM, ROM, stack, and execution-time fit before target integration;
- reducing manual model reimplementation;
- comparing reference model execution with generated code;
- supporting a traceable safety-oriented implementation workflow;
- integrating through a stand-alone or TargetLink route.

The narrative SHALL not present a generic product feature list unrelated to the
company's observed activity.


# 56. Version 1.5 Gemma2 Native-Context Protection Contract

The context builder SHALL keep the prompt within the configured Gemma context
window with margin for output.

It SHALL reduce context deterministically by:

1. removing duplicate passages;
2. retaining strongest evidence clusters;
3. retaining at least three distinct sources where available;
4. summarizing portfolio chunks without removing owner metadata;
5. excluding raw rejected-evidence text unless material;
6. excluding machine-readable trace details not needed for narrative.

Truncating the prompt at an arbitrary character boundary is prohibited.


# 57. Version 1.6 dSPACE Attribution-Scope Validation Contract

Attribution validation SHALL operate at sentence level and across adjacent
sentences.

The validator SHALL identify:

- grammatical subject;
- product alias;
- possessive relation;
- action verb;
- explicit owner phrase;
- nearby target-company name or pronoun.

Examples:

```text
Valid:
dSPACE Neural Net Coder may support the company's need for model-to-code
verification.

Invalid:
The company uses its Neural Net Coder to deploy the model.

Invalid unless evidenced:
The company selected NNC for the ECU.

Valid:
The company's own virtual-sensor software is a possible application for dSPACE
Neural Net Coder.
```

The validator SHALL not rely only on exact forbidden strings. It SHALL use
deterministic patterns, protected aliases, and sentence context.


# 58. Version 1.7 Gemma Narrative Length and Self-Revision Contract

The prompt MAY instruct Gemma to check its JSON and concision before returning
the final output. This remains one logical generation attempt.

Python SHALL still perform the authoritative checks.

No recursive open-ended self-revision loop is allowed. If the returned result is
invalid, the deterministic fallback SHALL be used.

The manifest SHALL distinguish:

```yaml
narrative_artifact_status:
  - llm_valid
  - llm_invalid_fallback_used
  - llm_timeout_fallback_used
  - llm_truncated_fallback_used
  - llm_ownership_violation_fallback_used
```


# 59. Version 1.0 Design-to-Implementation Alignment Contract

This document defines the intended new implementation; it does not assert that
the repository already exists or that the Power Electronics repository has been
copied.

The new implementation SHALL:

- use the identifiers in Section 0;
- retain the consolidated flat source-package approach;
- use ChromaDB directly;
- keep LlamaIndex optional;
- use the implemented v3 prompt filenames and ownership contract;
- maintain application version `2.0.0`;
- maintain runtime compatibility tag `1.0`;
- document actual module count and test count after implementation;
- record deviations in `docs/IMPLEMENTATION_NOTES.md`.

Architecture may be reused from
`C:\Users\ClaudioD\Desktop\BD-Agent-for-PwEl-v2.0`, but domain configuration,
portfolio corpus, prompts, tests, and regression data SHALL be NNC-specific.
Power Electronics scoring rules and portfolio products SHALL not be copied into
the active NNC configuration.


# 60. Version 1.0 Sales-Assessment Report Presentation Contract

The NNC report SHALL implement all presentation requirements inherited from the
Power Electronics Version 1.26 preview contract:

1. domain and country on separate lines below the title;
2. readable UTC generation timestamp;
3. `OVERALL ASSESSMENT` title;
4. `Applicability Mappings` before `Relevant Evidence`;
5. first mapping column `Matched dSPACE Product`;
6. second mapping column `Applicability Mapping`;
7. visible evidence descriptions shortened by approximately half;
8. unchanged internal evidence JSON;
9. every distinct applicable source listed with canonical URL;
10. human-readable PDF filename;
11. no overwrite of historical PDF or Markdown artifacts.

For this BDA, the mapping table's product cell SHALL use the validated
commercial name `Neural Net Coder`.

Automated tests SHALL compare extracted report text, section order, table
headers, company metadata, and evidence-display behavior.


# Appendix A — Architecture Parity Matrix

| Power Electronics BDA v1.26 element | NNC BDA equivalent | Change type |
|---|---|---|
| Repository and flat Python package | New NNC identifiers, same package architecture | Identifier |
| Companies.xlsx registry | Same workbook contract | Unchanged |
| Deterministic evidence pipeline | Same stages | Unchanged |
| Power-electronics taxonomy | Tiny-AI / Edge-AI taxonomy | Replaced |
| Engineering-need taxonomy | Embedded NN deployment and verification needs | Replaced |
| Multiple dSPACE power-electronics products | Single terminal product: Neural Net Coder | Replaced |
| Portfolio PDF corpus | Approved NNC product corpus | Replaced |
| ChromaDB + bge-large | Same technology, NNC collection | Retargeted |
| Gemma2:9b narrative | Same model and one-attempt policy | Unchanged |
| Multi-provider search | Same providers, NNC query families | Retargeted |
| Evidence, scoring, and manifests | Same artifact architecture | Unchanged |
| Product-ownership validation | Protect NNC, TargetLink, and dSPACE attribution | Retargeted |
| PDF/Markdown report | Same v1.26 layout | Unchanged except domain content |
| Regression data | 24 supplied Tiny-AI use cases plus negative controls | Replaced |
| Portfolio grounding gate | Mandatory NNC chunks | Unchanged mechanism |
| Search and quota controls | Same zero-cost and seed rules | Unchanged |


# Appendix B — Source Basis and Derivation Rules

This design was derived from the following supplied materials:

| Source | Primary design use |
|---|---|
| `BD-Agent-for-Power-Electronics_IMPLEMENTATION_SPEC_v1.26(1).md` | Authoritative architecture, runtime, evidence, search, portfolio, report, workbook, prompt, and reliability baseline |
| `NNC-List-of-TinyAI-Low-Power-EdgeAI-Use-Cases.xlsx` | 24 reference use cases, hardware aliases, industries, URLs, and regression fixtures |
| `NNC_Taxonomy_Machine_Learning_on_MCU_README_GitHub(1).md` | TinyML terminology, frameworks, model-compression methods, papers, and toolchain aliases |
| `consider the following list of virtual sensors or(1).md` | Virtual/soft-sensor discovery terms, NXP/Renesas/Arm-oriented examples, and candidate source patterns |
| `NNC-Sales-Playbook-&-Value-Proposition(1).pdf` | NNC purpose, ICP, value proposition, ONNX workflow, code generation, resource forecasting, optimization, verification, safety, and deployment routes |
| `Machine-Learning-Systems-Vol1.pdf` | Data–Algorithm–Machine reasoning, deployment paradigms, resource constraints, lifecycle, runtime and optimization concepts |
| `Machine-Learning-Systems-Vol2.pdf` | Energy measurement, reliability, security, governance, and operational controls |

Source-use rules:

1. The Power Electronics design controls architecture, not NNC domain meaning.
2. The NNC playbook controls product capability statements and product boundaries.
3. The use-case workbook supplies examples and regression fixtures, not automatic
   proof of current company activity.
4. The taxonomy and virtual-sensor lists supply discovery terms and literature
   leads; individual links still require retrieval and evidence validation.
5. The ML-systems books supply engineering concepts and terminology. They do not
   prove that Neural Net Coder implements every general ML-systems practice.
6. No external claim becomes a dSPACE product capability unless it appears in the
   approved NNC portfolio corpus.


# Appendix C — Normative Domain Configuration Example

The following illustrates the minimum active YAML structure.

```yaml
config_id: tiny_edge_ai_company_domain_taxonomy
config_version: 1.1.0
schema_version: 1.1.0
status: active

entity_scope: target_company

term_groups:
  neural_network:
    required_context: technical
    strong:
      - neural network
      - deep neural network
      - CNN
      - 1D CNN
      - LSTM
      - GRU
      - MLP
      - autoencoder
      - transformer
      - ONNX model
    weak:
      - AI
      - machine learning
      - data-driven

  embedded_target:
    strong:
      - microcontroller
      - MCU
      - ECU
      - Cortex-M
      - Cortex-R
      - bare metal
      - RTOS
      - embedded controller
    medium:
      - edge processor
      - embedded processor
      - system-on-chip
    negative:
      - cloud GPU
      - data center
      - server inference

  deployment:
    - ONNX
    - C code
    - C++
    - code generation
    - runtime
    - compiler
    - target deployment
    - production ECU
    - embedded software

  resources:
    - RAM
    - ROM
    - flash
    - stack
    - latency
    - execution time
    - power
    - energy
    - memory footprint
    - static allocation
    - no malloc

  optimization:
    - INT8
    - quantization
    - post-training quantization
    - pruning
    - distillation
    - fixed point
    - mixed precision

  verification:
    - back-to-back
    - MIL
    - SIL
    - PIL
    - numerical equivalence
    - MAE
    - MSE
    - RMSE

  safety:
    - MISRA C
    - ISO 26262
    - ISO/PAS 8800
    - functional safety
    - deterministic code
    - traceability

use_case_groups:
  virtual_sensor:
    - virtual sensor
    - soft sensor
    - virtual measurement
    - learned observer
    - state estimator
  condition_monitoring:
    - predictive maintenance
    - anomaly detection
    - condition monitoring
    - remaining useful life
  perception:
    - object detection
    - person counting
    - occupant detection
    - gesture recognition
    - keyword spotting
    - acoustic event detection
```

Normative exclusions:

```yaml
exclusions:
  - exclusion_id: EXC-NNC-001
    when:
      all:
        - model_class: non_neural
        - no_confirmed_neural_component: true
    effect:
      neural_network_gate: fail
      score_cap: 15

  - exclusion_id: EXC-NNC-002
    when:
      deployment_target: cloud_or_server_target
    effect:
      embedded_target_gate: fail
      score_penalty: 30

  - exclusion_id: EXC-NNC-003
    when:
      all:
        - company_role: semiconductor_vendor
        - evidence_type: silicon_capability_only
    effect:
      commercial_route: partner_or_ecosystem
      customer_score_cap: 40

  - exclusion_id: EXC-NNC-004
    when:
      company_role: direct_competitor
    effect:
      commercial_route: competitor
      customer_score: 0
```


# Appendix D — Engineering-Need and Capability Mapping Matrix

| Neutral engineering need | Triggering company evidence | NNC capability candidate | Required qualification |
|---|---|---|---|
| Trained-model handover | AI team and embedded team use separate toolchains | ONNX input workflow | Can the model export to supported ONNX? |
| Deterministic embedded code | Manual rewrite, runtime adaptation, C/C++ target | Deterministic C/C++ generation | Operator coverage, target compiler |
| Static memory implementation | No malloc, fixed memory, safety constraints | Static memory behavior | Exact generated memory layout |
| Resource-fit estimation | RAM/ROM/stack/latency limits | Resource forecast | Target clock, compiler, precision |
| Post-training optimization | Quantization or footprint pressure | Documented NNC optimization | Accuracy loss and supported precision |
| Accuracy preservation | Conversion or precision changes | Model/code comparison | Dataset and acceptance thresholds |
| Model-to-code equivalence | Reference model and generated code | Back-to-back verification | Metrics, tolerances, test vectors |
| Target execution verification | PIL or target execution | PIL workflow | Target interface and measurement setup |
| Safety-oriented implementation | MISRA, ISO 26262, ISO/PAS 8800 | Safety-oriented workflow | Safety plan and tool qualification scope |
| Stand-alone AI-to-C workflow | Code-first AI/embedded organization | Stand-alone GUI/CLI | CI integration and automation needs |
| TargetLink integration | Existing MBD/TargetLink workflow | TargetLink integration | Product version and integration scope |
| Cross-silicon portability | Multiple MCU families | Generic C/C++ handover | Target-specific libraries/accelerators |
| Power-budget validation | Always-on or battery operation | Resource/latency support only | Power must be measured on target; do not overclaim |
| Operator compatibility | Custom or unsupported graph operators | Compatibility assessment | Exact ONNX graph and opset |


# Appendix E — Supplied Use-Case Regression Catalog

The following rows SHALL seed the regression dataset. Expected results are
classification expectations for tests, not final assessments of the named
companies.

| # | Industry | Use case | Silicon / target | Expected model gate | Expected target gate | Expected NNC result |
|---:|---|---|---|---|---|---|
| 1 | Automotive | AI-Enhanced Virtual Wheel Force Transducer | NXP Semiconductors; S32K5 family zonal MCU. The article does not disclose the exact S32K5 part number. | NN confirmed | MCU confirmed | High |
| 2 | Automotive | Edge-AI Virtual-Sensor Deployment | NXP Semiconductors; S32K566 / S32K5 family. The page identifier references S32K566, while the visible technical description refers more genera... | NN/AI model strong | MCU confirmed | Medium-High |
| 3 | Automotive | Tire and Brake Wear Monitoring | Not disclosed; Not disclosed. The software can be deployed in the cloud or embedded in a vehicle ECU, but no MCU or processor is identified. | NN unconfirmed | ECU optional, MCU unknown | Medium |
| 4 | Automotive | Virtual Tire-Wear Monitoring | Not disclosed; Not disclosed — existing vehicle ECU. Tactile Mobility describes an ECU-embedded, low-footprint software implementation but doe... | NN unconfirmed | ECU embedded, MCU unknown | Medium |
| 5 | Automotive | Battery SOC/SOH Virtual Sensor | NXP Semiconductors for the documented MathWorks deployment demonstration; NXP S32K344, part of the S32K3 family, using an Arm Cortex-M7 core. ... | NN confirmed | S32K3 confirmed | High |
| 6 | Food & Beverage | Virtual Pressure Sensor | Not disclosed; Unspecified Arm Cortex-M microprocessor on the Coca-Cola Freestyle dispenser control board. No MCU manufacturer or product code... | Non-neural regression | Cortex-M confirmed | No Fit / Low |
| 7 | Off-Highway | Hydraulic Motor Temperature Soft Sensor | Not disclosed; Not disclosed — embedded target hardware only. Neither the MCU family nor the processor architecture is identified. | DNN alternative confirmed | Embedded target unknown | Medium-High conditional |
| 8 | Automotive | In-Cabin Acoustic Monitoring | Ambiq; Apollo4 Blue | NN proposed | Apollo4 confirmed | Partner / Exploratory |
| 9 | Medical & Wearables | Predictive Health Monitoring | Ambiq; Apollo5 / Apollo510 | NN confirmed | Apollo5 confirmed | Partner / Medium |
| 10 | Consumer & Industrial IoT | Voice and Object Recognition | Espressif; ESP32-S3 | NN applications confirmed | ESP32-S3 confirmed | Partner / Medium |
| 11 | Automotive | Motor Virtual Sensor | Infineon; AURIX™ TC4x | AI model, NN not certain | AURIX TC4x confirmed | Partner / Medium |
| 12 | Consumer & Smart Home | Multimodal Secure Sensing | Infineon; PSoC™ Edge | Multimodal AI, NN uncertain | PSoC Edge confirmed | Partner / Low-Medium |
| 13 | Consumer, Medical & IoT | Smart Audio and Gesture Recognition | Nordic Semiconductor; nRF54L Series / nRF54LM20B | TinyML models confirmed | nRF54L confirmed | Partner / Medium |
| 14 | Automotive | Indirect Tyre-Pressure Monitoring | NXP Semiconductors; S32K3 / i.MX RT1170 | NN proposed, exact project unconfirmed | S32K3/i.MX RT confirmed as platform | Low / Exploratory |
| 15 | Industrial | Predictive Motor Maintenance | NXP Semiconductors; i.MX RT Series, including RT1170 | ML model, NN uncertain | i.MX RT confirmed | Partner / Medium |
| 16 | Automotive | Predictive EV Range | Renesas; RH850 / U2B | NN exact use case unconfirmed | RH850/U2B confirmed as platform | Low / Exploratory |
| 17 | Medical, Consumer & Industrial | Touchless HMI | Renesas; RA8 / RA8D1 | Vision NN strongly implied | RA8D1 confirmed | Partner / Medium |
| 18 | Smart Home & IoT | Glass-Break Detection | Silicon Labs; xG24 / MG24 | ML inference confirmed, NN uncertain | xG24/MG24 confirmed | Partner / Medium |
| 19 | Automotive | Battery SoC and SoH Estimation | STMicroelectronics; Stellar P3E | Potential NN use case | Stellar P3E confirmed | Low / Exploratory |
| 20 | Industrial, Consumer & Smart Home | Edge Vision and Person Counting | STMicroelectronics; STM32N6 / STM32U5 | NN inference confirmed | STM32N6/U5 context | Partner / Medium-High |
| 21 | Automotive | Camera-Based Occupant Detection | Texas Instruments; Sitara AM62A-Q1 | Vision NN confirmed | AM62A-Q1 edge processor | Medium-High |
| 22 | Automotive | Virtual Piston-Pressure Sensor | Not disclosed; Powertrain ECU microcontroller; exact model not disclosed | LSTM confirmed | ECU confirmed, exact MCU unknown | High conditional |
| 23 | Automotive | Hybrid Battery SOC/SOH Estimation | NXP; MPC5746R | NN confirmed | MPC5746R confirmed | High |
| 24 | Industrial Automation | Edge-AI Predictive Maintenance | Arm provides processor IP; Intel supplies the cited IoT2040 processor; No specific MCU identified. Armv9-based sensors, SIMATIC S7-1500 PLC an... | AI anomaly detection, NN/MCU unknown | PLC/edge gateway | Low-Medium |

For every row, the regression fixture SHALL retain the complete supplied
description, companies involved, and reference URL outside this abbreviated
table.


# Appendix F — Qualification Question Library

The deterministic assessment SHALL select questions relevant to missing fields.

## Model and format

- What is the neural-network architecture?
- Which training framework and version are used?
- Can the trained model be exported to ONNX?
- Which ONNX opset and operators are required?
- Are custom operators or preprocessing stages present?
- Is inference stateful or recurrent?

## Target and compiler

- What MCU, ECU, core, accelerator, and compiler are used?
- Is the target bare metal, AUTOSAR, or RTOS-based?
- Is generic C/C++ acceptable, or are accelerator-specific kernels required?
- Are target libraries such as CMSIS-NN or vendor runtimes mandatory?

## Resources and performance

- What are the RAM, ROM/flash, stack, and execution-time budgets?
- What is the sample/inference rate and hard deadline?
- Which precision is required?
- What is the power or energy budget and duty cycle?
- Are resource estimates needed before hardware availability?

## Verification

- Which reference implementation is authoritative?
- Which input datasets and test vectors are available?
- Which error metrics and acceptance thresholds apply?
- Is SIL sufficient, or is PIL required?
- How are preprocessing and postprocessing compared?

## Safety and process

- Is the function safety-related or safety-critical?
- Which MISRA, ISO 26262, ISO/PAS 8800, or internal process requirements apply?
- Which artifacts are required for review and traceability?
- Is tool qualification or confidence-from-use required?
- How are model and dataset versions controlled?

## Organization and workflow

- Which team trains the model?
- Which team owns embedded integration?
- Is the preferred route stand-alone, CLI/CI, or TargetLink?
- Is manual rewrite currently required?
- How often is the model retrained or released?


# Appendix G — False-Positive and Exclusion Rules

| Pattern | Why it is risky | Required treatment |
|---|---|---|
| `AI-enabled MCU` product page | Describes silicon capability, not target-company use | Classify company role and require a concrete application |
| `virtual sensor` without model type | May be physical, statistical, or rule-based | Keep NN gate unknown |
| `machine learning` without architecture | May be non-neural | Discovery signal only |
| TensorFlow/PyTorch mention | Training framework does not prove embedded deployment | Require target or deployment evidence |
| MCU mention distant from AI text | May be unrelated content | Enforce local co-occurrence |
| ONNX on server | Format alone does not imply constrained deployment | Apply cloud/server classification |
| Quantization mention | May concern a non-NN algorithm or cloud model | Require model and target context |
| Edge AI gateway/PLC | May exceed MCU scope | Classify as non-constrained edge unless resources indicate otherwise |
| NPU-equipped chip | Hardware capability does not prove NNC need | Do not infer code-generation workflow |
| Linear regression soft sensor | Valuable Tiny-AI case but not NNC target | Non-neural classification |
| Kalman filter estimator | Not a neural network unless hybrid/NN component explicit | Do not pass NN gate |
| Vendor-specific code generator | Could be competitor or installed toolchain | Role and workflow analysis |
| Academic NN paper | May have no product or deployment intent | Research-only cap |
| Safety standard mention | Does not prove application certification | Treat as requirement, not status |
| `C code` mention | May be handwritten, generated, or unrelated | Require local model/deployment context |
| `linear quantization` in OBD or signal tables | Usually physical-value encoding/scaling, not NN compression | Negative override unless weights/activations/model precision occur locally |
| `ABS electronic control unit` in an owner's manual | Proves only an ordinary vehicle controller | Accept as contextual controller presence at most; mapping-ineligible |
| RAM/ROM/stack/watchdog diagnostics | Hardware self-test terms can mimic NNC resource vocabulary | Do not derive static-memory or resource-fit needs without local neural deployment |
| `embedded app` in search snippet | Search text may not describe ML or the retrieved passage | Require retrieved-content validation; snippet cannot satisfy a gate |
| Neural evidence in one source plus ECU evidence in another | Company-wide aggregation creates artificial applicability | Reject unless an exceptional project-linked context bundle is validated |
| Generic owner/OBD/service manual | High-volume documents contain many embedded terms | Candidate allowed; Relevant Evidence blocked by default |
| Ambiguous short company alias (`GM`) | Search providers may return unrelated material or match personal initials | Discovery only; require independent strong company anchor in retrieved source |
| `G.M.` in bibliography/editor name | Personal initials can collide with a company acronym | Attribution strength zero; `target_company_not_established` |
| Technically strong TinyML paper unrelated to company | Domain relevance is not company relevance | Store only as `general_industry_background`; zero score/mappings |
| Candidate registered during company scan | Search provenance can be mistaken for ownership/relationship | Persist `scan_target_company_id` separately; never auto-populate `attributed_company_id` |

## Appendix F.1 Opportunity-discovery taxonomy additions

The domain taxonomy SHALL include non-neural ML activities that are strong
qualification signals for future NNC deployment but are not yet NNC mappings.

```yaml
company_ml_opportunity_terms:
  model_activity:
    - supervised machine learning model
    - machine learning based approach
    - data-driven model
    - estimator
    - classifier
    - detector
    - recognition model
  use_case:
    - vehicle loading condition
    - operating condition recognition
    - state estimation
    - virtual sensor
    - soft sensor
    - sensorless estimation
    - anomaly detection
    - condition monitoring
    - predictive maintenance
  embedded_adjacent_context:
    - real-time
    - vehicle driving behavior
    - telematics unit
    - onboard
    - ADAS
    - vehicle dynamics
    - sensor data
    - control function
    - maintenance
  uncertainty_preserving_fields:
    - neural_model_status
    - model_architecture
    - embedded_execution_status
    - target_processor
    - onnx_status
```

These terms SHALL raise discovery and opportunity relevance only. They SHALL not
be aliases for `neural_network`, `microcontroller_deployment`, or `onnx_workflow`.

## Appendix G.1 Normative exclusion rules

```yaml
exclusions:
  - exclusion_id: NNC-FP-001
    name: Linear signal quantization is not neural quantization
    when:
      any_phrase:
        - linear quantization
        - signal quantization
        - diagnostic value quantization
      unless_local_context_has_any:
        - neural network weights
        - neural network activations
        - tensor precision
        - INT8 model
        - post-training quantization
        - quantization-aware training
        - ONNX model
    actions:
      - set_fact_class: confirmed_signal_encoding_or_scaling
      - set_mapping_eligible: false
      - add_reason_code: signal_quantization_not_model_quantization

  - exclusion_id: NNC-FP-002
    name: Generic ECU mention without neural deployment
    when:
      source_class_any:
        - vehicle_owner_manual
        - obd_or_diagnostic_manual
        - service_or_repair_manual
      has_any:
        - electronic control unit
        - ECU
        - microcontroller
        - RAM
        - ROM
        - stack
        - watchdog
        - ASIC
        - CPU
        - ADC
      lacks_context_bundle_dimension:
        - neural_model
        - deployment_workflow
    actions:
      - set_evidence_role: contextual_support_only
      - set_mapping_eligible: false
      - block_relevant_evidence_promotion: true
      - add_reason_code: target_only_no_neural_context

  - exclusion_id: NNC-FP-003
    name: Company-wide gate mixing
    when:
      mapping_dimensions_resolve_to_multiple_unlinked_context_bundles: true
    actions:
      - reject_mapping: true
      - add_reason_code: cross_document_gate_mixing
      - block_score_contribution: true
      - block_relevant_evidence_promotion: true

  - exclusion_id: NNC-FP-004
    name: Target company not established in retrieved source
    when:
      company_attribution_status_any:
        - not_established
        - contradicted
    actions:
      - set_source_attribution_scope: general_industry_background
      - block_target_company_evidence_extraction: true
      - set_mapping_eligible: false
      - block_score_contribution: true
      - block_relevant_evidence_promotion: true
      - add_reason_code: target_company_not_established

  - exclusion_id: NNC-FP-005
    name: Ambiguous short alias cannot establish company identity
    when:
      company_match_only_from_alias_class_any:
        - short_acronym
        - ambiguous_short_acronym
      strong_company_anchor_present: false
    actions:
      - set_company_attribution_status: not_established
      - set_mapping_eligible: false
      - block_target_company_evidence_extraction: true
      - add_reason_code: ambiguous_company_alias_only

  - exclusion_id: NNC-FP-006
    name: Personal initials and bibliography collisions are not company aliases
    when:
      company_alias_match_location_any:
        - bibliography
        - references
        - works_cited
        - author_or_editor_name
      match_form_any:
        - punctuation_separated_initials
        - personal_initials
      strong_company_anchor_present: false
    actions:
      - set_alias_match_strength: none
      - set_company_attribution_status: not_established
      - block_target_company_evidence_extraction: true
      - add_reason_code: bibliography_initials_alias_collision

  - exclusion_id: NNC-FP-007
    name: Cloud-only ML is not an embedded-deployment mapping
    when:
      explicit_execution_location_any:
        - cloud_only
        - server_only
        - datacenter_only
      embedded_adjacent_application_context_present: false
    actions:
      - set_mapping_eligible: false
      - set_nnc_opportunity_evidence_eligible: false
      - add_reason_code: cloud_only_non_embedded_ml
```

## Appendix G.2 Required General Motors false-positive regression fixtures

```yaml
false_positive_regression_fixtures:
  - fixture_id: GM-FP-OBD-LINEAR-QUANTIZATION
    source_class: obd_or_diagnostic_manual
    observed_terms:
      - ECU
      - microcontroller
      - RAM
      - ROM
      - stack
      - watchdog
      - ASIC
      - linear quantization
    local_subject: exhaust-gas and lambda diagnostic signal values
    expected:
      candidate_source: true
      neural_model_gate: fail
      model_quantization: false
      mapping_eligible: false
      relevant_evidence: false
      reason_codes:
        - signal_quantization_not_model_quantization
        - incomplete_context_bundle

  - fixture_id: GM-FP-OWNER-MANUAL-ABS-ECU
    source_class: vehicle_owner_manual
    observed_terms:
      - ABS electronic control unit
      - wheel-speed sensors
      - braking operation
    expected:
      candidate_source: true
      accepted_fact_class: confirmed_generic_controller_presence
      neural_model_gate: fail
      deployment_workflow_gate: fail
      mapping_eligible: false
      prohibited_derived_needs:
        - static_memory_implementation
        - resource_fit_estimation
        - cross_silicon_portability
      relevant_evidence: false
      reason_codes:
        - target_only_no_neural_context
        - generic_vehicle_manual

  - fixture_id: GM-FP-CROSS-DOCUMENT-MIXING
    inputs:
      - unrelated_gm_neural_network_source
      - unrelated_gm_deployment_workflow_source
      - owner_manual_generic_abs_ecu_source
    expected:
      company_profile_may_record_all_facts: true
      context_bundle_gate: fail
      applicability_mapping_created: false
      score_contribution: 0
      relevant_evidence_sources: []
      reason_code: cross_document_gate_mixing

  - fixture_id: GM-FP-AMBIGUOUS-ALIAS-TINYML-PAPER
    scan_target_company: General Motors
    discovery_query: '"GM" neural network microcontroller'
    source_title: TinyML for Small Microcontrollers
    source_class: academic_publication
    actual_source_affiliation: Universidad Nacional de La Plata
    technical_content:
      - TinyML
      - neural networks
      - convolutional neural networks
      - microcontrollers
      - TensorFlow Lite Micro
      - CMSIS-NN
      - EmbedIA
      - memory constraints
      - inference time
    company_match_artifact:
      token: G.M.
      location: bibliography_editor_name
      semantic_role: personal_initials
    expected:
      candidate_source: true
      technical_domain_relevance: high
      target_company_attribution_gate: fail
      attributed_company_id: null
      source_attribution_scope: general_industry_background
      target_company_evidence_records: 0
      mapping_eligible: false
      applicability_mapping_created: false
      score_contribution: 0
      relevant_evidence: false
      reason_codes:
        - target_company_not_established
        - ambiguous_company_alias_only
        - bibliography_initials_alias_collision
```


## Appendix G.3 Required Mahindra false-negative regression fixture

This fixture verifies discovery, organizational-unit attribution, and opportunity
evidence promotion without weakening the Version 1.1/1.2 mapping gates.

```yaml
false_negative_regression_fixture:
  fixture_id: MAHINDRA-FN-SAE-ML-LOAD-CONDITION
  scan_target_company: Mahindra & Mahindra Limited
  source_url: https://saemobilus.sae.org/papers/methodology-recognize-vehicle-loading-condition-indirect-method-using-telematics-machine-learning-2019-26-0019
  source_title: Methodology to Recognize Vehicle Loading Condition - An Indirect Method Using Telematics and Machine Learning
  source_class: academic_publication
  seed_url_required: false
  seed_url_used_for_acceptance_test: false
  publisher: SAE International
  author_affiliation: Mahindra Research Valley
  observed_content:
    - supervised machine learning model
    - real-time loading condition recognition
    - vehicle driving behavior
    - telematics units
    - small commercial vehicles
    - ADAS
    - maintenance application
  not_disclosed:
    - neural network architecture
    - CNN
    - LSTM
    - MLP
    - MCU execution
    - ECU execution
    - ONNX
    - generated C or C++
    - RAM or ROM envelope
    - deterministic latency
  expected:
    discovery_via_generic_query_family: true
    required_query_family: applied_ml_research
    target_company_attribution_gate: pass
    company_anchor_type: corporate_organizational_unit_affiliation
    relevance_class: nnc_opportunity_evidence
    technical_domain_relevance: high
    neural_model_gate: unconfirmed
    embedded_target_gate: unconfirmed
    deployment_workflow_gate: unconfirmed
    mapping_eligible: false
    applicability_mapping_created: false
    product_fit_score_contribution: 0
    relevant_evidence: true
    relevant_evidence_qualifier: neural architecture and embedded execution not disclosed
    qualification_questions:
      - What machine-learning model family was used?
      - Does inference execute onboard or in the cloud?
      - If onboard, what ECU/MCU/processor and deployment toolchain are used?
```

The implementation SHALL NOT satisfy this regression fixture by registering the
SAE URL as an explicit Mahindra seed. The source must be found through generic
query generation/provider execution or equivalent non-seed academic discovery.


## Appendix G.4 Required Mahindra Battery Health discovery regression fixture

This fixture verifies application-led discovery and retrieval ranking for a
company-authored technical presentation whose title does not contain the normal
NNC deployment vocabulary.

```yaml
false_negative_regression_fixture:
  fixture_id: MAHINDRA-FN-MATHWORKS-BATTERY-HEALTH
  scan_target_company: Mahindra & Mahindra Limited
  source_url: https://www.mathworks.com/content/dam/mathworks/mathworks-dot-com/solutions/aerospace-defense/files/2017/expo-in/intelligent-system-for-battery-health-monitoring.pdf
  source_title: Intelligent System for Battery Health Monitoring
  source_class: technical_presentation
  publisher: MathWorks
  event: MATLAB EXPO 2017
  seed_url_required: false
  seed_url_used_for_acceptance_test: false

  discovery_expectation:
    query_family_any:
      - use_case_led_battery
      - engineering_publisher_mathworks
    application_only_query_executed: true
    expected_example_queries:
      - '"Mahindra" "battery health"'
      - '"Mahindra" ("state of health" OR SOH) battery'
      - 'site:mathworks.com "Mahindra" ("battery health" OR "state of health")'

  observed_company_identity:
    - Mahindra Research Valley
    - Mahindra & Mahindra Ltd copyright

  observed_technical_content:
    - battery health monitoring
    - state of health
    - battery life prediction
    - battery prognostics
    - adaptive neuro-fuzzy classifier
    - neural-network adaptation
    - artificial neural network representation
    - MATLAB ANFIS

  not_disclosed:
    - ECU execution
    - MCU execution
    - ONNX
    - generated C or C++
    - target RAM or ROM
    - target latency

  expected:
    candidate_discovered: true
    candidate_selected_for_retrieval: true
    target_company_attribution_gate: pass
    use_case_class: battery_health_and_state_estimation
    hybrid_neural_model_status: confirmed
    neural_component_status: confirmed
    direct_nnc_onnx_compatibility: unconfirmed
    embedded_target_gate: unconfirmed
    relevance_class: nnc_opportunity_evidence
    relevant_evidence: true
    mapping_eligible: false
    product_fit_score_contribution: 0
    qualification_questions:
      - Can the neural component be exported as a supported ONNX graph?
      - Is the estimator intended to execute in a BMS/ECU or other constrained target?
      - What processor, memory, latency, and precision constraints apply?
```

The implementation SHALL NOT satisfy this fixture by adding the URL as a Mahindra
seed. Discovery and selection must result from generic use-case and
engineering-publisher rules.
## Appendix G.5 Required Mahindra SAE professional-publication regression fixture

```yaml
false_negative_regression_fixture:
  fixture_id: MAHINDRA-FN-SAE-VEHICLE-LOADING-ML
  scan_target_company: Mahindra & Mahindra Limited
  source_url: https://saemobilus.sae.org/papers/methodology-recognize-vehicle-loading-condition-indirect-method-using-telematics-machine-learning-2019-26-0019
  source_title: Methodology to Recognize Vehicle Loading Condition - An Indirect Method Using Telematics and Machine Learning
  publisher: SAE International
  source_category: professional_applied_ml_publication
  seed_url_required: false
  seed_url_used_for_acceptance_test: false

  expected_discovery:
    atomic_query_family_executed: true
    expected_query_variants_any:
      - 'site:saemobilus.sae.org/papers "Mahindra Research Valley" "machine learning"'
      - 'site:saemobilus.sae.org/papers Mahindra telematics'
      - 'site:saemobilus.sae.org/papers Mahindra "loading condition"'
      - '"Mahindra Research Valley" telematics "machine learning"'
      - '"Mahindra Research Valley" SAE "machine learning"'
    zero_result_provider_fallback_enabled: true
    minimum_successful_general_web_providers: 1

  observed_company_attribution:
    authors:
      - Vaisakh Venugopal
      - Paul Raj Bob
      - Vipin Nair
    affiliation:
      - Mahindra Research Valley

  observed_application:
    supervised_machine_learning_model: confirmed
    real_time_loading_condition_recognition: confirmed
    vehicle_driving_behavior: confirmed
    telematics: confirmed
    ADAS_application: confirmed
    indirect_sensorless_detection: confirmed

  not_disclosed:
    - neural_network_architecture
    - MCU_execution
    - ECU_execution
    - ONNX
    - C_or_CPP_generation

  expected_classification:
    target_company_attribution_gate: pass
    use_case_class:
      - indirect_physical_state_and_virtual_sensing
      - vehicle_operating_condition_recognition
    source_category: professional_applied_ml_publication
    neural_model_status: unconfirmed
    embedded_execution_status: unconfirmed
    relevance_class: nnc_opportunity_evidence
    relevant_evidence: true
    mapping_eligible: false
    score_contribution: 0
```

The acceptance test SHALL fail if the source is retrieved only because the exact
URL was inserted as an explicit Mahindra seed.
## Appendix G.6 Required GM patent-discovery regression fixture

```yaml
false_negative_regression_fixture:
  fixture_id: GM-FN-PATENT-TRACTIVE-LIMIT-WHEEL-STABILITY
  scan_target_company: General Motors
  source_url: https://patents.google.com/patent/US12246700B2/en
  source_title: Machine learning-based tractive limit and wheel stability status estimation
  publication_number: US12246700B2
  source_category: target_company_patent

  seed_url_required: false
  seed_url_used_for_acceptance_test: false

  attribution:
    expected_current_assignee: GM Global Technology Operations LLC
    expected_original_assignee: GM Global Technology Operations LLC
    expected_company_attribution: established
    expected_anchor: validated_patent_assignee

  expected_discovery:
    broad_ml_patent_query_executed: true
    use_case_patent_query_executed: true
    host_restricted_patent_query_executed: true
    expected_query_variants_any:
      - '"General Motors" patent "machine learning"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "machine learning"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "state estimation"'
      - '"General Motors" patent "wheel stability"'
      - '"General Motors" patent "tractive limit"'
      - 'site:patents.justia.com "GM Global Technology Operations LLC" "machine learning"'
    zero_result_cross_provider_fallback: true

  observed_technical_content:
    machine_learning_regression_model: confirmed
    machine_learning_classification_model: confirmed
    tractive_limit_estimation: confirmed
    wheel_stability_status_estimation: confirmed
    wheel_regions:
      - linear
      - near_peak
      - saturated
    onboard_sensor_inputs: confirmed
    onboard_controller_inputs: confirmed
    programmable_or_dedicated_electronic_control_unit: confirmed
    control_applications:
      - traction_control
      - yaw_control
      - antilock_braking
    neural_network:
      explicit_dependent_claim: confirmed
      evidence_strength: claimed_optional_embodiment
      selected_or_production_model: unconfirmed

  expected_classification:
    company_attribution_status: established
    source_category: target_company_patent
    applied_ml_activity:
      regression_model: confirmed
      classification_model: confirmed
    use_case:
      indirect_physical_state_and_virtual_sensing: confirmed
      vehicle_dynamics_learned_estimation: confirmed
      tractive_limit_estimation: confirmed
      wheel_stability_estimation: confirmed
    onboard_context: confirmed
    electronic_control_unit_implementation_possible: confirmed
    neural_model_status: possible_but_not_selected_or_confirmed
    patent_neural_evidence_strength: claimed_optional_embodiment
    ONNX_status: unconfirmed
    code_generation_status: unconfirmed
    relevance_class: nnc_opportunity_evidence
    relevant_evidence: true
    mapping_eligible: false
    score_contribution: 0

  expected_report:
    relevant_evidence_contains_source: true
    applicability_mapping_required: false
    score_may_remain_zero_from_this_source_alone: true
```

The acceptance test SHALL fail if the patent is discovered only because its exact
URL or publication number was added as a General Motors seed. The production
fix is the generic patent-discovery taxonomy, assignee resolution, query
generation, provider fallback, and retrieval ranking.

## Appendix G.7 Required predictive-battery patent regression fixture

```yaml
false_negative_regression_fixture:
  fixture_id: GM-FN-PATENT-PREDICTIVE-BATTERY-VIRTUAL-MEASUREMENTS
  scan_target_company: General Motors
  source_url: https://patents.google.com/patent/US20240302440A1/en
  source_title: Dynamic and predictive control of battery charging
  publication_number: US20240302440A1
  source_category: target_company_patent

  seed_url_required: false
  seed_url_used_for_acceptance_test: false

  attribution:
    expected_current_assignee: GM Global Technology Operations LLC
    expected_original_assignee: GM Global Technology Operations LLC
    expected_company_attribution: established
    expected_anchor: validated_patent_assignee

  expected_discovery:
    industry_baseline_family_selected:
      - battery_virtual_measurement_and_predictive_control
    application_only_patent_query_executed: true
    application_plus_ml_patent_query_executed: true
    host_restricted_patent_query_executed: true
    expected_query_variants_any:
      - '"General Motors" patent "battery charging"'
      - '"General Motors" patent "predictive charging"'
      - '"General Motors" patent "virtual measurement"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "battery charging"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "virtual measurement"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "battery charging" "machine learning"'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "data-driven" estimator'
      - 'site:patents.google.com/patent "GM Global Technology Operations LLC" "neural network" BMS'
      - 'site:patents.justia.com "GM Global Technology Operations LLC" "battery charging"'
    zero_result_cross_provider_fallback: true

  observed_use_case:
    real_time_predictive_battery_charging: confirmed
    virtual_or_latent_variables:
      - anode_potential_or_voltage
      - electrolyte_concentration
      - capacity_loss
      - aging_parameter
      - lithium_plating_related_limit
    hybrid_physics_data_driven_estimation: confirmed
    neural_network_estimator_embodiment: confirmed
    neural_network_learning_agent: confirmed
    adaptive_charging_calibration: confirmed

  observed_onboard_context:
    rechargeable_energy_storage_controller: confirmed
    onboard_charging_module: confirmed
    battery_management_controller: confirmed
    dedicated_processing_component: confirmed

  unconfirmed:
    - production_selected_neural_architecture
    - ONNX
    - generated_C_or_CPP
    - NNC_supported_operator_set
    - MCU_family
    - explicit_RAM_ROM_latency_constraints

  expected_classification:
    company_attribution_status: established
    source_category: target_company_patent
    use_case:
      - battery_health_and_state_estimation
      - battery_virtual_measurement_and_predictive_control
      - indirect_physical_state_and_virtual_sensing
    neural_component_roles:
      estimator: confirmed_as_embodiment
      learning_agent: confirmed_as_embodiment
    onboard_context: confirmed
    neural_model_status: confirmed_as_embodiment_but_production_selection_unconfirmed
    ONNX_status: unconfirmed
    embedded_code_generation: unconfirmed
    relevance_class: nnc_opportunity_evidence
    relevant_evidence: true
    mapping_eligible: false
    score_contribution: 0

  expected_report:
    relevant_evidence_contains_source: true
    preserve_virtual_measurement_use_case: true
    preserve_neural_learning_agent_role: true
    applicability_mapping_required: false
```

The acceptance test SHALL fail if discovery depends on the exact patent URL,
publication number, or a General Motors-specific seed. The production fix is
taxonomy-driven patent query generation from industry baseline use cases,
validated assignee identities, patent-host/classification expansion, provider
fallback, and role-aware patent evidence extraction.

## Appendix G.8 Required dual-GM patent-native discovery regression

This fixture verifies the patent search process rather than the downstream
taxonomy alone.

```yaml
patent_native_regression_fixture:
  fixture_id: GM-FN-PATENT-NATIVE-DUAL-DISCOVERY
  scan_target_company: General Motors
  validated_assignee:
    assignee_name: GM Global Technology Operations LLC
    validation_status: established

  prohibited_production_inputs:
    exact_seed_urls:
      - https://patents.google.com/patent/US12246700B2/en
      - https://patents.google.com/patent/US20240302440A1/en
    publication_numbers:
      - US12246700B2
      - US20240302440A1

  required_process:
    patent_native_assignee_enumeration: true
    metadata_records_requested_beyond_first_ten: true
    pagination_state_persisted: true
    provider_quality_contract_enforced: true
    non_patent_job_results_rejected: true
    quality_based_fallback_enabled: true
    local_metadata_corpus_built: true
    every_required_core_term_applied: true
    family_specific_retrieval_reservations_applied: true
    full_text_selected_after_local_ranking: true

  required_term_coverage:
    vehicle_dynamics_learned_estimation:
      - tractive limit
      - traction limit
      - wheel stability
      - wheel slip
      - tire saturation
      - tire-road friction
      - regression model
      - classification model

    battery_virtual_measurement_and_predictive_control:
      - predictive charging
      - dynamic charging
      - charging control
      - virtual measurement
      - calculated performance variable
      - anode voltage
      - electrolyte concentration
      - lithium plating
      - neural network learning agent

  expected_discovered_patents:
    - publication_number: US12246700B2
      expected_family: vehicle_dynamics_learned_estimation
      expected_relevance_class: nnc_opportunity_evidence
      expected_relevant_evidence: true
      expected_mapping_eligible: false

    - publication_number: US20240302440A1
      expected_family: battery_virtual_measurement_and_predictive_control
      expected_relevance_class: nnc_opportunity_evidence
      expected_relevant_evidence: true
      expected_mapping_eligible: false

  synthetic_provider_tests:
    first_page_contains_only_irrelevant_results:
      expected_fallback: true

    target_patent_is_on_page_three:
      expected_discovery: true

    nominal_patent_provider_returns_job_ads:
      expected_quality_status: unusable
      expected_reason_code: non_patent_results_from_patent_provider
      expected_fallback: true

    family_implementation_uses_only_first_term:
      expected_acceptance: fail
      expected_reason_code: PATENT-DISC-005
```

The test SHALL pass through assignee enumeration and local corpus ranking. The
known publication numbers are test assertions only and SHALL not be supplied to
the production discovery pipeline.

# Appendix H — Initial Implementation File Set

The first implementation increment SHOULD create and validate:

```text
config/domains/tiny_edge_ai/company_domain_taxonomy.yaml
config/domains/tiny_edge_ai/company_domain_layers.yaml
config/domains/tiny_edge_ai/engineering_need_taxonomy.yaml
config/domains/tiny_edge_ai/use_case_taxonomy.yaml
config/domains/tiny_edge_ai/hardware_target_taxonomy.yaml
config/domains/tiny_edge_ai/model_and_framework_taxonomy.yaml
config/domains/tiny_edge_ai/search_profiles.yaml
config/domains/tiny_edge_ai/query_templates.yaml
config/domains/tiny_edge_ai/exclusions.yaml
config/domains/tiny_edge_ai/scoring_rules.yaml
config/domains/tiny_edge_ai/page_relevance.yaml
config/domains/tiny_edge_ai/company_identity_rules.yaml
config/domains/tiny_edge_ai/company_alias_policy.yaml
config/domains/tiny_edge_ai/patent_discovery.yaml
config/domains/tiny_edge_ai/patent_use_case_terms.yaml
config/domains/tiny_edge_ai/patent_classification_taxonomy.yaml
config/domains/tiny_edge_ai/patent_provider_quality.yaml
config/domains/tiny_edge_ai/schemas/patent_discovery.schema.json
config/domains/tiny_edge_ai/schemas/patent_metadata_record.schema.json
config/domains/tiny_edge_ai/schemas/patent_provider_quality.schema.json
config/domains/tiny_edge_ai/schemas/patent_term_coverage.schema.json

config/dspace_portfolio/dspace_portfolio_index.yaml
config/dspace_portfolio/dspace_portfolio_profiles.yaml
config/dspace_portfolio/dspace_portfolio_aliases.yaml
config/dspace_portfolio/applicability_mapping_rules.yaml

data/nnc_reference_use_cases/use_cases_v1.json
data/nnc_reference_use_cases/expected_classifications_v1.json
```

Each YAML configuration SHALL have a versioned JSON Schema. The regression JSON
files SHALL also be schema-validated.


# Appendix I — Initial Implementation Sequence

Recommended implementation order:

1. copy the Version 1.26 repository into the new NNC repository;
2. change distribution, package, directory, CLI, and manifest identifiers;
3. remove active Power Electronics domain configuration and product profiles;
4. create NNC taxonomy and schemas;
5. import the 24 use cases as regression fixtures;
6. implement company-alias risk classes and the document-level target-company attribution gate;
7. separate `scan_target_company_id` from `attributed_company_id` in candidate and evidence artifacts;
8. implement neural, target, deployment, role, context-locality, and source-promotion gates;
9. implement evidence-role, background-evidence, and mapping-eligibility separation;
10. implement quantization ambiguity rules and negative-context overrides;
11. add the four General Motors false-positive regression fixtures;
12. add the Mahindra SAE false-negative regression fixture with seedless discovery;
13. implement `nnc_opportunity_evidence` taxonomy, claim ceilings, and report promotion;
14. implement generic corporate-organizational-unit affiliation resolution;
15. create NNC applicability rules and score trace;
16. prepare and approve the NNC portfolio document index;
17. ingest and validate the NNC ChromaDB collection;
18. adapt query templates and provider tests, including mandatory applied-ML academic queries;
19. implement use-case-led query ladders, industry-weighted query-budget reservation, engineering-publisher profiles, candidate scoring, and diversity quotas;
20. add the Mahindra MathWorks Battery Health false-negative regression fixture with seedless discovery;
21. implement professional-applied-ML publication taxonomy, atomic publisher queries, and zero-result cross-provider fallback;
22. add the Mahindra SAE vehicle-loading false-negative regression fixture with seedless discovery;
23. implement patented applied-ML discovery, validated patent-assignee profiles, patent host parsing, query-budget reservation, and zero-result cross-provider fallback;
24. implement patent neural-evidence strength classification and target-company-patent opportunity promotion;
25. add the GM US12246700B2 seedless patent-discovery regression fixture;
26. implement taxonomy-driven patent use-case query ladders and industry baseline patent families;
27. implement latent/virtual physical-variable semantics, battery predictive-control terms, patent-classification expansion, and role-aware hybrid estimator/controller extraction;
28. add the US20240302440A1 seedless predictive-battery patent regression fixture;
29. replace ordinary-web-first patent discovery with patent-native validated-assignee metadata enumeration;
30. implement patent metadata pagination, normalized patent-record schemas, local assignee corpus persistence, and separate metadata/full-text budgets;
31. enforce patent-provider result-quality validation and quality-based fallback for non-patent, irrelevant, and zero-usable-result sets;
32. implement complete required-synonym coverage instead of first-term-only family searches;
33. implement local deterministic patent metadata ranking and use-case-family full-text retrieval reservations;
34. implement CPC/IPC, patent-family, related-application, cited/citing, and same-assignee neighborhood expansion;
35. add the dual-GM patent-native discovery regression, including page-depth, irrelevant-first-page, broken-provider, and first-term-only tests;
36. adapt prompt ownership and substantive validation;
37. adapt report wording while retaining Version 1.26 layout;
38. run unit and integration tests;
39. run controlled example companies;
40. compare artifacts against this specification;
41. document every deviation.


# Appendix J — Document Change Log

| Version | Date | Description |
|---|---|---|
| 1.8.0 | 2026-08-04 | Replaced ordinary-web-first patent discovery with patent-native validated-assignee enumeration; added metadata pagination and local assignee corpus ranking, strict patent-provider quality validation, quality-based fallback, complete required-term coverage, separate patent budgets, family-specific retrieval reservations, CPC/family/citation expansion, patent search artifacts and completeness states, and a seedless dual-GM patent regression requiring both US12246700B2 and US20240302440A1 |
| 1.7.0 | 2026-08-04 | Added taxonomy-driven patent use-case query ladders, industry baseline patent families, latent/virtual physical-variable semantics, predictive battery-charging and electrochemical-state terms, hybrid physics/data-driven estimator and neural learning-agent roles, patent-classification expansion, stronger patent ranking, and seedless US20240302440A1 regression fixture |
| 1.6.0 | 2026-08-04 | Added mandatory patented applied-ML discovery, patent query-budget reservation, validated patent-assignee profiles, atomic Google Patents/Justia queries, patent zero-result cross-provider fallback, vehicle-dynamics learned-estimation taxonomy, patent neural-claim evidence strength, target-company-patent Relevant Evidence promotion, and seedless GM US12246700B2 regression fixture |
| 1.5.0 | 2026-08-04 | Added professional-applied-ML publication taxonomy, indirect physical-state/vehicle-loading discovery lexicon, atomic SAE/publisher queries, zero-result cross-provider fallback, stronger technical-publication ranking, and seedless Mahindra SAE vehicle-loading regression fixture |
| 1.4.0 | 2026-08-04 | Added use-case-led discovery/query ladders, battery/SOH/RUL/BMS discovery lexicon, ANFIS/ANFC neuro-fuzzy semantics, engineering-publisher profiles (including MathWorks/SAE), reserved query budgets, deterministic retrieval-priority scoring and diversity quotas, and seedless Mahindra Battery Health regression fixture |
| 1.3.0 | 2026-08-03 | Added company-specific `nnc_opportunity_evidence`, broadened academic/applied-ML discovery including SAE/DOI query families, generic corporate R&D-unit affiliation resolution, seedless Mahindra SAE regression fixture, and two-path Relevant Evidence promotion while preserving strict mapping gates |
| 1.2.0 | 2026-08-03 | Added hard target-company identity/attribution gate, short-alias risk policy, separation of scan provenance from source attribution, background-evidence isolation, and GM `G.M.` bibliography collision regression fixture |
| 1.1.0 | 2026-08-03 | Corrected GM false positives by adding context-bundle locality, quantization disambiguation, generic-manual promotion blocks, mapping-eligibility separation, and Relevant Evidence gating |
| 1.0.0 | 2026-07-28 | Initial authoritative design for BDA for Neural Net Coder, mapped from the Power Electronics BDA Version 1.26 and supplied Tiny-AI / Edge-AI source materials |