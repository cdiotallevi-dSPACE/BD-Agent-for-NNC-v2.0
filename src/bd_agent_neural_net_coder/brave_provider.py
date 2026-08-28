from __future__ import annotations
import httpx
from .execution_resources import pooled_client
from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url

class BraveSearchProvider:
    provider_id = "brave"
    async def execute(self, query: SearchQuery, context: CompanySearchContext) -> list[ProviderSearchResult]:
        headers={"Accept":"application/json","X-Subscription-Token":context.api_key or ""}
        async with pooled_client(self.provider_id, timeout=context.timeout_seconds) as client:
            response=await client.get(context.endpoint,headers=headers,params={"q":query.rendered_query,"count":context.max_results,"safesearch":context.safesearch}); response.raise_for_status()
        if "json" not in response.headers.get("content-type","").lower(): raise ValueError("invalid_brave_content_type")
        data=response.json(); items=(data.get("web") or {}).get("results")
        if not isinstance(items,list): raise ValueError("invalid_brave_response")
        limits={k:response.headers.get(k) for k in ("x-ratelimit-limit","x-ratelimit-remaining","x-ratelimit-reset")}
        remaining=response.headers.get("x-ratelimit-remaining")
        self.provider_reported_remaining=int(remaining) if remaining and remaining.isdigit() else None
        return [ProviderSearchResult(self.provider_id,query.query_id,x.get("title",""),x["url"],x.get("description","") or "",i,{"rate_limit":limits}) for i,x in enumerate(items,1) if valid_http_url(x.get("url"))]
