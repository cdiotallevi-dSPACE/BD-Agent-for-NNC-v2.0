from __future__ import annotations
import hashlib, json, os, re, tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PROHIBITED = {"product_id", "product_name", "product_candidate", "matched_product", "recommended_product", "product_chunk_id", "product_fit_score"}

def utc_now() -> str: return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def run_timestamp() -> str: return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
def local_run_directory_timestamp(moment: datetime | None = None) -> str:
    local = (moment or datetime.now().astimezone()).astimezone()
    offset = local.strftime("%z")
    readable_offset = f"UTC{offset[:3]}-{offset[3:]}" if offset else "LOCAL"
    return f"{local.day} {local.strftime('%B %Y, %H-%M-%S')} {readable_offset}"
def slugify(value: str) -> str:
    value = value.encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value)).strip("-") or "company"
def sha256_text(value: str) -> str: return "sha256:" + hashlib.sha256(value.encode()).hexdigest()
def normalize_url(url: str) -> str:
    p = urlsplit(url.strip()); host = (p.hostname or "").lower()
    if host.startswith("www."): host = host[4:]
    port = f":{p.port}" if p.port and p.port not in (80, 443) else ""
    query = urlencode(sorted((k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith("utm_")))
    path = re.sub(r"/{2,}", "/", p.path or "/").rstrip("/") or "/"
    return urlunsplit(((p.scheme or "https").lower(), host + port, path, query, ""))
def normalize_company_domain(value: str) -> str:
    raw = str(value or "").strip()
    if not raw: raise ValueError("company_domain is required")
    parsed = urlsplit(raw if "://" in raw else "https://" + raw)
    host = (parsed.hostname or "").lower().rstrip(".")
    if host.startswith("www."): host = host[4:]
    if not host or "." not in host or any(ch.isspace() for ch in host):
        raise ValueError(f"invalid company_domain: {value!r}")
    return host
def validate_scope_names(obj: object) -> None:
    if isinstance(obj, dict):
        bad = PROHIBITED.intersection(obj)
        if bad: raise ValueError(f"prohibited cross-scope fields: {sorted(bad)}")
        for value in obj.values(): validate_scope_names(value)
    elif isinstance(obj, list):
        for value in obj: validate_scope_names(value)
def atomic_json(path: Path, value: object) -> None:
    validate_scope_names(value); path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f: f.write(payload); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
