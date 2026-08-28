import json

from typer.testing import CliRunner

from bd_agent_neural_net_coder.cli import app
from bd_agent_neural_net_coder.credential_manager import credential_status, resolve_credential


def test_canonical_credential_precedes_alias():
    result=resolve_credential("brave",{},{"BRAVE_SEARCH_API_KEY":"canonical-secret","BRAVE_API_KEY":"alias-secret"})
    assert result["value"]=="canonical-secret"
    assert result["source_env"]=="BRAVE_SEARCH_API_KEY"
    assert result["alias_used"] is False


def test_alias_is_accepted_without_secret_in_status():
    status=credential_status("serpapi",{},{"SERPAPI_KEY":"never-print-this"})
    assert status["configured"] is True and status["alias_used"] is True
    assert status["source_env"]=="SERPAPI_KEY"
    assert "never-print-this" not in json.dumps(status)


def test_show_search_credentials_never_prints_secrets(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY","brave-private-value")
    monkeypatch.setenv("SERPAPI_API_KEY","serpapi-private-value")
    monkeypatch.setenv("SERPER_API_KEY","serper-private-value")
    output=CliRunner().invoke(app,["show-search-credentials"])
    assert output.exit_code==0
    for secret in ("brave-private-value","serpapi-private-value","serper-private-value"):
        assert secret not in output.stdout
