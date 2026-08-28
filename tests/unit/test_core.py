from datetime import datetime, timedelta, timezone
import pytest
from bd_agent_neural_net_coder.core import local_run_directory_timestamp, normalize_url, slugify, validate_scope_names
def test_slug_is_stable(): assert slugify("Siemens Energy") == "siemens-energy"
def test_url_normalization(): assert normalize_url("HTTPS://www.Example.com/a/?utm_source=x&b=2") == "https://example.com/a?b=2"
def test_prohibited_scope_name():
    with pytest.raises(ValueError): validate_scope_names({"product_id":"x"})
def test_local_run_directory_timestamp_is_windows_safe_and_readable():
    moment=datetime(2026,8,3,15,8,0,tzinfo=timezone(timedelta(hours=2)))
    value=local_run_directory_timestamp(moment)
    assert value=="3 August 2026, 15-08-00 UTC+02-00"
    assert not any(character in value for character in '<>:"/\\|?*')
