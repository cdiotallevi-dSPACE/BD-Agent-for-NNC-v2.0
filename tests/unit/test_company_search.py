import asyncio
from pathlib import Path

from bd_agent_neural_net_coder.ddgs_provider import DDGSSearchProvider
from bd_agent_neural_net_coder.search_models import CompanySearchContext, SearchQuery
from bd_agent_neural_net_coder.search_orchestrator import generate_queries, load_company_profile


def test_ddgs_text_is_actually_invoked(monkeypatch):
    calls = []

    class FakeDDGS:
        def __init__(self, timeout):
            self.timeout = timeout

        def text(self, query, **kwargs):
            calls.append((query, kwargs))
            return [{"title": "HVDC", "href": "https://example.test/hvdc", "body": "converter"}]

    monkeypatch.setattr("bd_agent_neural_net_coder.ddgs_provider.DDGS", FakeDDGS)
    query = SearchQuery("qry_0001", "site:example.test HVDC", "official_domain", mandatory=True)
    results = asyncio.run(DDGSSearchProvider().execute(query, CompanySearchContext("Example", "example.test")))
    assert calls and calls[0][0] == query.rendered_query
    assert results[0].url == "https://example.test/hvdc"


def test_siemens_profile_queries_and_seeds_are_additive():
    root = Path(__file__).resolve().parents[2]
    profile = load_company_profile(root, "Siemens Energy", "siemens-energy.com", ["https://siemens-energy.com/extra"])
    queries = generate_queries(profile)
    rendered = {query.rendered_query for query in queries}
    assert 'site:siemens-energy.com "neural network" embedded' in rendered
    assert "site:siemens-energy.com TinyML microcontroller" in rendered
    assert "https://siemens-energy.com/extra" in profile["seed_urls"]
    assert len(profile["seed_urls"]) == 1

def test_full_url_and_bare_domain_generate_identical_queries():
    root = Path(__file__).resolve().parents[2]
    full = load_company_profile(root,"COMPREDICT GmbH","https://compredict.ai/")
    bare = load_company_profile(root,"COMPREDICT GmbH","compredict.ai")
    assert full["official_domains"] == bare["official_domains"] == ["compredict.ai"]
    assert [q.rendered_query for q in generate_queries(full)] == [q.rendered_query for q in generate_queries(bare)]

def test_company_aliases_create_additive_discovery_queries():
    root = Path(__file__).resolve().parents[2]
    profile = load_company_profile(root,"General Motors","https://www.gm.com/",company_aliases=["General Motors Company","GMC","GM"])
    rendered={q.rendered_query for q in generate_queries(profile)}
    assert profile["official_domains"]==["gm.com"]
    assert profile["company_aliases"]==["General Motors Company","GMC","GM"]
    assert '"General Motors Company" neural network microcontroller' in rendered
    assert '"GMC" neural network microcontroller' in rendered
    assert '"GM" neural network microcontroller' in rendered
