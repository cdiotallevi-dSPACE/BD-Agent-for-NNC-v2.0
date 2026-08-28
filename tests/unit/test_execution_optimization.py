import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from bd_agent_neural_net_coder.execution_resources import (
    ordered_downloads, bounded_page_text, pdf_hashes, http_scope, pooled_client,
)
from bd_agent_neural_net_coder.audit_journal import DiscoveryJournal, replay_journal, discovery_audit, journaled_json
import bd_agent_neural_net_coder.portfolio_index as portfolio


def test_hash_compatibility_and_bounded_text():
    for payload in (b"", b"abc", bytes(range(256)) * 2049):
        result = pdf_hashes(payload)
        assert result["content_hash"] == "sha256:" + hashlib.sha256(payload.hex().encode()).hexdigest()
        assert result["raw_content_hash"] == "sha256:" + hashlib.sha256(payload).hexdigest()
    pages = [{"text": ""}, {"text": "a" * 100}, {"text": "  "}, {"text": "last"}]
    for limit in range(1, 110):
        assert bounded_page_text(pages, limit) == " ".join(p["text"] for p in pages)[:limit]


def test_worker_order_concurrency_and_slow_head_progress():
    async def scenario():
        release = asyncio.Event()
        active = 0
        maximum = 0
        finished = []
        async def download(index):
            nonlocal active, maximum
            active += 1
            maximum = max(active, maximum)
            if index == 0:
                await release.wait()
            else:
                await asyncio.sleep(0)
            finished.append(index)
            if index == 2:
                release.set()  # would deadlock with old fixed batch [0, 1]
            active -= 1
            return index
        results = [value async for value in ordered_downloads(list(range(12)), download, 2)]
        assert results == list(range(12))
        assert finished.index(2) < finished.index(0)
        assert maximum <= 2
    asyncio.run(asyncio.wait_for(scenario(), 2))


def test_worker_cancellation_cleans_up():
    async def scenario():
        active = set()
        async def download(index):
            active.add(index)
            try:
                await asyncio.sleep(0 if index == 0 else 20)
                return index
            finally:
                active.remove(index)
        iterator = ordered_downloads(list(range(12)), download, 2)
        assert await anext(iterator) == 0
        await iterator.aclose()
        assert not active
    asyncio.run(scenario())


def test_slow_pdf_keeps_ranked_page_budget(tmp_path, monkeypatch):
    import fitz
    import yaml
    import bd_agent_neural_net_coder.pipeline as pipeline
    (tmp_path / "config").mkdir()
    (tmp_path / "config/search_providers.yaml").write_text(yaml.safe_dump({"retrieval": {
        "maximum_total_urls": 3, "maximum_pdf_documents": 3, "maximum_pages_per_pdf": 2,
        "maximum_total_parsed_pdf_pages": 3, "max_download_bytes": 1000000,
        "download_concurrency": 2, "progress_interval_documents": 1}}))
    with fitz.open() as doc:
        for _ in range(2): doc.new_page().insert_text((72, 72), "Neural network temperature estimator")
        payload = doc.tobytes()
    urls = [f"https://example.org/{i}.pdf" for i in range(3)]
    class Response:
        content = payload
        headers = {"content-type": "application/pdf"}
        def __init__(self, url): self.url = url
        def raise_for_status(self): pass
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def get(self, url):
            await asyncio.sleep(0.02 if url == urls[0] else 0)
            return Response(url)
    monkeypatch.setattr(pipeline.httpx, "AsyncClient", lambda **kwargs: Client())
    docs = asyncio.run(pipeline.Pipeline(tmp_path)._retrieve(urls))
    assert [d["requested_url"] for d in docs] == urls
    assert [len(d["pages"]) for d in docs] == [2, 1, 0]
    assert [d["parse_status"] for d in docs] == ["pdf_parsed", "pdf_parsed_truncated", "pdf_page_budget_excluded"]
    assert all(d["content_hash"] == "sha256:" + hashlib.sha256(payload.hex().encode()).hexdigest() for d in docs)


def test_journal_replays_mutations_before_snapshot_and_torn_tail(tmp_path):
    journal = DiscoveryJournal(tmp_path)
    rows = [{"state": "started"}]
    journal.update("search_execution.json", {"executions": rows})
    rows[0]["state"] = "completed"
    rows.append({"state": "failed"})
    journal.update("search_execution.json", {"executions": rows})
    journal.stream.close()  # emulate hard exit before final checkpoint
    assert not (tmp_path / "search_execution.json").exists()
    with journal.path.open("ab") as stream:
        stream.write(b'{"torn":')
    assert replay_journal(journal.path)["search_execution.json"] == {"executions": rows}


def test_journal_writes_final_snapshots_on_exception(tmp_path):
    @discovery_audit
    async def interrupted(root, out):
        journaled_json(out / "provider_results.json", {"results": [{"title": "saved"}]})
        raise RuntimeError("test")
    with pytest.raises(RuntimeError):
        asyncio.run(interrupted(tmp_path, tmp_path))
    assert json.loads((tmp_path / "provider_results.json").read_text())["results"] == [{"title": "saved"}]
    assert json.loads((tmp_path / "discovery_events.jsonl").read_text().splitlines()[-1])["kind"] == "discovery_interrupted"


def test_http_reuse_is_scoped_and_provider_isolated(monkeypatch):
    import bd_agent_neural_net_coder.execution_resources as resources
    instances = []
    class Client:
        def __init__(self, **kwargs):
            self.closed = False
            instances.append(self)
        async def __aenter__(self): return self
        async def __aexit__(self, *args): self.closed = True
    monkeypatch.setattr(resources.httpx, "AsyncClient", Client)
    @http_scope
    async def run():
        async with pooled_client("uspto", timeout=15) as first:
            pass
        assert not first.closed
        async with pooled_client("uspto", timeout=15) as second:
            assert second is first
        async with pooled_client("google", timeout=15) as third:
            assert third is not first
    asyncio.run(run())
    asyncio.run(run())  # separate loops MUST create fresh clients
    assert len(instances) == 4 and all(c.closed for c in instances)


def _fake_index(root):
    runtime = root / "data/dspace_portfolio_runtime"
    (runtime / "chroma_db").mkdir(parents=True)
    (runtime / "collection_manifest.json").write_text(json.dumps({"embedding_model": portfolio.EMBEDDING_MODEL,
        "embedding_dimension": portfolio.DIMENSION, "chunk_count": 4, "document_count": 1}))
    (runtime / "document_manifest.json").write_text(json.dumps({"documents": [{"status": "active", "indexed_chunk_ids": ["c1"]}]}))


def test_batched_portfolio_preserves_selected_chunks_and_filters(tmp_path, monkeypatch):
    _fake_index(tmp_path)
    created, embedded = [], []
    class Store:
        def __init__(self, path): created.append(path)
        def validate_collection_metadata(self): return True
        def count(self): return 4
        def get(self, ids): return {"ids": ids}
        def query(self, vector, item, top_k):
            assert item == "neural_net_coder" and top_k == 8
            meta = dict(source_filename="nnc.pdf", page_start=1, page_end=1, section="deploy", chunk_type="technical")
            return {"ids": [["a", "b", "c", "d"]], "documents": [["text"] * 4],
                    "metadatas": [[meta, meta, meta, {**meta, "chunk_type": "overview"}]],
                    "distances": [[0.1, 0.2, 0.3, 0.65]]}
    def embed(self, texts):
        embedded.append(list(texts))
        return [[float(len(text))] for text in texts]
    monkeypatch.setattr(portfolio, "ChromaPortfolioStore", Store)
    monkeypatch.setattr(portfolio.OllamaEmbeddingClient, "embed", embed)
    queries = ["alpha", "beta", "gamma", "alpha"]
    baseline = [portfolio.retrieve(tmp_path, q, "neural_net_coder") for q in queries]
    created.clear(); embedded.clear()
    @portfolio.portfolio_scope
    def optimized():
        portfolio.validate_index(tmp_path)
        portfolio.prefetch_portfolio(tmp_path, queries, batch_size=2)
        return [portfolio.retrieve(tmp_path, q, "neural_net_coder") for q in queries]
    assert optimized() == baseline
    assert len(created) == 1
    assert embedded == [["alpha", "beta"], ["gamma"]]


def test_slow_pdf_keeps_ranked_page_budget(tmp_path, monkeypatch):
    import httpx
    import pymupdf as fitz
    import bd_agent_neural_net_coder.pipeline as pipeline
    cfg = dict(download_concurrency=2, progress_interval_documents=1, max_download_bytes=1000000,
               maximum_pdf_documents=10, maximum_pages_per_pdf=2, maximum_total_parsed_pdf_pages=3)
    monkeypatch.setattr(pipeline, "load_search_config", lambda *args: {"retrieval": cfg})
    with fitz.open() as pdf:
        for _ in range(2):
            pdf.new_page().insert_text((30, 30), "engineering evidence")
        payload = pdf.tobytes()
    async def get(self, url, **kwargs):
        if url.endswith("0.pdf"):
            await asyncio.sleep(0.02)
        return httpx.Response(200, content=payload, headers={"content-type": "application/pdf"}, request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx.AsyncClient, "get", get)
    urls = [f"https://example.org/{i}.pdf" for i in range(3)]
    docs = asyncio.run(pipeline.Pipeline(tmp_path)._retrieve(urls))
    assert [d["requested_url"] for d in docs] == urls
    assert [len(d["pages"]) for d in docs] == [2, 1, 0]
    assert [d["parse_status"] for d in docs] == ["pdf_parsed", "pdf_parsed_truncated", "pdf_page_budget_excluded"]
    assert all(d["content_hash"] == pdf_hashes(payload)["content_hash"] for d in docs)


def test_portfolio_detects_ingestion_and_changed_manifest(tmp_path, monkeypatch):
    _fake_index(tmp_path)
    @portfolio.portfolio_scope
    def changed():
        portfolio._check_generation(tmp_path)
        path = tmp_path / "data/dspace_portfolio_runtime/document_manifest.json"
        path.write_text(path.read_text() + " ")
        portfolio._check_generation(tmp_path)
    with pytest.raises(RuntimeError, match="changed_during_run"):
        changed()
    @portfolio.portfolio_scope
    def ingesting():
        path = tmp_path / "data/dspace_portfolio_runtime/locks"
        path.mkdir()
        (path / "ingestion.lock").touch()
        portfolio._check_generation(tmp_path)
    with pytest.raises(RuntimeError, match="ingestion active"):
        ingesting()


@pytest.mark.parametrize("fallback,scholar_limit", [(False, 1), (True, 1), (False, 0)])
def test_provider_parallelism_keeps_merge_order_fallback_and_budget(tmp_path, monkeypatch, fallback, scholar_limit):
    import bd_agent_neural_net_coder.search_orchestrator as search
    from bd_agent_neural_net_coder.config_manager import load_search_config
    from bd_agent_neural_net_coder.search_models import SearchQuery, ProviderSearchResult
    config = load_search_config(Path(__file__).resolve().parents[2])
    config["providers"]["semantic_scholar"]["max_queries"] = scholar_limit
    config["providers"]["semantic_scholar"]["enabled"] = True
    monkeypatch.setattr(search, "load_search_config", lambda *args: config)
    monkeypatch.setattr(search, "resolve_credential", lambda *args: {"value": None, "canonical_env": None})
    query = SearchQuery("qry_0001", "Example neural", "professional_publication_atomic" if fallback else "academic",
                        mandatory=True, target_provider_ids=("ddgs", "semantic_scholar"))
    monkeypatch.setattr(search, "generate_queries", lambda *args: [query])
    events = []
    class DDGS:
        async def execute(self, query, context):
            events.append("ddgs_start")
            await asyncio.sleep(0.02)
            events.append("ddgs_end")
            return [ProviderSearchResult("ddgs", query.query_id, "first", "https://example.org/first", "", 1)]
    class Scholar:
        provider_id = "semantic_scholar"
        async def execute(self, query, context):
            events.append("scholar_start")
            await asyncio.sleep(0)
            events.append("scholar_end")
            return [ProviderSearchResult(self.provider_id, query.query_id, "second", "https://example.org/second", "", 1)]
    monkeypatch.setitem(search.PROVIDERS, "ddgs", DDGS)
    monkeypatch.setitem(search.PROVIDERS, "semantic_scholar", Scholar)
    async def native(*args): return {"selected": [], "records": [], "manifests": [], "status": "completed"}
    async def sitemap(*args): return [], {"sitemaps_attempted": 1}
    async def crawl(*args): return [], {"pages_crawled": 0}
    async def pdf(*args): return [], {"pdf_links_discovered": 0}
    monkeypatch.setattr(search.PatentNativeDiscovery, "run", native)
    monkeypatch.setattr(search.SitemapSearchProvider, "discover", sitemap)
    monkeypatch.setattr(search.InternalCrawlerProvider, "discover", crawl)
    monkeypatch.setattr(search.PublicationHubProvider, "discover", crawl)
    monkeypatch.setattr(search.PDFLinkProvider, "discover", pdf)
    out = tmp_path / "out"
    out.mkdir()
    result = asyncio.run(search.discover(tmp_path, out, "Example", "example.org"))
    if not fallback and scholar_limit:
        assert events.index("scholar_end") < events.index("ddgs_end")
        assert [r["provider_id"] for r in result["provider_results"]] == ["ddgs", "semantic_scholar"]
    else:
        assert "scholar_start" not in events
    assert result["provider_results"][0]["title"] == "first"
    replayed = replay_journal(out / "discovery_events.jsonl")
    for name in ("search_execution.json", "search_queries.json", "provider_results.json"):
        assert replayed[name] == json.loads((out / name).read_text(encoding="utf-8"))
