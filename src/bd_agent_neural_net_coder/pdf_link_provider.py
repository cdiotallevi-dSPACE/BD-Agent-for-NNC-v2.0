from __future__ import annotations

import asyncio
import json
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .search_models import valid_http_url


class PDFLinkProvider:
    provider_id = "pdf_link"

    async def discover(self, pages: list[str], approved_domains: set[str], max_documents: int = 50,
                       maximum_pages_scanned: int = 200, scan_concurrency: int = 8,
                       progress_interval_pages: int = 20, request_timeout_seconds: int = 12) -> tuple[list[dict], dict]:
        pages=list(dict.fromkeys(page for page in pages if not page.lower().split("?",1)[0].endswith(".pdf")))[:maximum_pages_scanned]
        found=[]; inspected=0; failed=0; xml_pages=0
        print(f"[BDA] PDF-link discovery started: up to {len(pages)} pages; {max_documents} PDF links; concurrency {scan_concurrency}.",flush=True)
        timeout=httpx.Timeout(request_timeout_seconds,connect=min(8,request_timeout_seconds))
        limits=httpx.Limits(max_connections=scan_concurrency,max_keepalive_connections=scan_concurrency)
        async with httpx.AsyncClient(timeout=timeout,limits=limits,follow_redirects=True,headers={"User-Agent":"BDA-NNC/2.0"}) as client:
            async def inspect(page: str) -> tuple[list[dict],bool,bool]:
                try:
                    response=await client.get(page); response.raise_for_status()
                    content_type=response.headers.get("content-type","").casefold()
                    prefix=response.text.lstrip()[:100].casefold()
                    is_xml=("xml" in content_type or prefix.startswith("<?xml") or
                            prefix.startswith("<urlset") or prefix.startswith("<sitemapindex") or
                            prefix.startswith("<rss") or prefix.startswith("<feed"))
                    soup=BeautifulSoup(response.text,"xml" if is_xml else "html.parser")
                except Exception:
                    return [],False,True
                values=[]
                for anchor in soup.find_all("a", href=True):
                    values.append((urljoin(str(response.url), anchor["href"]), anchor.get_text(" ", strip=True)))
                for meta in soup.find_all("meta", content=True):
                    values.append((urljoin(str(response.url), meta["content"]), meta.get("name") or meta.get("property") or ""))
                if is_xml:
                    for location in soup.find_all("loc"):
                        if location.get_text(strip=True):
                            values.append((urljoin(str(response.url),location.get_text(strip=True)),"XML location"))
                for script in soup.find_all("script", type=re.compile("ld\\+json", re.I)):
                    try:
                        values.extend((urljoin(str(response.url), value), "JSON-LD") for value in re.findall(r'https?://[^"\\s]+?\\.pdf(?:\\?[^"\\s]*)?', json.dumps(json.loads(script.string or "{}"))))
                    except Exception:
                        pass
                page_found=[]
                for url, title in values:
                    host = (urlparse(url).hostname or "").lower()
                    if valid_http_url(url) and ".pdf" in url.lower() and any(host == d or host.endswith("." + d) for d in approved_domains):
                        page_found.append({"url":url,"title":title,"snippet":"","discovery_channel":"pdf_link","provider_id":self.provider_id,"provenance":page})
                return page_found,is_xml,False

            for start in range(0,len(pages),scan_concurrency):
                if len({item["url"] for item in found})>=max_documents: break
                batch=pages[start:start+scan_concurrency]
                results=await asyncio.gather(*(inspect(page) for page in batch))
                for page_found,is_xml,did_fail in results:
                    inspected+=1; xml_pages+=int(is_xml); failed+=int(did_fail); found.extend(page_found)
                unique_count=len({item["url"] for item in found})
                if inspected==len(pages) or inspected%progress_interval_pages<scan_concurrency or unique_count>=max_documents:
                    print(f"[BDA] PDF-link progress: {inspected}/{len(pages)} pages inspected; {min(unique_count,max_documents)}/{max_documents} PDF links found.",flush=True)
        unique = {item["url"]: item for item in found}
        selected=list(unique.values())[:max_documents]
        stop_reason="pdf_discovery_budget_satisfied" if len(selected)>=max_documents else ("page_scan_budget_exhausted" if inspected>=maximum_pages_scanned else "candidate_pages_exhausted")
        print(f"[BDA] PDF-link discovery completed: {inspected} pages inspected; {len(selected)} PDF links retained; {stop_reason}.",flush=True)
        return selected,{"pdf_links_discovered":len(unique),"pdf_links_retained":len(selected),"pdf_link_pages_inspected":inspected,
            "pdf_link_pages_failed":failed,"pdf_link_xml_pages_parsed":xml_pages,"pdf_link_maximum_pages_scanned":maximum_pages_scanned,
            "pdf_link_stop_reason":stop_reason}
