from pathlib import Path
from bd_agent_neural_net_coder.config_manager import validate_all
def test_all_yaml_is_schema_and_cross_reference_valid():
    root=Path(__file__).resolve().parents[2]
    assert validate_all(root/"config") == []

