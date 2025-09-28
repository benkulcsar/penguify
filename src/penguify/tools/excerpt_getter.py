"""
Helper functions for extracting and cleaning story excerpts.
"""

import logging
from abc import ABC, abstractmethod

from bs4 import BeautifulSoup

from .content_fetcher import ContentFetcher

logger = logging.getLogger(__name__)


class ExcerptGetter(ABC):
    @abstractmethod
    def get_excerpt(self, text_html: str | None = None, url: str | None = None) -> str: ...


class DefaultExcerptGetter(ExcerptGetter):
    """
    Helper for extracting and cleaning story excerpts.
    """

    def __init__(self, content_fetcher: ContentFetcher, excerpt_chars: int = 1000):
        self.content_fetcher = content_fetcher
        self.excerpt_chars = excerpt_chars

    def get_excerpt(self, text_html: str | None = None, url: str | None = None) -> str:
        """
        Returns a cleaned excerpt from a Story object.
        """

        if text_html:
            logger.info("Cleaning HTML for story")
            raw_excerpt = self._clean_html_to_text(text_html)

        elif url:
            logger.info(f"Fetching external excerpt for story from URL: {url}")
            raw_excerpt = self.content_fetcher.fetch_content(url) if isinstance(url, str) else ""

        else:
            logger.info("No text or URL provided for excerpt")
            return ""

        excerpt = self._trim_excerpt(raw_excerpt)
        return excerpt

    def _clean_html_to_text(self, html: str | None) -> str:
        """
        Cleans HTML content and returns plain text.
        """

        logger.debug("Cleaning HTML to text")
        soup = BeautifulSoup(html or "", "html.parser")

        for tag in soup(["script", "style"]):
            tag.decompose()

        return " ".join(soup.get_text("\n").split())

    def _trim_excerpt(self, text: str | None) -> str:
        """
        Trims text to a specified character limit, preferably at a sentence boundary.
        """

        logger.debug("Trimming excerpt")
        if not text:
            return ""

        text = " ".join(text.split())

        if len(text) <= self.excerpt_chars:
            return text

        # Cut at sentence boundary if possible
        cutoff = text.rfind(". ", 0, self.excerpt_chars)
        return text[: cutoff + 1 if cutoff > 0 else self.excerpt_chars].strip()
