from __future__ import annotations

from pathlib import Path

from .core import atomic_json, utc_now
from .credential_manager import resolve_credential


class ProviderCycleState:
    def __init__(self, path: Path, provider_config: dict):
        self.path = path
        self.data = {"created_at": utc_now(), "updated_at": utc_now(), "providers": {}, "events": []}
        for provider_id, cfg in provider_config.items():
            mode = cfg.get("activation_mode", "required" if cfg.get("required") else "enabled")
            credential = resolve_credential(provider_id, cfg)
            state = "active"
            if mode == "disabled":
                state = "disabled"
            elif mode == "auto" and credential.get("canonical_env") and not credential.get("value"):
                state = "skipped_missing_credentials"
                self._event(provider_id, "informational_skip", "missing_credentials")
            self.data["providers"][provider_id] = {"activation_mode": mode, "state": state, "skip_remaining_cycle": state != "active"}
        self.persist()

    def _event(self, provider_id: str, event_type: str, reason: str, details: dict | None = None):
        self.data["events"].append({"provider_id": provider_id, "event_type": event_type, "reason": reason, "at": utc_now(), "details": details or {}})

    def available(self, provider_id: str) -> bool:
        return not self.data["providers"].get(provider_id, {}).get("skip_remaining_cycle", False)

    def record_rate_limit(self, provider_id: str, details: dict | None = None):
        provider = self.data["providers"].setdefault(provider_id, {})
        if not provider.get("skip_remaining_cycle"):
            provider.update({"state": "rate_limited", "skip_remaining_cycle": True})
            self._event(provider_id, "provider_rate_limited", "cycle_cooldown", details)
            self.persist()

    def record_access_denied(self, provider_id: str, details: dict | None = None):
        self._event(provider_id, "provider_access_denied", "access_denied", details)
        self.persist()

    def persist(self):
        self.data["updated_at"] = utc_now()
        atomic_json(self.path, self.data)
