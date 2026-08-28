from pathlib import Path
import json
import typer
from dotenv import load_dotenv
from .config_manager import load_yaml, validate_all
from .pipeline import Pipeline
from .core import atomic_json, run_timestamp, sha256_text, slugify, utc_now
from .workbook import selected_companies, update_rating, queue_pending
from .model_runtime import validate_models as run_model_validation
from .portfolio_index import ingest, retrieve, validate_index, ChromaPortfolioStore
from .search_models import CompanySearchContext, SearchQuery
from .provider_registry import PROVIDERS
from .search_orchestrator import discover_sync, load_company_profile
from .provider_quota_ledger import ProviderQuotaLedger, QuotaUnavailable
from .credential_manager import credential_status, resolve_credential
from .provider_cycle_state import ProviderCycleState

# Load local credentials for every CLI entry point without replacing any
# environment variable explicitly supplied by the operator or process.
load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

app=typer.Typer(no_args_is_help=True)
def root() -> Path: return Path(__file__).resolve().parents[2]

@app.command("show-search-credentials")
def show_search_credentials():
    cfg=load_yaml(root()/"config/search_providers.yaml")
    provider_ids=("brave","serpapi","serper")
    result={"credentials":[credential_status(provider_id,cfg["providers"].get(provider_id,{})) for provider_id in provider_ids]}
    typer.echo(json.dumps(result,indent=2))

@app.command("validate-config")
def validate_config():
    errors=validate_all(root()/"config")
    if errors:
        for e in errors: typer.echo(e,err=True)
        raise typer.Exit(1)
    typer.echo("Configuration valid")

@app.command("validate-models")
def validate_models():
    result=run_model_validation()
    typer.echo(json.dumps(result,indent=2))
    if not result["semantic_runtime_ready"]:
        typer.echo("ERROR: bge-large is required; semantic indexing and retrieval are blocked.",err=True)
        raise typer.Exit(2)
    if not result["final_report_runtime_ready"]:
        typer.echo("WARNING: gemma2:9b unavailable; deterministic report fallback will be used.",err=True)

@app.command("validate-installation")
def validate_installation():
    import importlib
    missing=[]
    for package in ("chromadb","pymupdf","httpx","ollama","ddgs"):
        try: importlib.import_module(package)
        except ImportError: missing.append(package)
    if missing:
        typer.echo(f"Missing mandatory dependencies: {', '.join(missing)}",err=True)
        raise typer.Exit(2)
    typer.echo("Mandatory portfolio-index and company-search dependencies are installed")

@app.command("validate-search-providers")
def validate_search_providers():
    import asyncio, tempfile
    from .config_manager import load_yaml
    cfg=load_yaml(root()/"config/search_providers.yaml")
    report={"providers":{},"ddgs_smoke_query":None,"normalization_valid":False,"cache_read_write_valid":False,"sitemap_parser_valid":False,"pdf_parser_valid":False}
    for provider_id, provider_cfg in cfg["providers"].items():
        if not provider_cfg.get("enabled"): continue
        report["providers"][provider_id]={"required":provider_cfg.get("required",False),"available":provider_id in PROVIDERS}
    try:
        query=SearchQuery("smoke_0001","site:example.com Tiny-AI Edge-AI","diagnostic",mandatory=True)
        context=CompanySearchContext("Example","example.com",max_results=1,timeout_seconds=10)
        results=asyncio.run(PROVIDERS["ddgs"]().execute(query,context))
        report["ddgs_smoke_query"]={"state":"provider_completed","results":len(results)}
        report["normalization_valid"]=all(r.provider_id=="ddgs" and r.url.startswith(("http://","https://")) for r in results)
    except Exception as exc:
        report["ddgs_smoke_query"]={"state":"provider_failed","error":{"type":type(exc).__name__,"message":str(exc)}}
    try:
        from .core import atomic_json
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"cache.json"; atomic_json(path,{"ok":True})
            report["cache_read_write_valid"]=json.loads(path.read_text())["ok"]
        import xml.etree.ElementTree as ET, fitz
        report["sitemap_parser_valid"]=ET.fromstring(b"<urlset/>").tag=="urlset"
        pdf=fitz.open(); pdf.new_page(); report["pdf_parser_valid"]=pdf.page_count==1; pdf.close()
    except Exception:
        pass
    required_missing=[p for p,v in report["providers"].items() if v["required"] and not v["available"]]
    report["ready"]=not required_missing and report["ddgs_smoke_query"]["state"]=="provider_completed" and report["cache_read_write_valid"] and report["sitemap_parser_valid"] and report["pdf_parser_valid"]
    typer.echo(json.dumps(report,indent=2))
    if not report["ready"]: raise typer.Exit(2)

def _quota_runtime():
    cfg=load_yaml(root()/"config/search_providers.yaml")
    metered={key:value for key,value in cfg["providers"].items() if value.get("period_type") in {"calendar_month","nonrenewing"}}
    return cfg,ProviderQuotaLedger(root()/cfg["search_cost_policy"]["ledger_path"],metered)

@app.command("validate-free-search-config")
def validate_free_search_config():
    cfg,ledger=_quota_runtime(); policy=cfg["search_cost_policy"]; errors=[]; providers=[]
    if policy.get("mode")!="zero_cost_only": errors.append("search mode must be zero_cost_only")
    for prohibited in ("paid_overage_allowed","automatic_plan_upgrade_allowed","automatic_credit_purchase_allowed"):
        if policy.get(prohibited): errors.append(f"{prohibited} must be false")
    for provider_id,p in cfg["providers"].items():
        state="disabled" if not p.get("enabled") else "available"
        credential=credential_status(provider_id,p)
        env=credential["canonical_env"]
        if p.get("enabled") and env and not credential["configured"]: state="missing_credentials"
        if p.get("period_type") and (not isinstance(p.get("configured_hard_cap"),int) or p["configured_hard_cap"]<=0): errors.append(f"{provider_id}: invalid hard cap")
        if p.get("advertised_free_allowance") and p.get("configured_hard_cap",0)>p["advertised_free_allowance"]*(1-policy.get("reserve_percent_default",10)/100): errors.append(f"{provider_id}: hard cap does not preserve reserve")
        providers.append({"provider_id":provider_id,"state":state,"credential_env":env,"credential_source_env":credential["source_env"],"alias_used":credential["alias_used"],"concrete_adapter":provider_id in PROVIDERS})
    snapshot=ledger.snapshot(); result={"mode":policy["mode"],"paid_overage_allowed":policy["paid_overage_allowed"],"ledger_path":str(ledger.path),"ledger_writable":ledger.path.exists(),"providers":providers,"quota":snapshot,"errors":errors,"valid":not errors}
    typer.echo(json.dumps(result,indent=2));
    if errors: raise typer.Exit(2)

@app.command("show-search-quota")
def show_search_quota():
    _,ledger=_quota_runtime(); typer.echo(json.dumps(ledger.snapshot(),indent=2))

@app.command("reconcile-search-quota")
def reconcile_search_quota():
    _,ledger=_quota_runtime(); typer.echo(json.dumps({"status":"reconciled_from_conservative_local_ledger","ledger":ledger.snapshot()},indent=2))

@app.command("test-search-provider")
def test_search_provider(provider: str=typer.Option(...)):
    import asyncio
    cfg,ledger=_quota_runtime(); p=cfg["providers"].get(provider)
    if not p or provider not in PROVIDERS or not p.get("endpoint"):
        typer.echo(f"Unknown or non-API provider: {provider}",err=True); raise typer.Exit(2)
    key=resolve_credential(provider,p)["value"]
    if not key:
        typer.echo(json.dumps({"provider_id":provider,"state":"missing_credentials","request_attempted":False},indent=2)); return
    try: ledger.reserve(provider)
    except QuotaUnavailable as exc:
        typer.echo(json.dumps({"provider_id":provider,"state":exc.state,"request_attempted":False},indent=2)); return
    query=SearchQuery("diagnostic_0001","site:example.com Tiny-AI Edge-AI","diagnostic",mandatory=False,target_provider_ids=(provider,))
    context=CompanySearchContext("Example","example.com",max_results=1,timeout_seconds=p.get("request_timeout_seconds",15),api_key=key,endpoint=p["endpoint"])
    try:
        results=asyncio.run(PROVIDERS[provider]().execute(query,context)); ledger.reconcile(provider,"completed")
        output={"provider_id":provider,"state":"provider_completed","results":[{"title":r.title,"url":r.url,"snippet":r.snippet} for r in results]}
    except Exception as exc:
        ledger.reconcile(provider,"failed_chargeable"); message=str(exc).replace(key,"[REDACTED]")
        output={"provider_id":provider,"state":"provider_failed","error":{"type":type(exc).__name__,"message":message}}
    typer.echo(json.dumps(output,indent=2))

@app.command("execute-query")
def execute_query(provider: str=typer.Option(...), query: str=typer.Option(...), company: str="Diagnostic Company", official_domain: str="example.com"):
    import asyncio
    if provider not in PROVIDERS or provider in {"sitemap","internal_crawler","publication_hub","pdf_link"}:
        typer.echo(f"Provider does not support direct text queries: {provider}",err=True); raise typer.Exit(2)
    started=utc_now(); search_query=SearchQuery("diagnostic_0001",query,"diagnostic",mandatory=True,target_provider_ids=(provider,))
    try:
        results=asyncio.run(PROVIDERS[provider]().execute(search_query,CompanySearchContext(company,official_domain)))
        record={"provider_id":provider,"submitted_query":query,"started_at":started,"completed_at":utc_now(),"state":"provider_completed","result_count":len(results),"candidate_registration_count":len(results),"results":[r.__dict__ for r in results]}
    except Exception as exc:
        record={"provider_id":provider,"submitted_query":query,"started_at":started,"completed_at":utc_now(),"state":"provider_failed","error":{"type":type(exc).__name__,"message":str(exc)}}
    destination=root()/"output/search_diagnostics"/run_timestamp(); destination.mkdir(parents=True,exist_ok=True)
    (destination/"execute_query.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    typer.echo(json.dumps(record,indent=2))
    if record["state"]=="provider_failed": raise typer.Exit(2)

@app.command("discover-company-sources")
def discover_company_sources(company: str=typer.Option(...), official_domain: str=typer.Option(None)):
    import asyncio
    profile=load_company_profile(root(),company,official_domain or "")
    domain=official_domain or profile["official_domains"][0]
    destination=root()/"output/search_diagnostics"/slugify(company)/run_timestamp(); destination.mkdir(parents=True,exist_ok=True)
    result=discover_sync(root(),destination,company,domain)
    candidates=result["candidates"]
    documents=asyncio.run(Pipeline(root())._retrieve([item["canonical_url"] for item in result["retrieval_candidates"]]))
    manifest={"documents":[{"url":item["url"],"filename":item["title"],"content_hash":item["content_hash"],"page_count":len(item["pages"]),"status":item["parse_status"],"error":item["error"]} for item in documents if item["source_type"]=="pdf"]}
    (destination/"web_pdf_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    result["report"]["metrics"]["web_pdfs_downloaded"]=sum(1 for item in documents if item["source_type"]=="pdf" and not item["error"])
    result["report"]["metrics"]["web_pdfs_parsed"]=sum(1 for item in documents if item["parse_status"]=="pdf_parsed")
    (destination/"source_discovery_report.json").write_text(json.dumps(result["report"],indent=2),encoding="utf-8")
    typer.echo(json.dumps({"run_directory":str(destination),"status":result["report"]["status"],"metrics":result["report"]["metrics"]},indent=2))

@app.command("scan-company")
def scan_company(company: str, official_domain: str=typer.Option(...), country: str=typer.Option("Not specified"), seed_url: list[str]=typer.Option(None)):
    preflight=validate_index(root())
    if not preflight["ready"]:
        typer.echo(json.dumps(preflight,indent=2),err=True); raise typer.Exit(2)
    typer.echo(Pipeline(root()).run(company,official_domain,seed_url or None,country=country))

@app.command("test-patent-discovery")
def test_patent_discovery(company: str=typer.Option(...), workbook: Path=Path("data/Companies.xlsx")):
    """Fast patent-only retest using the selected registry company identity."""
    from .patent_retest import run_patent_retest
    workbook=(root()/workbook).resolve() if not workbook.is_absolute() else workbook
    selected=selected_companies(workbook,"patent_retest")
    matches=[item for item in selected if item["company_name"].strip().casefold()==company.strip().casefold()]
    if len(matches)!=1:
        typer.echo(f"Expected exactly one selected registry row for {company!r}; found {len(matches)}.",err=True)
        raise typer.Exit(2)
    out=run_patent_retest(root(),matches[0])
    summary=json.loads((out/"patent_retest_summary.json").read_text(encoding="utf-8"))
    typer.echo(json.dumps(summary,indent=2))

@app.command("scan-registry")
def scan_registry(workbook: Path=Path("data/Companies.xlsx"), run_profile: str=typer.Option("standard",help="standard or fast_iteration")):
    workbook=(root()/workbook).resolve() if not workbook.is_absolute() else workbook
    preflight=validate_index(root())
    if not preflight["ready"]:
        typer.echo(json.dumps(preflight,indent=2),err=True); raise typer.Exit(2)
    stamp=run_timestamp(); cycle_id=f"cycle_{stamp}"; batch_dir=root()/"output/batches"/stamp; batch_dir.mkdir(parents=True,exist_ok=True)
    cycle_dir=root()/"output/cycles"/cycle_id; cycle_dir.mkdir(parents=True,exist_ok=True)
    snapshot=selected_companies(workbook,cycle_id)
    cycle_snapshot={"cycle_id":cycle_id,"created_at":utc_now(),"workbook":str(workbook),"selected_rows":snapshot}
    atomic_json(cycle_dir/"cycle_snapshot.json",cycle_snapshot); atomic_json(batch_dir/"cycle_snapshot.json",cycle_snapshot)
    provider_state=ProviderCycleState(cycle_dir/"provider_cycle_state.json",load_yaml(root()/"config/search_providers.yaml")["providers"])
    manifest={"cycle_id":cycle_id,"status":"running","execution_status":"running","quality_status":"clean","degradation_flags":[],"started_at":utc_now(),"completed_at":None,"selected_company_count":len(snapshot),"companies":[]}
    atomic_json(cycle_dir/"cycle_manifest.json",manifest)
    company_results=[]; interrupted=False
    try:
        for company in snapshot:
            workbook_update={"status":"not_attempted"}
            def post_score(out, final, company=company):
                rating=final["overall_product_match"]["new_excel_rating"]
                try:
                    audit=update_rating(workbook,company["company_id"],company["company_name"],company.get("previous_overall_product_match_raw"),rating,cycle_id,final["run_id"],final["cycle_source_counts"],company.get("previous_cycle_source_counts_raw"))
                    atomic_json(out/"workbook_update_audit.json",audit); workbook_update.update({"status":"applied","audit":audit})
                except Exception as exc:
                    assessment_path=next(out.glob("*_final_assessment.json"))
                    pending={"company_id":company["company_id"],"company_name":company["company_name"],"cycle_id":cycle_id,"previous_workbook_rating":company["previous_overall_product_match"],"rating":rating,"source_counts":final["cycle_source_counts"],"assessment_run_id":final["run_id"],"assessment_completed_at":utc_now(),"final_assessment_hash":sha256_text(assessment_path.read_text(encoding="utf-8")),"write_status":"pending_workbook_unlock","failure":type(exc).__name__}
                    queue_pending(batch_dir/"pending_rating_updates.json",pending); workbook_update.update({"status":"pending","failure":type(exc).__name__})
            try:
                out=Pipeline(root(),run_profile=run_profile).run(company["company_name"],company["company_domain"],country=company.get("country"),company_aliases=company.get("other_names",[]),validated_source_assignees=company.get("validated_source_assignees",[]),cycle_id=cycle_id,previous_score=company["previous_overall_product_match"],deterministic_persisted_callback=post_score,provider_cycle_state=provider_state)
                run_manifest=json.loads(next(out.glob("*_run_manifest.json")).read_text(encoding="utf-8"))
                company_results.append({"company_id":company["company_id"],"company_name":company["company_name"],"execution_status":"completed","quality_status":run_manifest["quality_status"],"degradation_flags":run_manifest.get("degradation_flags",[]),"score":run_manifest["newly_calculated_score"],"pdf":str(out/run_manifest["report_filename"]),"llm_fallback_used":run_manifest["llm_fallback_used"],"llm_failure_code":run_manifest["llm_failure_code"],"workbook_update":workbook_update,"run_directory":str(out)})
            except KeyboardInterrupt:
                interrupted=True; raise
            except Exception as exc:
                company_results.append({"company_id":company["company_id"],"company_name":company["company_name"],"execution_status":"failed","quality_status":"degraded","error":{"type":type(exc).__name__,"message":str(exc)},"workbook_update":workbook_update})
    except KeyboardInterrupt:
        typer.echo("Cycle aborted by user.",err=True)
    finally:
        completed=sum(item["execution_status"]=="completed" for item in company_results)
        failed=sum(item["execution_status"]=="failed" for item in company_results)
        flags=set()
        for item in company_results:
            flags.update(item.get("degradation_flags",[]))
            if item.get("llm_fallback_used"): flags.update(("llm_fallback_used",item.get("llm_failure_code")))
        if any(event["event_type"]=="provider_rate_limited" for event in provider_state.data["events"]): flags.add("provider_rate_limited")
        flags.discard(None)
        if interrupted: status="aborted"
        elif failed and completed: status="incomplete"
        elif failed: status="failed"
        elif flags: status="completed_degraded"
        else: status="completed"
        summary={"cycle_id":cycle_id,"status":status,"execution_status":"completed" if not failed and not interrupted else status,"quality_status":"degraded" if flags or failed else "clean","degradation_flags":sorted(flags),"selected_company_count":len(snapshot),"completed_company_count":completed,"failed_company_count":failed,"companies":company_results,"provider_events":provider_state.data["events"],"workbook_updates_applied":sum(item.get("workbook_update",{}).get("status")=="applied" for item in company_results),"pending_workbook_updates":sum(item.get("workbook_update",{}).get("status")=="pending" for item in company_results)}
        atomic_json(cycle_dir/"cycle_summary.json",summary)
        md=[f"# BDA Cycle {cycle_id}","",f"Status: **{status}**",f"Companies completed: {completed}/{len(snapshot)}",f"Quality: **{summary['quality_status']}**","","| Company | Execution | Score | LLM fallback | Workbook |","| --- | --- | ---: | --- | --- |"]
        for item in company_results: md.append(f"| {item['company_name']} | {item['execution_status']} | {item.get('score','')} | {item.get('llm_fallback_used','')} | {item.get('workbook_update',{}).get('status','')} |")
        (cycle_dir/"cycle_summary.md").write_text("\n".join(md),encoding="utf-8")
        manifest.update({"status":status,"execution_status":summary["execution_status"],"quality_status":summary["quality_status"],"degradation_flags":summary["degradation_flags"],"completed_at":utc_now(),"companies":company_results})
        atomic_json(cycle_dir/"cycle_manifest.json",manifest); provider_state.persist()
    if interrupted: raise typer.Exit(130)
    if failed: raise typer.Exit(2)

@app.command("batch",deprecated=True)
def batch_alias(workbook: Path=Path("data/Companies.xlsx")):
    """Deprecated alias for scan-registry."""
    typer.echo("Warning: 'batch' is deprecated; use 'scan-registry'.",err=True)
    scan_registry(workbook)

@app.command("validate-registry")
def validate_registry(workbook: Path=Path("data/Companies.xlsx")):
    workbook=(root()/workbook).resolve() if not workbook.is_absolute() else workbook
    selected_companies(workbook,"validation"); typer.echo("Registry valid")

@app.command("list-registry-selection")
def list_registry_selection(workbook: Path=Path("data/Companies.xlsx")):
    workbook=(root()/workbook).resolve() if not workbook.is_absolute() else workbook
    typer.echo(json.dumps(selected_companies(workbook,"preview"),indent=2,default=str))

@app.command("compare-runs")
def compare_runs(run_a: Path, run_b: Path):
    def final(p): return json.loads(next(p.glob("*_final_assessment.json")).read_text())
    a,b=final(run_a),final(run_b)
    typer.echo(json.dumps({"rating_change":b["overall_dspace_portfolio_applicability"]-a["overall_dspace_portfolio_applicability"],"mapping_count_change":len(b["applicability_mappings"])-len(a["applicability_mappings"])},indent=2))

@app.command("ingest-dspace-portfolio")
def ingest_dspace_portfolio(source: Path=Path("data/dspace_portfolio_documents"), incremental: bool=True, rebuild: bool=False):
    source=(root()/source).resolve() if not source.is_absolute() else source
    try: typer.echo(json.dumps(ingest(root(),source,rebuild=rebuild),indent=2))
    except Exception as exc:
        typer.echo(f"Portfolio ingestion failed: {exc}",err=True); raise typer.Exit(2)

@app.command("validate-portfolio-index")
def validate_portfolio_index():
    result=validate_index(root()); typer.echo(json.dumps(result,indent=2))
    if not result["ready"]: raise typer.Exit(2)

@app.command("inspect-portfolio-index")
def inspect_portfolio_index():
    result=validate_index(root())
    if result["ready"]:
        store=ChromaPortfolioStore(root()/"data/dspace_portfolio_runtime/chroma_db")
        result["collection_metadata"]=store.collection.metadata
    typer.echo(json.dumps(result,indent=2))
    if not result["ready"]: raise typer.Exit(2)

@app.command("retrieve-portfolio")
def retrieve_portfolio(query: str=typer.Option(...), portfolio_item_id: str=typer.Option(...), top_k: int=5):
    try: typer.echo(json.dumps(retrieve(root(),query,portfolio_item_id,top_k),indent=2))
    except Exception as exc: typer.echo(str(exc),err=True); raise typer.Exit(2)

@app.command("benchmark-models")
def benchmark_models(hardware_profile: str="notebook_32gb_no_cuda"):
    typer.echo(f"Validation-only benchmark profile: {hardware_profile}. Production models remain fixed at bge-large and gemma2:9b.")

if __name__=="__main__": app()
