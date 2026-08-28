from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx

from .search_models import valid_http_url

RELEVANT = ("neural-network", "neural", "tinyml", "tiny-ai", "edge-ai", "microcontroller", "mcu", "embedded-ai", "onnx", "virtual-sensor", "soft-sensor", "publication", "white-paper", "report", "presentation")


class SitemapSearchProvider:
    provider_id = "sitemap"

    async def discover(self, domains: list[str], max_files: int = 10, max_urls: int = 100) -> tuple[list[dict], dict]:
        pending = []
        found = []
        attempted = 0
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": "BDA-NNC/2.0"}) as client:
            for domain in domains:
                base = f"https://{domain}"
                try:
                    robots = await client.get(urljoin(base, "/robots.txt"))
                    for line in robots.text.splitlines():
                        if line.lower().startswith("sitemap:") and valid_http_url(line.split(":", 1)[1].strip()):
                            pending.append(line.split(":", 1)[1].strip())
                except Exception:
                    pass
                pending.extend([urljoin(base, "/sitemap.xml"), urljoin(base, "/sitemap_index.xml")])
            seen = set()
            while pending and attempted < max_files and len(found) < max_urls:
                sitemap_url = pending.pop(0)
                if sitemap_url in seen:
                    continue
                seen.add(sitemap_url); attempted += 1
                try:
                    response = await client.get(sitemap_url); response.raise_for_status()
                    data = gzip.decompress(response.content) if sitemap_url.lower().endswith(".gz") else response.content
                    root = ET.fromstring(data)
                    locations = [(element.text or "").strip() for element in root.iter() if element.tag.endswith("loc")]
                    if root.tag.endswith("sitemapindex"):
                        pending.extend(url for url in locations if valid_http_url(url))
                    else:
                        for url in locations:
                            if valid_http_url(url) and any(term in url.lower() for term in RELEVANT):
                                found.append({"url": url, "title": "", "snippet": "", "discovery_channel": "sitemap", "provider_id": self.provider_id, "provenance": sitemap_url})
                except Exception:
                    continue
        return found[:max_urls], {"sitemaps_attempted": attempted, "sitemaps_parsed": attempted}
