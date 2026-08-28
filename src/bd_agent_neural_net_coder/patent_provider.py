from __future__ import annotations

from .ddgs_provider import DDGSSearchProvider
from .search_models import CompanySearchContext, ProviderSearchResult, SearchQuery
from .patent_native_discovery import normalized_patent_identifier, PATENT_PATH_ID, PATENT_HOSTS
from urllib.parse import urlparse


class PatentSearchProvider:
    provider_id = "patent"

    async def execute(self, query: SearchQuery, context: CompanySearchContext) -> list[ProviderSearchResult]:
        self.quality_records = []
        routed = SearchQuery(query.query_id, query.rendered_query, "patent", query.priority, query.mandatory)
        results = await DDGSSearchProvider().execute(routed, context)
        usable = []
        for result in results:
            host = (urlparse(result.url).hostname or "").lower()
            match = PATENT_PATH_ID.search(result.url)
            identifier = normalized_patent_identifier(match.group(1)) if match else None
            if host not in PATENT_HOSTS or not identifier:
                self.quality_records.append({"title": result.title, "url": result.url, "status": "unusable",
                    "reason_code": "non_patent_results_from_patent_provider" if host not in PATENT_HOSTS else "missing_patent_identifier",
                    "fallback_required": True})
                continue
            self.quality_records.append({"title": result.title, "url": result.url, "status": "usable",
                "reason_code": "usable_supplemental_patent_record", "normalized_publication_number": identifier,
                "fallback_required": False})
            usable.append(ProviderSearchResult(self.provider_id, result.query_id, result.title, result.url,
                result.snippet, result.rank, {**result.provider_metadata, "discovery": "supplemental_site_restricted_ddgs",
                "provider_result_quality": "usable", "normalized_publication_number": identifier,
                "patent_native_enumeration_or_search": False}))
        return usable
