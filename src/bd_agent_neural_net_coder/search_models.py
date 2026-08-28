from __future__ import annotations

from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse


def valid_http_url(value: str | None) -> bool:
    try:
        parsed = urlparse(value or "")
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


@dataclass(frozen=True)
class SearchQuery:
    query_id: str
    rendered_query: str
    family: str
    priority: str = "medium"
    mandatory: bool = False
    target_provider_ids: tuple[str, ...] = ("ddgs",)
    originating_terms: tuple[str, ...] = ()

    def record(self, generated_at: str) -> dict:
        value = asdict(self)
        value["query_family"] = value.pop("family")
        value["target_provider_ids"] = list(self.target_provider_ids)
        value["originating_terms"] = list(self.originating_terms)
        value.update({"template_id": self.family, "generated_at": generated_at, "execution_state": "generated"})
        return value


@dataclass(frozen=True)
class ProviderSearchResult:
    provider_id: str
    query_id: str
    title: str
    url: str
    snippet: str
    rank: int
    provider_metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CompanySearchContext:
    company_name: str
    official_domain: str
    region: str = "us-en"
    safesearch: str = "moderate"
    backend: str = "auto"
    max_results: int = 10
    timeout_seconds: int = 15
    github_token: str | None = None
    api_key: str | None = None
    endpoint: str = ""
