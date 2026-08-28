from .ddgs_provider import DDGSSearchProvider
from .github_provider import GitHubSearchProvider
from .patent_provider import PatentSearchProvider
from .semantic_scholar_provider import SemanticScholarSearchProvider
from .sitemap_provider import SitemapSearchProvider
from .internal_crawler_provider import InternalCrawlerProvider, PublicationHubProvider
from .pdf_link_provider import PDFLinkProvider
from .brave_provider import BraveSearchProvider
from .serpapi_provider import SerpAPISearchProvider
from .serper_provider import SerperSearchProvider

PROVIDERS = {
    "ddgs": DDGSSearchProvider,
    "semantic_scholar": SemanticScholarSearchProvider,
    "github": GitHubSearchProvider,
    "patent": PatentSearchProvider,
    "sitemap": SitemapSearchProvider,
    "internal_crawler": InternalCrawlerProvider,
    "publication_hub": PublicationHubProvider,
    "pdf_link": PDFLinkProvider,
    "brave": BraveSearchProvider,
    "serpapi": SerpAPISearchProvider,
    "serper": SerperSearchProvider,
}
