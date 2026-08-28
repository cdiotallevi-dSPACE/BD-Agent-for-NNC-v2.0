import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from verify_cycle_launch import verify_manifest


class GuardTests(unittest.TestCase):
    def test_manifest_states(self):
        start = datetime(2026, 8, 28, tzinfo=timezone.utc)
        base = dict(status="completed", execution_status="completed",
                    started_at=start.isoformat(), completed_at=start.isoformat(),
                    selected_company_count=1, companies=[dict(execution_status="completed")])
        cases = [({}, True), ({"status": "completed_degraded"}, True),
                 ({"status": "running"}, False), ({"execution_status": "failed"}, False),
                 ({"completed_at": None}, False), ({"companies": []}, False),
                 ({"selected_company_count": 0, "companies": []}, False),
                 ({"started_at": "2026-08-07T00:00:00Z"}, False),
                 ({"companies": [{"execution_status": "failed"}]}, False)]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "cycle_manifest.json"
            for changes, valid in cases:
                with self.subTest(changes=changes):
                    path.write_text(json.dumps({**base, **changes}), encoding="utf-8")
                    if valid:
                        verify_manifest(path, start)
                    else:
                        with self.assertRaises((ValueError, AttributeError)):
                            verify_manifest(path, start)


if __name__ == "__main__":
    unittest.main()
