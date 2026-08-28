from __future__ import annotations

import httpx
from .execution_resources import pooled_client

from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url


class GitHubSearchProvider:
    provider_id = "github"

    async def execute(self, query: SearchQuery, context: CompanySearchContext) -> list[ProviderSearchResult]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if context.github_token:
            headers["Authorization"] = f"Bearer {context.github_token}"
        async with pooled_client(self.provider_id, timeout=context.timeout_seconds, headers=headers) as client:
            response = await client.get("https://api.github.com/search/repositories", params={"q": query.rendered_query, "per_page": context.max_results})
            response.raise_for_status()
        limits = {name: response.headers.get(name) for name in ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset")}
        return [
            ProviderSearchResult(self.provider_id, query.query_id, item.get("full_name", ""), item["html_url"], item.get("description") or "", rank, {"rate_limit": limits})
            for rank, item in enumerate(response.json().get("items", []), 1)
            if valid_http_url(item.get("html_url"))
        ]
