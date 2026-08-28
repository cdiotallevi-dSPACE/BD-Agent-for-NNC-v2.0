from __future__ import annotations
import httpx
from .execution_resources import pooled_client
from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url

class SerpAPISearchProvider:
    provider_id="serpapi"
    async def execute(self,query:SearchQuery,context:CompanySearchContext)->list[ProviderSearchResult]:
        async with pooled_client(self.provider_id, timeout=context.timeout_seconds) as client:
            response=await client.get(context.endpoint,params={"q":query.rendered_query,"api_key":context.api_key,"num":context.max_results}); response.raise_for_status()
        if "json" not in response.headers.get("content-type","").lower(): raise ValueError("invalid_serpapi_content_type")
        data=response.json()
        if data.get("error"): raise RuntimeError(str(data["error"]))
        items=data.get("organic_results",[])
        if not isinstance(items,list): raise ValueError("invalid_serpapi_response")
        return [ProviderSearchResult(self.provider_id,query.query_id,x.get("title",""),x["link"],x.get("snippet","") or "",int(x.get("position",i)),{}) for i,x in enumerate(items,1) if valid_http_url(x.get("link"))]
