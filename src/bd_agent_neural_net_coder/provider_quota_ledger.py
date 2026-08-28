from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .core import atomic_json, utc_now


class QuotaUnavailable(RuntimeError):
    def __init__(self, state: str):
        super().__init__(state)
        self.state = state


def _month_period(now: datetime) -> tuple[str, str]:
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    end = datetime(now.year + (now.month == 12), 1 if now.month == 12 else now.month + 1, 1, tzinfo=timezone.utc)
    return start.isoformat().replace("+00:00", "Z"), end.isoformat().replace("+00:00", "Z")


@contextmanager
def _exclusive_lock(path: Path, timeout: float = 10.0):
    lock_path = path.with_suffix(path.suffix + ".lock")
    deadline = time.monotonic() + timeout
    descriptor = None
    while descriptor is None:
        try:
            descriptor = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(descriptor, f"{os.getpid()} {utc_now()}".encode())
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"quota ledger lock timeout: {lock_path}")
            time.sleep(0.025)
    try:
        yield
    finally:
        os.close(descriptor)
        try:
            lock_path.unlink()
        except FileNotFoundError:
            pass


class ProviderQuotaLedger:
    def __init__(self, path: Path, providers: dict):
        self.path = path
        self.providers = providers
        path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if not self.path.exists():
            return {"schema_version": "1.0.0", "providers": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _fresh_record(self, provider_id: str, now: datetime) -> dict:
        cfg = self.providers[provider_id]
        period_type = cfg["period_type"]
        if period_type == "calendar_month":
            period_start, period_end = _month_period(now)
        else:
            period_start, period_end = "nonrenewing", None
        cap = int(cfg["configured_hard_cap"])
        return {"provider_id": provider_id, "period_type": period_type, "period_start": period_start, "period_end": period_end, "configured_hard_cap": cap, "requests_reserved": 0, "requests_completed": 0, "requests_failed_but_chargeable": 0, "provider_reported_remaining": None, "paid_overage_allowed": False, "updated_at": utc_now()}

    def _record(self, ledger: dict, provider_id: str, now: datetime) -> dict:
        current = ledger["providers"].get(provider_id)
        fresh = self._fresh_record(provider_id, now)
        if current is None or (fresh["period_type"] == "calendar_month" and current.get("period_start") != fresh["period_start"]):
            current = fresh; ledger["providers"][provider_id] = current
        return current

    @staticmethod
    def _remaining(record: dict) -> int:
        local = max(0, int(record["configured_hard_cap"]) - int(record["requests_reserved"]) - int(record["requests_completed"]) - int(record["requests_failed_but_chargeable"]))
        reported = record.get("provider_reported_remaining")
        return min(local, max(0, int(reported))) if reported is not None else local

    def reserve(self, provider_id: str) -> dict:
        if provider_id not in self.providers:
            raise QuotaUnavailable("account_state_unknown")
        with _exclusive_lock(self.path):
            ledger = self._read(); record = self._record(ledger, provider_id, datetime.now(timezone.utc))
            if self._remaining(record) <= 0:
                state = "starter_allowance_exhausted" if record["period_type"] == "nonrenewing" else "free_quota_exhausted"
                raise QuotaUnavailable(state)
            record["requests_reserved"] += 1; record["updated_at"] = utc_now()
            atomic_json(self.path, ledger)
            return dict(record) | {"effective_remaining": self._remaining(record)}

    def reconcile(self, provider_id: str, outcome: str, provider_remaining: int | None = None) -> dict:
        with _exclusive_lock(self.path):
            ledger = self._read(); record = self._record(ledger, provider_id, datetime.now(timezone.utc))
            record["requests_reserved"] = max(0, record["requests_reserved"] - 1)
            if outcome == "completed": record["requests_completed"] += 1
            elif outcome == "failed_chargeable": record["requests_failed_but_chargeable"] += 1
            if provider_remaining is not None: record["provider_reported_remaining"] = max(0, int(provider_remaining))
            record["updated_at"] = utc_now(); atomic_json(self.path, ledger)
            return dict(record) | {"requests_remaining": self._remaining(record), "effective_remaining": self._remaining(record)}

    def snapshot(self) -> dict:
        with _exclusive_lock(self.path):
            ledger = self._read()
            for provider_id in self.providers: self._record(ledger, provider_id, datetime.now(timezone.utc))
            for record in ledger["providers"].values():
                record["requests_remaining"] = self._remaining(record); record["effective_remaining"] = self._remaining(record)
            atomic_json(self.path, ledger); return ledger
