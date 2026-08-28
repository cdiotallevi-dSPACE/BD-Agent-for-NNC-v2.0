import asyncio
import time

import pytest

import bd_agent_neural_net_coder.ddgs_provider as module
from bd_agent_neural_net_coder.ddgs_provider import DDGSSearchProvider
from bd_agent_neural_net_coder.search_models import CompanySearchContext, SearchQuery


def test_ddgs_hard_timeout_does_not_block_cycle(monkeypatch):
    class HungDDGS:
        def __init__(self, timeout): pass
        def text(self, *args, **kwargs):
            time.sleep(10)
            return []
    monkeypatch.setattr(module, "DDGS", HungDDGS)
    query = SearchQuery(query_id="q1", family="test", rendered_query="test")
    context = CompanySearchContext(company_name="X", official_domain="x.test", region="us-en",
                                   safesearch="moderate", max_results=5, backend="auto", timeout_seconds=-4)
    with pytest.raises(TimeoutError):
        asyncio.run(DDGSSearchProvider().execute(query, context))


def test_ddgs_worker_exception_is_forwarded_without_late_bound_name_error(monkeypatch):
    class FailedDDGS:
        def __init__(self, timeout): pass
        def text(self, *args, **kwargs):
            raise RuntimeError("provider failed")
    monkeypatch.setattr(module, "DDGS", FailedDDGS)
    query = SearchQuery(query_id="q2", family="test", rendered_query="test")
    context = CompanySearchContext(company_name="X", official_domain="x.test", region="us-en",
                                   safesearch="moderate", max_results=5, backend="auto", timeout_seconds=1)
    with pytest.raises(RuntimeError, match="provider failed"):
        asyncio.run(DDGSSearchProvider().execute(query, context))
