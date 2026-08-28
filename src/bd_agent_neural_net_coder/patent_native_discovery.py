"""Patent-native assignee enumeration and deterministic local ranking (design v1.8)."""
from __future__ import annotations
from .execution_resources import pooled_client, http_scope

import asyncio
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .core import atomic_json, normalize_url, slugify, utc_now
from .shared_use_case_taxonomy import (
    all_matching_terms, families_for_industry, family_terms,
    load_shared_use_case_taxonomy, match_use_case_families,
    neural_cpc_match, patent_cpc_family_matches,
)

PATENT_ID = re.compile(r"(?i)\b(?:US|EP|WO|DE|JP|CN|GB|CA|AU)\s*\d{5,}[A-Z]\d?\b")
PATENT_PATH_ID = re.compile(r"(?i)/(?:patent/)?((?:US|EP|WO|DE|JP|CN|GB|CA|AU)\d{5,}[A-Z]\d?|\d{7,})")
PATENT_HOSTS = {"patents.google.com", "patents.justia.com", "data.uspto.gov", "api.uspto.gov"}
_SHARED_TAXONOMY = load_shared_use_case_taxonomy()
# Required query coverage is intentionally bounded to core terms. Extended
# synonyms remain available through match_use_case_families() for local
# metadata/full-text matching and do not create a DDGS request explosion.
REQUIRED_TERMS = {family_id: tuple(definition.get("core_discovery_terms", []))
                  for family_id, definition in _SHARED_TAXONOMY["use_case_families"].items()}
HIGH_VALUE_CODES = {code for definition in _SHARED_TAXONOMY["use_case_families"].values()
                    for code in definition.get("patent_cpc_codes", [])}

DEFAULT_RESERVATIONS = {
    "battery_virtual_measurement_and_predictive_control": 20,
    "vehicle_dynamics_learned_estimation": 20,
    "indirect_physical_state_and_virtual_sensing": 15,
    "condition_monitoring_and_prognostics": 15,
    "perception_classification_and_detection": 10,
    "occupant_driver_cabin_sensing": 5,
    "cross_family_highest_ranked": 15,
}


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).casefold()).strip()


def _contains(text: str, term: str) -> bool:
    return _norm(term) in _norm(text)


def normalized_patent_identifier(value: str) -> str | None:
    compact = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    return compact if re.fullmatch(r"(?:US|EP|WO|DE|JP|CN|GB|CA|AU)\d{5,}[A-Z]\d?", compact) else None


def normalize_uspto_application(item: dict, enumeration_assignee: str) -> dict | None:
    """Map the supplied USPTO Patent File Wrapper JSON schema to BDA's patent record."""
    metadata = item.get("applicationMetaData") or {}
    sequences = metadata.get("publicationSequenceNumberBag") or []
    categories = metadata.get("publicationCategoryBag") or []
    candidates = [metadata.get("earliestPublicationNumber"), metadata.get("pctPublicationNumber")]
    candidates.extend(f"US{seq}{categories[index]}" for index, seq in enumerate(sequences)
                      if index < len(categories) and seq and categories[index])
    pregrant_publication = next((normalized_patent_identifier(value) for value in candidates if value), None)
    patent_number = re.sub(r"\D", "", str(metadata.get("patentNumber") or ""))
    # A grant following a pre-grant publication receives B2; a grant without a
    # prior publication receives B1. Preserve both identifiers for auditing.
    grant_publication = normalized_patent_identifier(f"US{patent_number}{'B2' if pregrant_publication else 'B1'}") if patent_number else None
    publication = grant_publication or pregrant_publication
    if not publication:
        return None
    assignments = item.get("assignmentBag") or []
    assignees = [str(row.get("assigneeNameText") or "").strip()
                 for assignment in assignments for row in (assignment.get("assigneeBag") or [])
                 if str(row.get("assigneeNameText") or "").strip()]
    applicants = [str(row.get("applicantNameText") or "").strip()
                  for row in (metadata.get("applicantBag") or []) if str(row.get("applicantNameText") or "").strip()]
    inventors = [str(row.get("inventorNameText") or "").strip()
                 for row in (metadata.get("inventorBag") or []) if str(row.get("inventorNameText") or "").strip()]
    application = re.sub(r"\D", "", str(item.get("applicationNumberText") or ""))
    grant_document = item.get("grantDocumentMetaData") or {}
    pgpub_document = item.get("pgpubDocumentMetaData") or {}
    document_url = grant_document.get("fileLocationURI") or pgpub_document.get("fileLocationURI")
    portal_url = f"https://data.uspto.gov/patent-file-wrapper/search/details/{application}/application-data"
    return {"source_provider": "uspto_patent_file_wrapper", "source_record_id": application or publication,
        "patent_url": document_url or portal_url, "patent_portal_url": portal_url,
        "report_canonical_url": portal_url,
        "publication_number": publication, "application_number": application or None,
        "publication_number_aliases": [value for value in (grant_publication, pregrant_publication) if value],
        "title": str(metadata.get("inventionTitle") or "").strip(),
        "abstract": str(metadata.get("abstractText") or item.get("abstractText") or "").strip(),
        "metadata_keywords": metadata.get("priorArtKeywordBag") or metadata.get("keywordBag") or [],
        "current_assignees": list(dict.fromkeys(assignees or applicants)), "original_assignees": applicants,
        "inventors": inventors, "filing_date": metadata.get("filingDate"),
        "publication_date": metadata.get("earliestPublicationDate"), "grant_date": metadata.get("grantDate"),
        "legal_status": metadata.get("applicationStatusDescriptionText"),
        "classifications": {"cpc": metadata.get("cpcClassificationBag") or [], "ipc": []},
        "patent_family_id": None, "cited_patent_ids": [], "citing_patent_ids": [], "related_application_ids": [],
        "metadata_complete": bool(metadata.get("inventionTitle") and (assignees or applicants)),
        "patent_native_enumeration_or_search": True, "enumeration_assignee": enumeration_assignee}


def patent_result_quality(record: dict, validated_assignees: list[str], taxonomy_terms: tuple[str, ...] | list[str]) -> dict:
    url = str(record.get("patent_url") or record.get("url") or "")
    host = (urlparse(url).hostname or "").lower()
    identifier = normalized_patent_identifier(record.get("publication_number", ""))
    if not identifier:
        match = PATENT_PATH_ID.search(url)
        identifier = normalized_patent_identifier(match.group(1)) if match else None
    codes = [*record.get("classifications", {}).get("cpc", []), *record.get("classifications", {}).get("ipc", [])]
    title_abstract = f"{record.get('title','')} {record.get('abstract','')} {record.get('snippet','')} {' '.join(record.get('metadata_keywords', []))}"
    assignees = [*record.get("current_assignees", []), *record.get("original_assignees", [])]
    assignee_match = any(_norm(expected) in _norm(actual) or _norm(actual) in _norm(expected)
                         for expected in validated_assignees for actual in assignees if actual)
    taxonomy_match = (any(_contains(title_abstract, term) for term in taxonomy_terms)
                      or bool(record.get("native_taxonomy_search_term"))
                      or bool(patent_cpc_family_matches(codes))
                      or neural_cpc_match(codes))
    native = bool(record.get("patent_native_enumeration_or_search"))
    recognized = host in PATENT_HOSTS and bool(identifier)
    has_text = bool(str(record.get("title") or record.get("abstract") or record.get("snippet") or "").strip())
    usable = recognized and has_text and native and (assignee_match or bool(record.get("candidate_assignee_for_validation")))
    if usable:
        reason = "usable_patent_record"
    elif host not in PATENT_HOSTS:
        reason = "non_patent_results_from_patent_provider"
    elif not identifier:
        reason = "missing_patent_identifier"
    elif not native:
        reason = "not_patent_native_enumeration_or_search"
    elif not assignee_match:
        reason = "target_assignee_absent"
    else:
        reason = "missing_title_or_abstract"
    return {"status": "usable" if usable else "unusable", "reason_code": reason,
            "recognized_patent_document": recognized, "target_assignee_signal": assignee_match,
            "taxonomy_signal": taxonomy_match, "normalized_identifier": identifier,
            "fallback_required": not usable}


def supplemental_patent_results_usable(results: list, validated_assignees: list[str], taxonomy_terms: list[str]) -> bool:
    for item in results:
        record = {"url": getattr(item, "url", ""), "title": getattr(item, "title", ""),
                  "snippet": getattr(item, "snippet", ""), "current_assignees": [],
                  "patent_native_enumeration_or_search": True}
        text = f"{record['title']} {record['snippet']}"
        record["current_assignees"] = [name for name in validated_assignees if _contains(text, name)]
        quality = patent_result_quality(record, validated_assignees, taxonomy_terms)
        if quality["status"] == "usable" and quality["taxonomy_signal"]:
            return True
    return False


def rank_patent(record: dict, validated_assignees: list[str]) -> dict:
    title = str(record.get("title", "")); abstract = str(record.get("abstract", ""))
    combined = f"{title} {abstract} {' '.join(record.get('metadata_keywords', []))}"
    matched: dict[str, list[str]] = {}
    score = 0; reasons = []
    assignees = [*record.get("current_assignees", []), *record.get("original_assignees", [])]
    if any(_norm(expected) in _norm(actual) or _norm(actual) in _norm(expected)
           for expected in validated_assignees for actual in assignees if actual):
        score += 35; reasons.append("validated_assignee_exact_match")
    matched.update(match_use_case_families(combined))
    for family, hits in list(matched.items()):
        if hits:
            score += 30 + (20 if any(_contains(title, term) for term in hits) else 15)
            reasons.extend(["exact_required_use_case_term", "title_match" if any(_contains(title, term) for term in hits) else "abstract_match"])
    native_family = record.get("native_taxonomy_search_family")
    native_term = record.get("native_taxonomy_search_term")
    if native_family and native_term and native_family not in matched:
        matched[native_family] = [native_term]
        score += 24; reasons.append("patent_native_taxonomy_query_match")
    fold = combined.casefold()
    if "neural network" in fold: score += 24; reasons.append("explicit_neural_network_term")
    if "machine learning" in fold: score += 18; reasons.append("explicit_machine_learning_term")
    if "regression model" in fold or "classification model" in fold: score += 15; reasons.append("regression_or_classification_model")
    if re.search(r"(?i)(onboard|on-board|controller|control unit|ECU|BMS|OBCM|RESS)", combined):
        score += 15; reasons.append("onboard_or_controller_context")
    codes = list(record.get("classifications", {}).get("cpc", [])) + list(record.get("classifications", {}).get("ipc", []))
    cpc_matches = patent_cpc_family_matches(codes)
    for family, hits in cpc_matches.items():
        matched.setdefault(family, []).extend(x for x in hits if x not in matched.get(family, []))
    if cpc_matches: score += 15; reasons.append("high_value_classification")
    if neural_cpc_match(codes): score += 24; reasons.append("neural_model_classification")
    if str(record.get("legal_status", "")).casefold() in {"active", "pending"}: score += 5; reasons.append("active_or_pending_status")
    return {**record, "local_rank_score": score, "local_rank_reasons": sorted(set(reasons)),
            "matched_use_case_families": sorted(matched), "matched_required_terms": matched}


def select_with_reservations(ranked: list[dict], reservations: dict[str, int], maximum: int) -> list[dict]:
    # Within every qualified use-case family, official USPTO records take
    # precedence over Google/foreign family renderings. Deterministic relevance
    # score remains the ordering criterion inside each provider tier.
    ordered = sorted(ranked, key=lambda r: (
        0 if r.get("source_provider") == "uspto_patent_file_wrapper" else 1,
        -int(r.get("local_rank_score", 0)),
        r.get("publication_number") or r.get("patent_url", "")))
    selected: list[dict] = []; seen_ids: set[str] = set(); seen_families: set[str] = set()
    def add(record: dict) -> bool:
        identifier = record.get("publication_number") or record.get("patent_url")
        family_id = record.get("patent_family_id")
        if identifier in seen_ids or len(selected) >= maximum: return False
        if family_id and family_id in seen_families: return False
        selected.append(record); seen_ids.add(identifier)
        if family_id: seen_families.add(family_id)
        return True
    for family, capacity in reservations.items():
        if family == "cross_family_highest_ranked": continue
        count = 0
        for record in ordered:
            if family in record.get("matched_use_case_families", []) and add(record):
                record["retrieval_reservation_family"] = family; count += 1
                if count >= capacity: break
    for record in ordered:
        if add(record): record["retrieval_reservation_family"] = "cross_family_highest_ranked"
        if len(selected) >= maximum: break
    return selected


def _atomic_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            for record in records: handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


class PatentNativeDiscovery:
    def __init__(self, config: dict,
                 fetch_json: Callable[[str], Awaitable[dict]] | None = None,
                 fetch_text: Callable[[str], Awaitable[str]] | None = None):
        self.config = config
        self._fetch_json = fetch_json
        self._fetch_text = fetch_text
        provider = config.get("patent_provider_request_policy", {})
        self._request_interval = float(provider.get("minimum_request_interval_seconds", 0.8))
        self._retry_delays = tuple(float(x) for x in provider.get("retry_delays_seconds", [2, 5, 12]))
        self._cache_dir = Path(provider.get("cache_directory", "data/cache/patent_native_http"))
        self._request_lock = asyncio.Lock()
        self._last_request_at = 0.0
        self._open_circuits: dict[str, httpx.HTTPStatusError] = {}
        # Direct provider-method tests and utilities retain the historical
        # complete core coverage. run() narrows this by industry/profile.
        self._active_native_terms = dict(REQUIRED_TERMS)

    def _cache_file(self, kind: str, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{kind}_{digest}.json"

    def _read_cache(self, kind: str, url: str):
        path = self._cache_file(kind, url)
        try:
            wrapper = json.loads(path.read_text(encoding="utf-8"))
            return wrapper["payload"]
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _write_cache(self, kind: str, url: str, payload) -> None:
        atomic_json(self._cache_file(kind, url), {"url": url, "cached_at": utc_now(), "payload": payload})

    async def _network_get(self, url: str, extra_headers: dict | None = None) -> httpx.Response:
        retryable = {429, 500, 502, 503, 504}
        host = (urlparse(url).hostname or "unknown").lower()
        if host in self._open_circuits:
            raise self._open_circuits[host]
        attempts = len(self._retry_delays) + 1
        last_error = None
        for attempt in range(attempts):
            if attempt:
                await asyncio.sleep(self._retry_delays[attempt - 1])
            async with self._request_lock:
                loop = asyncio.get_running_loop()
                remaining = self._request_interval - (loop.time() - self._last_request_at)
                if remaining > 0:
                    await asyncio.sleep(remaining)
                headers = {"User-Agent": "BDA-NNC/2.0 (+patent research)", **(extra_headers or {})}
                async with pooled_client(host, timeout=15, follow_redirects=True, headers=headers) as client:
                    response = await client.get(url)
                self._last_request_at = loop.time()
            if response.status_code not in retryable:
                response.raise_for_status()
                self._open_circuits.pop(host, None)
                return response
            last_error = httpx.HTTPStatusError(f"retryable provider response {response.status_code}", request=response.request, response=response)
        self._open_circuits[host] = last_error
        raise last_error

    async def _json(self, url: str, headers: dict | None = None) -> dict:
        if self._fetch_json: return await self._fetch_json(url)
        cached = self._read_cache("json", url)
        if cached is not None: return cached
        payload = (await self._network_get(url, headers)).json()
        self._write_cache("json", url, payload)
        return payload

    async def _text(self, url: str) -> str:
        if self._fetch_text: return await self._fetch_text(url)
        cached = self._read_cache("text", url)
        if cached is not None: return str(cached)
        payload = (await self._network_get(url)).text
        self._write_cache("text", url, payload)
        return payload

    async def enumerate_google(self, assignee: str, budget: dict) -> tuple[list[dict], dict]:
        records = []; pages = []; maximum = int(budget["maximum_metadata_records_per_native_source"])
        page_limit = int(budget["maximum_pages_per_assignee_source"])
        for page in range(page_limit):
            # Prefer newest assignee records so recent pending/granted inventions
            # cannot be crowded out by decades of older portfolio material.
            native_query = f'assignee=("{assignee}")&num=100&page={page}&sort=new'
            url = "https://patents.google.com/xhr/query?url=" + quote(native_query, safe="") + "&exp="
            try:
                payload = await self._json(url)
                results = payload.get("results", {})
                rows = [row for cluster in results.get("cluster", []) for row in cluster.get("result", [])]
                pages.append({"page": page + 1, "status": "completed", "raw_records": len(rows)})
                for row in rows:
                    patent = row.get("patent", {}); publication = normalized_patent_identifier(patent.get("publication_number", ""))
                    if not publication: continue
                    family_status = patent.get("family_metadata", {}).get("aggregated", {}).get("country_status", [])
                    active = any(x.get("best_patent_stage", {}).get("state") == "ACTIVE" for x in family_status)
                    records.append({"source_provider": "google_patents", "source_record_id": row.get("id"),
                        "patent_url": normalize_url(urljoin("https://patents.google.com/", row.get("id", ""))),
                        "publication_number": publication, "application_number": None,
                        "title": BeautifulSoup(patent.get("title", ""), "html.parser").get_text(" ", strip=True),
                        "abstract": BeautifulSoup(patent.get("snippet", ""), "html.parser").get_text(" ", strip=True),
                        "current_assignees": [patent.get("assignee", "")] if patent.get("assignee") else [],
                        "original_assignees": [], "inventors": [patent.get("inventor", "")] if patent.get("inventor") else [],
                        "filing_date": patent.get("filing_date"), "publication_date": patent.get("publication_date"),
                        "grant_date": patent.get("grant_date"), "legal_status": "active" if active else None,
                        "classifications": {"cpc": [], "ipc": []}, "patent_family_id": None,
                        "cited_patent_ids": [], "citing_patent_ids": [], "related_application_ids": [],
                        "metadata_complete": bool(patent.get("title") and patent.get("assignee")),
                        "patent_native_enumeration_or_search": True, "enumeration_assignee": assignee})
                    if len(records) >= maximum: break
                if len(records) >= maximum or not rows or page + 1 >= int(results.get("total_num_pages", page + 1)): break
            except Exception as exc:
                pages.append({"page": page + 1, "status": "failed", "error": type(exc).__name__}); break
        return records[:maximum], {"provider": "google_patents", "pages": pages, "records": min(len(records), maximum),
            "pagination_terminated_by": "configured_budget" if len(records) >= maximum else ("provider_error" if pages and pages[-1]["status"] == "failed" else "end_of_results")}

    async def enumerate_google_terms(self, assignee: str, budget: dict) -> tuple[list[dict], dict]:
        """Native assignee+taxonomy search; terms are generic and patent IDs are never inputs."""
        records = []; executions = []; term_buckets = []
        core_families = tuple(self._active_native_terms)
        maximum = int(budget["maximum_metadata_records_per_native_source"])
        for family in core_families:
            for term in self._active_native_terms[family]:
                native_query = f'assignee=("{assignee}")&q=("{term}")&num=100&page=0&sort=new'
                url = "https://patents.google.com/xhr/query?url=" + quote(native_query, safe="") + "&exp="
                try:
                    payload = await self._json(url); results = payload.get("results", {})
                    rows = [row for cluster in results.get("cluster", []) for row in cluster.get("result", [])]
                    matched = 0; term_records = []
                    for row in rows:
                        patent = row.get("patent", {}); publication = normalized_patent_identifier(patent.get("publication_number", ""))
                        text = BeautifulSoup(f"{patent.get('title','')} {patent.get('snippet','')}", "html.parser").get_text(" ", strip=True)
                        if not publication: continue
                        term_records.append({"source_provider": "google_patents", "source_record_id": row.get("id"),
                            "patent_url": normalize_url(urljoin("https://patents.google.com/", row.get("id", ""))),
                            "publication_number": publication, "application_number": None,
                            "title": BeautifulSoup(patent.get("title", ""), "html.parser").get_text(" ", strip=True),
                            "abstract": BeautifulSoup(patent.get("snippet", ""), "html.parser").get_text(" ", strip=True),
                            "current_assignees": [patent.get("assignee", "")] if patent.get("assignee") else [],
                            "original_assignees": [], "inventors": [patent.get("inventor", "")] if patent.get("inventor") else [],
                            "filing_date": patent.get("filing_date"), "publication_date": patent.get("publication_date"),
                            "grant_date": patent.get("grant_date"), "legal_status": None, "classifications": {"cpc": [], "ipc": []},
                            "patent_family_id": None, "cited_patent_ids": [], "citing_patent_ids": [], "related_application_ids": [],
                            "metadata_complete": bool(patent.get("title") and patent.get("assignee")),
                            "patent_native_enumeration_or_search": True, "enumeration_assignee": assignee,
                            "native_taxonomy_search_family": family, "native_taxonomy_search_term": term})
                        matched += int(_contains(text, term))
                    term_records.sort(key=lambda item: (
                        not _contains(item.get("title", ""), term),
                        not _contains(f"{item.get('title','')} {item.get('abstract','')}", term),
                        item.get("publication_number") or ""))
                    term_buckets.append(term_records)
                    executions.append({"family": family, "term": term, "status": "completed", "raw_records": len(rows), "exact_matches": matched})
                except Exception as exc:
                    executions.append({"family": family, "term": term, "status": "failed", "error": type(exc).__name__,
                        "http_status": getattr(getattr(exc, "response", None), "status_code", None), "exact_matches": 0})
                total_terms=sum(len(terms) for terms in self._active_native_terms.values())
                print(f"[BDA] Patent-native term coverage: {len(executions)}/{total_terms} terms; {term}; {executions[-1]['status']}.", flush=True)
        # Preserve bounded representation from every mandatory term. Appending
        # whole result pages and truncating would let the first five terms fill
        # a 500-record cap and silently discard all later (notably battery) terms.
        seen = set()
        while len(records) < maximum and any(term_buckets):
            progressed = False
            for bucket in term_buckets:
                while bucket:
                    candidate = bucket.pop(0)
                    key = candidate.get("publication_number") or candidate.get("patent_url")
                    if key in seen:
                        continue
                    seen.add(key); records.append(candidate); progressed = True
                    break
                if len(records) >= maximum:
                    break
            if not progressed:
                break
        return records, {"provider": "google_patents_taxonomy_search", "term_executions": executions,
            "records": len(records), "pagination_terminated_by": "one_page_per_required_term_fair_cap"}

    async def enumerate_justia(self, assignee: str, budget: dict) -> tuple[list[dict], dict]:
        records = []; pages = []; maximum = int(budget["maximum_metadata_records_per_native_source"])
        page_limit = int(budget["maximum_pages_per_assignee_source"]); base = f"https://patents.justia.com/assignee/{slugify(assignee)}"
        for page in range(1, page_limit + 1):
            try:
                html = await self._text(base + f"?page={page}"); soup = BeautifulSoup(html, "html.parser")
                links = []
                for anchor in soup.select('a[href*="/patent/"]'):
                    href = urljoin("https://patents.justia.com", anchor.get("href", "")); match = PATENT_PATH_ID.search(href)
                    if not match or href in {x[0] for x in links}: continue
                    links.append((href, anchor.get_text(" ", strip=True), match.group(1)))
                pages.append({"page": page, "status": "completed", "raw_records": len(links)})
                for href, title, raw_id in links:
                    publication = normalized_patent_identifier(raw_id) or ("US" + raw_id if raw_id.isdigit() else None)
                    records.append({"source_provider": "justia_patents", "source_record_id": raw_id,
                        "patent_url": normalize_url(href), "publication_number": publication, "application_number": None,
                        "title": title, "abstract": "", "current_assignees": [assignee], "original_assignees": [],
                        "inventors": [], "filing_date": None, "publication_date": None, "grant_date": None,
                        "legal_status": None, "classifications": {"cpc": [], "ipc": []}, "patent_family_id": None,
                        "cited_patent_ids": [], "citing_patent_ids": [], "related_application_ids": [],
                        "metadata_complete": bool(title), "patent_native_enumeration_or_search": True,
                        "enumeration_assignee": assignee})
                    if len(records) >= maximum: break
                if len(records) >= maximum or not links: break
            except Exception as exc:
                pages.append({"page": page, "status": "failed", "error": type(exc).__name__}); break
        return records[:maximum], {"provider": "justia_patents", "pages": pages, "records": min(len(records), maximum),
            "pagination_terminated_by": "configured_budget" if len(records) >= maximum else ("provider_error" if pages and pages[-1]["status"] == "failed" else "end_of_results")}

    async def enumerate_uspto(self, assignee: str, budget: dict) -> tuple[list[dict], dict]:
        """Enumerate official Patent File Wrapper records using the supplied JSON schema."""
        api_key = os.getenv("USPTO_API_KEY", "").strip()
        if not api_key:
            return [], {"provider": "uspto_patent_file_wrapper", "status": "unavailable_missing_credentials",
                "records": 0, "pages": [], "credential_environment_variable": "USPTO_API_KEY"}
        provider = self.config.get("uspto_patent_file_wrapper", {})
        endpoint = provider.get("endpoint", "https://api.uspto.gov/api/v1/patent/applications/search")
        query_template = provider.get("assignee_query_template", 'assigneeNameText:("{assignee}")')
        page_size = min(100, int(provider.get("page_size", 100)))
        maximum = int(budget["maximum_metadata_records_per_native_source"])
        page_limit = min(int(budget["maximum_pages_per_assignee_source"]), (maximum + page_size - 1) // page_size)
        records = []; pages = []
        for page in range(page_limit):
            query = query_template.format(assignee=assignee.replace('"', ""))
            params = f"q={quote(query, safe='')}&offset={page * page_size}&limit={page_size}"
            url = endpoint + ("&" if "?" in endpoint else "?") + params
            try:
                payload = await self._json(url, {"X-API-KEY": api_key, "Accept": "application/json"})
                rows = payload.get("patentFileWrapperDataBag") or []
                normalized = [record for item in rows if (record := normalize_uspto_application(item, assignee))]
                records.extend(normalized)
                pages.append({"page": page + 1, "status": "completed", "raw_records": len(rows),
                    "normalized_records": len(normalized)})
                if not rows or len(records) >= maximum or len(records) >= int(payload.get("count") or 0): break
            except Exception as exc:
                pages.append({"page": page + 1, "status": "failed", "error": type(exc).__name__,
                    "http_status": getattr(getattr(exc, "response", None), "status_code", None)})
                break
        status = "completed" if any(page["status"] == "completed" for page in pages) else "failed"
        return records[:maximum], {"provider": "uspto_patent_file_wrapper", "status": status,
            "schema": "patent-data-schema.json", "pages": pages, "records": min(len(records), maximum),
            "pagination_terminated_by": "configured_budget" if len(records) >= maximum else
                ("provider_error" if pages and pages[-1]["status"] == "failed" else "end_of_results")}

    async def enumerate_uspto_terms(self, assignee: str, budget: dict) -> tuple[list[dict], dict]:
        api_key = os.getenv("USPTO_API_KEY", "").strip()
        if not api_key:
            return [], {"provider": "uspto_patent_file_wrapper_taxonomy_search", "status": "unavailable_missing_credentials",
                "records": 0, "term_executions": [], "credential_environment_variable": "USPTO_API_KEY"}
        provider = self.config.get("uspto_patent_file_wrapper", {})
        endpoint = provider.get("endpoint", "https://api.uspto.gov/api/v1/patent/applications/search")
        assignee_query = provider.get("assignee_query_template", 'applicationMetaData.applicantBag.applicantNameText:"{assignee}"').format(assignee=assignee.replace('"', ""))
        maximum = int(budget["maximum_metadata_records_per_native_source"])
        buckets = []; executions = []
        for family, family_query_terms in self._active_native_terms.items():
            for term in family_query_terms:
                tokens = [token for token in re.findall(r"[A-Za-z0-9]+", term) if len(token) > 1]
                if family in {"battery_virtual_measurement_and_predictive_control", "battery_power_capability_and_adaptation"} and "battery" not in {x.casefold() for x in tokens}:
                    tokens.insert(0, "battery")
                boolean_term = " AND ".join(tokens)
                query = f"{assignee_query} AND applicationMetaData.inventionTitle:({boolean_term})"
                url = endpoint + "?" + f"q={quote(query, safe='')}&offset=0&limit=100"
                try:
                    payload = await self._json(url, {"X-API-KEY": api_key, "Accept": "application/json"})
                    rows = payload.get("patentFileWrapperDataBag") or []
                    normalized = [record for item in rows if (record := normalize_uspto_application(item, assignee))]
                    for record in normalized:
                        record["native_taxonomy_search_family"] = family
                        record["native_taxonomy_search_term"] = term
                    buckets.append(normalized)
                    executions.append({"family": family, "term": term, "status": "completed",
                        "raw_records": len(rows), "normalized_records": len(normalized)})
                except Exception as exc:
                    executions.append({"family": family, "term": term, "status": "failed", "error": type(exc).__name__,
                        "http_status": getattr(getattr(exc, "response", None), "status_code", None)})
                total_terms=sum(len(terms) for terms in self._active_native_terms.values())
                print(f"[BDA] USPTO taxonomy coverage: {len(executions)}/{total_terms} terms; {term}; {executions[-1]['status']}.", flush=True)
        records = []; seen = set()
        while len(records) < maximum and any(buckets):
            progressed = False
            for bucket in buckets:
                while bucket:
                    record = bucket.pop(0); key = record.get("publication_number") or record.get("application_number")
                    if key in seen: continue
                    seen.add(key); records.append(record); progressed = True; break
                if len(records) >= maximum: break
            if not progressed: break
        return records, {"provider": "uspto_patent_file_wrapper_taxonomy_search", "status": "completed",
            "records": len(records), "term_executions": executions,
            "pagination_terminated_by": "one_page_per_required_term_fair_cap"}

    @http_scope
    async def run(self, profile: dict, out: Path) -> dict:
        raw_assignees = profile.get("validated_patent_assignees", [])
        assignees = [x.get("assignee_name") for x in raw_assignees if isinstance(x, dict) and x.get("validation_status") == "established"]
        budget = self.config["patent_discovery_budget"]
        taxonomy = load_shared_use_case_taxonomy()
        active = families_for_industry(profile.get("industry", "unknown"))
        term_limit = (int(taxonomy["channel_policy"]["fast_iteration_core_terms_per_family"])
                      if self.config.get("active_run_profile") == "fast_iteration"
                      else int(taxonomy["channel_policy"]["standard_core_terms_per_family"]))
        self._active_native_terms = {family_id: tuple(definition.get("core_discovery_terms", [])[:term_limit])
                                     for family_id, definition in active.items()}
        # Generic neural queries are assigned to a cross-family bucket and are
        # independently executed for every validated source assignee.
        generic_limit = 3 if self.config.get("active_run_profile") == "fast_iteration" else 4
        self._active_native_terms["generic_neural_application"] = tuple(
            taxonomy["generic_neural_terms"]["core_discovery_terms"][:generic_limit])
        atomic_json(out / "patent_assignee_registry.json", {"validated_assignees": raw_assignees,
            "status": "ready" if assignees else "degraded_no_validated_assignee"})
        manifests = []; all_records = []
        for assignee in assignees:
            # Official USPTO metadata is authoritative and is enumerated first.
            # Google Patents remains a metadata/full-text fallback.
            uspto, um = await self.enumerate_uspto(assignee, budget); all_records.extend(uspto); manifests.append(um)
            uspto_terms, utm = await self.enumerate_uspto_terms(assignee, budget); all_records.extend(uspto_terms); manifests.append(utm)
            google, gm = await self.enumerate_google(assignee, budget); all_records.extend(google); manifests.append(gm)
            term_records, tm = await self.enumerate_google_terms(assignee, budget); all_records.extend(term_records); manifests.append(tm)
            justia, jm = await self.enumerate_justia(assignee, budget); all_records.extend(justia); manifests.append(jm)
        by_id = {}; alias_to_id = {}
        for record in all_records:
            identifiers=[x for x in [record.get("publication_number"),*record.get("publication_number_aliases",[])] if x]
            key=next((alias_to_id[x] for x in identifiers if x in alias_to_id),record.get("publication_number") or record["patent_url"])
            previous=by_id.get(key)
            if previous:
                richer=record if len(record.get("abstract", ""))>len(previous.get("abstract", "")) else previous
                other=previous if richer is record else record
                merged={**other,**richer}
                official=next((x for x in (record,previous) if x.get("source_provider")=="uspto_patent_file_wrapper"),None)
                if official:
                    merged.update({name:official.get(name) for name in ("patent_url","patent_portal_url","source_provider","source_record_id","application_number") if official.get(name)})
                    merged["current_assignees"]=official.get("current_assignees") or merged.get("current_assignees",[])
                merged["publication_number_aliases"]=list(dict.fromkeys([*previous.get("publication_number_aliases",[]),*record.get("publication_number_aliases",[]),*identifiers]))
                if other.get("native_taxonomy_search_term") and not merged.get("native_taxonomy_search_term"):
                    merged["native_taxonomy_search_term"]=other["native_taxonomy_search_term"]
                    merged["native_taxonomy_search_family"]=other["native_taxonomy_search_family"]
                by_id[key]=merged
            else:
                by_id[key]=record
            for identifier in identifiers: alias_to_id[identifier]=key
        # Preserve taxonomy-matched native-search records before filling the
        # bounded corpus with ordinary assignee enumeration records.
        all_terms = tuple(term for terms in REQUIRED_TERMS.values() for term in terms)
        quality_rows = []
        all_deduplicated = list(by_id.values())
        for record in all_deduplicated:
            quality = patent_result_quality(record, assignees, all_terms); record["provider_quality"] = quality
            quality_rows.append({"source_provider": record["source_provider"], "source_record_id": record["source_record_id"], **quality})
        usable_all = [record for record in all_deduplicated if record["provider_quality"]["status"] == "usable"]
        ranked_all = [rank_patent(record, assignees) for record in usable_all]
        maximum_corpus = int(budget["maximum_metadata_records_per_assignee"])
        records = []
        for family in self._active_native_terms:
            family_ranked = sorted((r for r in ranked_all if family in r.get("matched_use_case_families", [])), key=lambda r: (-r["local_rank_score"], r.get("publication_number") or ""))
            records.extend(r for r in family_ranked[:maximum_corpus // 2] if r.get("publication_number") not in {x.get("publication_number") for x in records})
        for record in sorted(ranked_all, key=lambda r: (-r["local_rank_score"], r.get("publication_number") or "")):
            if len(records) >= maximum_corpus: break
            if record.get("publication_number") not in {x.get("publication_number") for x in records}: records.append(record)
        usable = records
        term_execution = {}
        for manifest in manifests:
            for row in manifest.get("term_executions", []):
                key = (row["family"], row["term"]); previous = term_execution.get(key)
                if previous is None or (previous.get("status") != "completed" and row.get("status") == "completed"):
                    term_execution[key] = row
        coverage = []
        coverage_terms = {**REQUIRED_TERMS, "generic_neural_application": self._active_native_terms["generic_neural_application"]}
        for family, terms in coverage_terms.items():
            for term in terms:
                matches = [r.get("publication_number") for r in usable if _contains(f"{r.get('title','')} {r.get('abstract','')}", term)
                           or (r.get("native_taxonomy_search_family") == family and r.get("native_taxonomy_search_term") == term)]
                native_execution = term_execution.get((family, term))
                execution_status = native_execution.get("status") if native_execution else ("not_required_for_native_query" if family not in self._active_native_terms else "not_executed")
                coverage.append({"use_case_family": family, "required_term": term, "execution_status": execution_status,
                    "failure": ({"error": native_execution.get("error"), "http_status": native_execution.get("http_status")} if native_execution and native_execution.get("status") == "failed" else None),
                    "match_count": len(matches), "matching_publication_numbers": matches})
        ranked = records
        reservations = self.config.get("patent_full_text_reservations", DEFAULT_RESERVATIONS)
        selected = select_with_reservations(ranked, reservations, int(budget["maximum_full_patents_retrieved_per_company"]))
        atomic_json(out / "patent_enumeration_manifest.json", {"status": "completed" if assignees else "degraded_no_validated_assignee",
            "native_assignee_enumeration_attempted": bool(assignees), "sources": manifests,
            "raw_records": len(all_records), "normalized_records": len(records), "usable_records": len(usable)})
        atomic_json(out / "patent_provider_quality.json", {"records": quality_rows, "metrics": {
            "raw_result_count": len(records), "usable_patent_record_count": len(usable),
            "target_assignee_record_count": sum(x["target_assignee_signal"] for x in quality_rows),
            "taxonomy_signal_record_count": sum(x["taxonomy_signal"] for x in quality_rows),
            "rejected_non_patent_count": sum(x["reason_code"] == "non_patent_results_from_patent_provider" for x in quality_rows),
            "rejected_missing_identifier_count": sum(x["reason_code"] == "missing_patent_identifier" for x in quality_rows),
            "capability_validation_status": "pass" if usable else "fail"}})
        _atomic_jsonl(out / "patent_metadata_corpus.jsonl", records)
        required_coverage = [x for x in coverage if x["use_case_family"] in self._active_native_terms and x["required_term"] in self._active_native_terms[x["use_case_family"]]]
        atomic_json(out / "patent_term_coverage.json", {"complete": all(x["execution_status"] == "completed" for x in required_coverage), "terms": coverage})
        atomic_json(out / "patent_metadata_rankings.json", {"rankings": sorted(ranked, key=lambda r: -r["local_rank_score"]),
            "family_reservations": reservations, "selected_publication_numbers": [r.get("publication_number") for r in selected]})
        expansion_channels = ["same_patent_family", "related_applications", "continuations_or_divisionals", "cited_patents",
                              "citing_patents", "same_assignee_same_CPC", "same_assignee_neighboring_CPC"]
        atomic_json(out / "patent_family_expansion.json", {"status": "completed_no_expansion_metadata" if selected else "not_applicable",
            "channels_attempted": [{"channel": channel, "status": "metadata_unavailable_from_enumeration_record", "records": 0} for channel in expansion_channels],
            "records": [], "configured_budgets": {"family": budget["maximum_family_expansion_records"], "citation": budget["maximum_citation_expansion_records"]}})
        atomic_json(out / "patent_full_text_manifest.json", {"status": "selected_pending_retrieval", "reservations": reservations,
            "selected": [{"publication_number": r.get("publication_number"), "patent_url": r["patent_url"],
                          "use_case_families": r.get("matched_use_case_families", []),
                          "reservation_family": r.get("retrieval_reservation_family"), "retrieval_status": "pending"} for r in selected]})
        return {"records": records, "ranked": ranked, "selected": selected, "manifests": manifests,
                "status": "completed" if assignees and usable else ("degraded_no_validated_assignee" if not assignees else "degraded")}
