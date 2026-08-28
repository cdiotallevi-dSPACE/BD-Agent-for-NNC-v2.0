from typer.testing import CliRunner

from bd_agent_neural_net_coder.cli import app
from bd_agent_neural_net_coder.config_manager import load_yaml


def test_patent_retest_command_is_registered():
    result = CliRunner().invoke(app, ["test-patent-discovery", "--help"])
    assert result.exit_code == 0
    assert "--company" in result.stdout


def test_fast_run_budgets_preserve_metadata_depth():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    cfg = load_yaml(root / "config/search_providers.yaml")
    assert cfg["patent_discovery_budget"]["maximum_metadata_records_per_assignee"] == 1000
    assert cfg["patent_discovery_budget"]["maximum_full_patents_retrieved_per_company"] == 80
    assert cfg["patent_discovery_budget"]["maximum_replacement_patent_attempts"] == 80
    assert sum(cfg["patent_full_text_reservations"].values()) == 80
    assert cfg["retrieval"]["maximum_pdf_documents"] == 20
    assert cfg["retrieval"]["maximum_pages_per_pdf"] == 50
    assert cfg["retrieval"]["maximum_total_parsed_pdf_pages"] == 500
    assert cfg["candidate_budget"]["maximum_retrieved_non_seed_documents_per_company"] == 60
