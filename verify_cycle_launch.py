"""Run the normal CLI and require fresh, terminal cycle evidence (stdlib only)."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def verify_manifest(path, started):
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("execution_status") != "completed" or data.get("status") not in {"completed", "completed_degraded"}:
        raise ValueError("Cycle did not complete")
    for key in ("started_at", "completed_at"):
        stamp = datetime.fromisoformat(data[key].replace("Z", "+00:00"))
        if stamp < started.replace(microsecond=0):
            raise ValueError("Stale cycle timestamp")
    companies = data.get("companies", [])
    count = data.get("selected_company_count")
    if not isinstance(count, int) or count < 1 or len(companies) != count:
        raise ValueError("No companies selected or cycle results incomplete")
    if any(c.get("execution_status") != "completed" for c in companies):
        raise ValueError("A company did not complete")
    return data


def main():
    root, receipt, profile = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    try:
        if receipt.exists():
            raise ValueError("Verification receipt already exists")
        cycles = root / "output" / "cycles"
        before = set(cycles.glob("*/cycle_manifest.json"))
        started = datetime.now(timezone.utc)
        command = [str(root / ".venv/Scripts/bda.exe"), "scan-registry",
                   "--workbook", "data/Companies.xlsx", "--run-profile", profile]
        result = subprocess.run(command, cwd=root)
        if result.returncode != 0:
            raise ValueError(f"BDA exited with code {result.returncode}")
        fresh = set(cycles.glob("*/cycle_manifest.json")) - before
        if len(fresh) != 1:
            raise ValueError(f"Expected one newly generated cycle manifest; found {len(fresh)}")
        path = fresh.pop()
        data = verify_manifest(path, started)
        print(f"Verified cycle manifest: {path}")
        if data["status"] == "completed_degraded":
            print("WARNING: cycle completed with degraded coverage; review its manifest.")
        if any(c.get("workbook_update", {}).get("status") == "pending" for c in data["companies"]):
            print("WARNING: workbook updates are pending; review the cycle summary.")
        with receipt.open("x", encoding="utf-8") as stream:
            stream.write(str(path))
        return 0
    except Exception as exc:
        print(f"ERROR: Cycle completion NOT verified: {exc}", file=sys.stderr)
        print("Review BDA output and endpoint security detections. No success is assumed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
