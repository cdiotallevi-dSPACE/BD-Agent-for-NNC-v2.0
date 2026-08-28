import json
from bd_agent_neural_net_coder.workbook import queue_pending

def test_newer_pending_supersedes_older(tmp_path):
    path=tmp_path/"pending_rating_updates.json"
    queue_pending(path,{"company_id":"A","assessment_run_id":"run1","write_status":"pending_workbook_unlock"})
    queue_pending(path,{"company_id":"A","assessment_run_id":"run2","write_status":"pending_workbook_unlock"})
    updates=json.loads(path.read_text())["updates"]
    assert updates[0]["write_status"]=="superseded"
    assert updates[1]["write_status"]=="pending_workbook_unlock"
