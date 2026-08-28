from __future__ import annotations

import os
from collections.abc import Mapping

DEFAULT_CREDENTIALS = {
    "brave": ("BRAVE_SEARCH_API_KEY", ("BRAVE_API_KEY",)),
    "serpapi": ("SERPAPI_API_KEY", ("SERPAPI_KEY",)),
    "serper": ("SERPER_API_KEY", ()),
}


def resolve_credential(provider_id: str, provider_cfg: dict | None = None,
                       environ: Mapping[str, str] | None = None) -> dict:
    """Resolve a provider secret while keeping it separate from safe diagnostics."""
    provider_cfg = provider_cfg or {}
    environ = os.environ if environ is None else environ
    default_env, default_aliases = DEFAULT_CREDENTIALS.get(provider_id, (None, ()))
    canonical = provider_cfg.get("credential_env", default_env)
    aliases = tuple(provider_cfg.get("credential_aliases", default_aliases))
    names = tuple(name for name in (canonical, *aliases) if name)
    selected = next((name for name in names if environ.get(name)), None)
    return {
        "provider_id": provider_id,
        "configured": selected is not None,
        "canonical_env": canonical,
        "accepted_aliases": list(aliases),
        "source_env": selected,
        "alias_used": bool(selected and selected != canonical),
        "value": environ.get(selected) if selected else None,
    }


def credential_status(provider_id: str, provider_cfg: dict | None = None,
                      environ: Mapping[str, str] | None = None) -> dict:
    resolved = resolve_credential(provider_id, provider_cfg, environ)
    return {key: value for key, value in resolved.items() if key != "value"}
