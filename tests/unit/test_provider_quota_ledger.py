import json
from concurrent.futures import ThreadPoolExecutor

from bd_agent_neural_net_coder.provider_quota_ledger import ProviderQuotaLedger, QuotaUnavailable
from bd_agent_neural_net_coder.search_orchestrator import _redact, generate_queries


def config(cap=2, period="calendar_month"):
    return {"metered":{"configured_hard_cap":cap,"period_type":period}}


def test_atomic_reservations_never_exceed_cap(tmp_path):
    ledger=ProviderQuotaLedger(tmp_path/"quota.json",config())
    def reserve():
        try: ledger.reserve("metered"); return True
        except QuotaUnavailable: return False
    with ThreadPoolExecutor(max_workers=5) as pool:
        results=list(pool.map(lambda _:reserve(),range(5)))
    assert sum(results)==2
    assert ledger.snapshot()["providers"]["metered"]["effective_remaining"]==0


def test_monthly_period_rolls_over(tmp_path):
    path=tmp_path/"quota.json"; ledger=ProviderQuotaLedger(path,config(1))
    ledger.reserve("metered"); data=json.loads(path.read_text()); data["providers"]["metered"]["period_start"]="2000-01-01T00:00:00Z"; path.write_text(json.dumps(data))
    assert ledger.snapshot()["providers"]["metered"]["effective_remaining"]==1


def test_nonrenewing_allowance_does_not_roll_over(tmp_path):
    ledger=ProviderQuotaLedger(tmp_path/"quota.json",config(1,"nonrenewing")); ledger.reserve("metered")
    try: ledger.reserve("metered")
    except QuotaUnavailable as exc: assert exc.state=="starter_allowance_exhausted"
    else: raise AssertionError("nonrenewing cap was exceeded")


def test_key_redaction_and_cost_free_routing():
    assert "secret" not in _redact("url?key=secret",["secret"])
    profile={"company_name":"Example","official_domains":["example.com"],"official_asset_domains":[],"related_corporate_domains":[]}
    queries=generate_queries(profile)
    assert any("brave" in q.target_provider_ids for q in queries)
    assert any("serpapi" in q.target_provider_ids for q in queries)
    assert any("serper" in q.target_provider_ids for q in queries)
    assert any("github" in q.target_provider_ids for q in queries)
