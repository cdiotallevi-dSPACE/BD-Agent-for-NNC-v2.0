# BDA for NNC v2.0

Local, evidence-first Business Development Agent for dSPACE Neural Net Coder.
It discovers public evidence about neural networks deployed on low-power
microcontrollers and constrained ECUs, applies deterministic semantic gates,
retrieves authoritative Neural Net Coder evidence from ChromaDB, and produces
auditable Markdown/PDF sales assessments.

The application keeps three semantic scopes separate: target-company facts,
neutral engineering needs, and verified dSPACE portfolio capabilities. Generic
AI/ML language is not sufficient to pass the neural-network gate. Training-only,
cloud-only, and non-neural evidence cannot silently become a positive NNC fit.

## Quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,vector]"
bda validate-config
bda validate-search-providers
bda validate-models
```

Place approved Neural Net Coder product PDFs in
`data/dspace_portfolio_documents`, then build the mandatory persistent index:

```powershell
bda ingest-dspace-portfolio --source data/dspace_portfolio_documents --rebuild
bda validate-portfolio-index
bda inspect-portfolio-index
```

Add or review companies in `data/Companies.xlsx`. The worksheet must be named
`Companies`; rows whose `Scan Y/N` value is `Y` are processed sequentially:

```powershell
bda scan-registry
```

On Windows, `Run-BDA.cmd` performs the validation and registry cycle.

Positive recommendations require authoritative Neural Net Coder chunks retrieved
from the local ChromaDB collection. `bge-large` is used for embeddings and one
`gemma2:9b` narrative attempt is made after deterministic scoring. LLM failure
does not change scores or grounding decisions.

The result does not prove purchase intent, compatibility, certification, or
current use of Neural Net Coder. Respect robots.txt, source terms, copyright,
privacy, and configured zero-cost search budgets.
