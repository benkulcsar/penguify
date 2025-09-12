"""
Helper functions for extracting and cleaning story excerpts.
"""

import logging
from abc import ABC, abstractmethod

import trafilatura

logger = logging.getLogger(__name__)


class ContentFetcher(ABC):
    @abstractmethod
    def fetch_content(self, url: str) -> str: ...


class TrafilaturaContentFetcher(ContentFetcher):
    def fetch_content(self, url: str) -> str:
        """
        Fetches and extracts text from an external URL using trafilatura.
        """
        try:
            logger.info(f"Fetching and extracting external excerpt from URL: {url}")
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logger.warning(f"Failed to download content from {url}")
                return ""
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            return text or ""
        except Exception as e:
            logger.warning(f"Failed to fetch or extract excerpt from {url}: {e}")
            return ""


class FakeContentFetcher(ContentFetcher):
    """
    Fake fetcher that returns deterministic text without network calls.
    """

    def __init__(self, body: str | None = None):
        self.body = body or "This is fake fetched content used for testing."

    def fetch_content(self, url: str) -> str:
        return f"{self.body} [url={url}]"
