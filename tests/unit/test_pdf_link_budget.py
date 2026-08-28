import asyncio

import pytest

import bd_agent_neural_net_coder.pdf_link_provider as module
from bd_agent_neural_net_coder.pdf_link_provider import PDFLinkProvider


class Response:
    def __init__(self,url,text,content_type="text/html"):
        self.url=url; self.text=text; self.headers={"content-type":content_type}
    def raise_for_status(self): return None


@pytest.mark.asyncio
async def test_pdf_link_scan_is_bounded_concurrent_and_stops_when_document_budget_met(monkeypatch,capsys):
    active=maximum_active=0
    class Client:
        def __init__(self,*args,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def get(self,url):
            nonlocal active,maximum_active
            active+=1; maximum_active=max(maximum_active,active)
            await asyncio.sleep(0.01)
            active-=1
            index=url.rsplit("/",1)[-1]
            return Response(url,f'<a href="https://official.test/{index}.pdf">PDF</a>')
    monkeypatch.setattr(module.httpx,"AsyncClient",Client)
    pages=[f"https://official.test/page/{i}" for i in range(50)]
    found,metrics=await PDFLinkProvider().discover(pages,{"official.test"},max_documents=3,
        maximum_pages_scanned=10,scan_concurrency=3,progress_interval_pages=2,request_timeout_seconds=1)
    assert len(found)==3
    assert metrics["pdf_link_pages_inspected"]==3
    assert metrics["pdf_link_stop_reason"]=="pdf_discovery_budget_satisfied"
    assert maximum_active==3
    assert "3/10 pages inspected" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_pdf_link_xml_is_parsed_as_xml_and_page_cap_is_enforced(monkeypatch):
    class Client:
        def __init__(self,*args,**kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def get(self,url):
            return Response(url,'<?xml version="1.0"?><urlset><url><loc>https://official.test/manual.pdf</loc></url></urlset>',"application/xml")
    monkeypatch.setattr(module.httpx,"AsyncClient",Client)
    pages=[f"https://official.test/sitemap/{i}" for i in range(20)]
    found,metrics=await PDFLinkProvider().discover(pages,{"official.test"},max_documents=10,
        maximum_pages_scanned=4,scan_concurrency=2,progress_interval_pages=2,request_timeout_seconds=1)
    assert found[0]["url"]=="https://official.test/manual.pdf"
    assert metrics["pdf_link_pages_inspected"]==4
    assert metrics["pdf_link_xml_pages_parsed"]==4
    assert metrics["pdf_link_stop_reason"]=="page_scan_budget_exhausted"
