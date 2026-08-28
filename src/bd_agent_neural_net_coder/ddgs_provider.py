from __future__ import annotations

import asyncio
import threading
from ddgs import DDGS

from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery, valid_http_url


class DDGSSearchProvider:
    provider_id = "ddgs"

    async def execute(self, query: SearchQuery, context: CompanySearchContext) -> list[ProviderSearchResult]:
        # DDGS occasionally ignores its own network timeout and leaves the
        # asyncio default-executor thread blocked for an hour or more. A daemon
        # worker plus an asyncio deadline guarantees that one provider query
        # cannot prevent the production cycle from advancing to fallback.
        loop = asyncio.get_running_loop()
        completed: asyncio.Future = loop.create_future()

        def run() -> None:
            try:
                value = DDGS(timeout=context.timeout_seconds).text(
                    query.rendered_query,
                    region=context.region,
                    safesearch=context.safesearch,
                    max_results=context.max_results,
                    backend=context.backend,
                )
            except BaseException as exc:
                if not loop.is_closed():
                    # Exception target names are cleared automatically when an
                    # except block exits. Bind the value now so the callback
                    # cannot later raise NameError in the event-loop thread.
                    loop.call_soon_threadsafe(lambda error=exc: completed.done() or completed.set_exception(error))
            else:
                if not loop.is_closed():
                    loop.call_soon_threadsafe(lambda result=value: completed.done() or completed.set_result(result))

        threading.Thread(target=run, name=f"ddgs-{query.query_id}", daemon=True).start()
        try:
            raw = await asyncio.wait_for(completed, timeout=max(1, context.timeout_seconds + 5))
        except asyncio.TimeoutError as exc:
            raise TimeoutError(f"DDGS query exceeded {context.timeout_seconds + 5}s hard deadline") from exc
        return [
            ProviderSearchResult(
                provider_id=self.provider_id,
                query_id=query.query_id,
                title=item.get("title", ""),
                url=item["href"],
                snippet=item.get("body", ""),
                rank=index,
                provider_metadata={"backend": context.backend},
            )
            for index, item in enumerate(raw or [], 1)
            if valid_http_url(item.get("href"))
        ]
