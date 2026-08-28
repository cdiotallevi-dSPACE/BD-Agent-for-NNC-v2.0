from __future__ import annotations

import httpx
from .execution_resources import pooled_client

from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url


class SemanticScholarSearchProvider:
    provider_id = "semantic_scholar"
    endpoint = "https://api.semanticscholar.org/graph/v1/paper/search"

    async def execute(self, query: SearchQuery, context: CompanySearchContext) -> list[ProviderSearchResult]:
        fields = "title,abstract,year,authors,url,externalIds,openAccessPdf"
        async with pooled_client(self.provider_id, timeout=context.timeout_seconds, follow_redirects=True) as client:
            response = await client.get(self.endpoint, params={"query": query.rendered_query, "limit": context.max_results, "fields": fields})
            response.raise_for_status()
        results = []
        for rank, item in enumerate(response.json().get("data", []), 1):
            pdf = (item.get("openAccessPdf") or {}).get("url")
            url = pdf or item.get("url")
            if not valid_http_url(url):
                continue
            results.append(ProviderSearchResult(self.provider_id, query.query_id, item.get("title", ""), url, item.get("abstract") or "", rank, {"year": item.get("year"), "authors": item.get("authors", []), "external_ids": item.get("externalIds", {})}))
        return results
