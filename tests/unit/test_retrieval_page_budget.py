import asyncio
from pathlib import Path

import fitz
import yaml

import bd_agent_neural_net_coder.pipeline as pipeline_module
from bd_agent_neural_net_coder.pipeline import Pipeline


def _pdf_bytes(page_count: int) -> bytes:
    document=fitz.open()
    for index in range(page_count):
        page=document.new_page(); page.insert_text((72,72),f"page {index+1} neural network ONNX microcontroller")
    value=document.tobytes(); document.close()
    return value


class _Response:
    def __init__(self,url,content):
        self.url=url; self.content=content; self.headers={"content-type":"application/pdf"}
    def raise_for_status(self): return None


class _Client:
    def __init__(self,responses): self.responses=responses
    async def __aenter__(self): return self
    async def __aexit__(self,*args): return False
    async def get(self,url): return self.responses[url]


def test_total_and_per_pdf_page_budgets_are_enforced_with_progress(tmp_path,monkeypatch,capsys):
    config=tmp_path/"config"; config.mkdir()
    (config/"search_providers.yaml").write_text(yaml.safe_dump({"retrieval":{
        "maximum_total_urls":10,"maximum_pdf_documents":5,"maximum_pages_per_pdf":3,
        "maximum_total_parsed_pdf_pages":5,"max_download_bytes":10_000_000,
        "download_concurrency":2,"progress_interval_documents":1,
    }}),encoding="utf-8")
    urls=["https://example.test/a.pdf","https://example.test/b.pdf"]
    responses={url:_Response(url,_pdf_bytes(4)) for url in urls}
    monkeypatch.setattr(pipeline_module.httpx,"AsyncClient",lambda **kwargs:_Client(responses))
    docs=asyncio.run(Pipeline(tmp_path)._retrieve(urls))
    assert sum(len(doc["pages"]) for doc in docs)==5
    assert [len(doc["pages"]) for doc in docs]==[3,2]
    assert all(doc["parse_status"]=="pdf_parsed_truncated" for doc in docs)
    assert sum(doc["pages_skipped_by_budget"] for doc in docs)==3
    output=capsys.readouterr().out
    assert "Retrieval progress: 1/2" in output
    assert "0 pages remain in budget" in output


def test_pdf_document_budget_excludes_later_pdf(tmp_path,monkeypatch):
    config=tmp_path/"config"; config.mkdir()
    (config/"search_providers.yaml").write_text(yaml.safe_dump({"retrieval":{
        "maximum_total_urls":10,"maximum_pdf_documents":1,"maximum_pages_per_pdf":10,
        "maximum_total_parsed_pdf_pages":20,"max_download_bytes":10_000_000,
        "download_concurrency":2,"progress_interval_documents":10,
    }}),encoding="utf-8")
    urls=["https://example.test/a.pdf","https://example.test/b.pdf"]
    responses={url:_Response(url,_pdf_bytes(2)) for url in urls}
    monkeypatch.setattr(pipeline_module.httpx,"AsyncClient",lambda **kwargs:_Client(responses))
    docs=asyncio.run(Pipeline(tmp_path)._retrieve(urls))
    assert docs[0]["parse_status"]=="pdf_parsed"
    assert docs[1]["parse_status"]=="pdf_document_budget_excluded"
    assert docs[1]["pages"]==[]
