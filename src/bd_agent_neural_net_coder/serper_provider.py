from __future__ import annotations
import httpx
from .execution_resources import pooled_client
from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url

class SerperSearchProvider:
    provider_id="serper"
    async def execute(self,query:SearchQuery,context:CompanySearchContext)->list[ProviderSearchResult]:
        headers={"X-API-KEY":context.api_key or "","Content-Type":"application/json"}
        async with pooled_client(self.provider_id, timeout=context.timeout_seconds) as client:
            response=await client.post(context.endpoint,headers=headers,json={"q":query.rendered_query,"num":context.max_results}); response.raise_for_status()
        if "json" not in response.headers.get("content-type","").lower(): raise ValueError("invalid_serper_content_type")
        data=response.json(); items=data.get("organic",[])
        self.provider_reported_remaining=int(data["credits"]) if isinstance(data.get("credits"),int) else None
        if not isinstance(items,list): raise ValueError("invalid_serper_response")
        return [ProviderSearchResult(self.provider_id,query.query_id,x.get("title",""),x["link"],x.get("snippet","") or "",int(x.get("position",i)),{"credits":data.get("credits")}) for i,x in enumerate(items,1) if valid_http_url(x.get("link"))]
