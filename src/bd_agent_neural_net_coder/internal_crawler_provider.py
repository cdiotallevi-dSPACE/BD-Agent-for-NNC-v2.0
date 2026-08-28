from __future__ import annotations

from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .search_models import valid_http_url

LINK_TERMS = ("technical", "product", "publication", "report", "pdf", "download", "white-paper", "project", "research", "patent", "engineering", "neural", "tinyml", "edge-ai", "microcontroller", "onnx", "embedded")


class InternalCrawlerProvider:
    provider_id = "internal_crawler"

    async def discover(self, starts: list[str], approved_domains: set[str], max_pages: int = 25, max_depth: int = 1, channel: str = "internal_link") -> tuple[list[dict], dict]:
        queue = deque((url, 0) for url in starts if valid_http_url(url))
        visited, results = set(), []
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": "BDA-NNC/2.0"}) as client:
            while queue and len(visited) < max_pages:
                url, depth = queue.popleft()
                if url in visited:
                    continue
                visited.add(url)
                try:
                    response = await client.get(url); response.raise_for_status()
                    soup = BeautifulSoup(response.text, "html.parser")
                except Exception:
                    continue
                for anchor in soup.find_all("a", href=True):
                    target = urljoin(str(response.url), anchor["href"])
                    label = " ".join([anchor.get_text(" ", strip=True), anchor.get("title", ""), target]).lower()
                    host = (urlparse(target).hostname or "").lower()
                    if not valid_http_url(target) or not any(host == d or host.endswith("." + d) for d in approved_domains):
                        continue
                    if any(term in label for term in LINK_TERMS):
                        results.append({"url": target, "title": anchor.get_text(" ", strip=True), "snippet": "", "discovery_channel": channel, "provider_id": "publication_hub" if channel == "publication_hub" else self.provider_id, "provenance": url})
                        if depth < max_depth and not target.lower().split("?", 1)[0].endswith(".pdf"):
                            queue.append((target, depth + 1))
        return results, {"pages_crawled": len(visited)}


class PublicationHubProvider(InternalCrawlerProvider):
    provider_id = "publication_hub"
