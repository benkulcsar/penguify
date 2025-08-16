"""
Helper functions for extracting and cleaning story excerpts.
"""

import logging

import trafilatura
from bs4 import BeautifulSoup

from models import Story

logger = logging.getLogger(__name__)

EXCERPT_CHARS = 1000


def get_story_excerpt(story: Story) -> str:
    """
    Returns a cleaned excerpt from a Story object.
    """
    if story.text:
        logger.info(f"Cleaning HTML for story ID {getattr(story, 'id', None)}")
        raw_excerpt = _clean_html_to_text(story.text)
        excerpt = _trim_excerpt(raw_excerpt)
    else:
        logger.info(f"Fetching external excerpt for story ID {getattr(story, 'id', None)} from URL: {story.url}")
        excerpt = _get_external_excerpt(story.url) if isinstance(story.url, str) else ""
    return excerpt


def _clean_html_to_text(html: str | None) -> str:
    """
    Cleans HTML content and returns plain text.
    """
    logger.debug("Cleaning HTML to text")
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return " ".join(soup.get_text("\n").split())


def _trim_excerpt(text: str | None, limit: int = EXCERPT_CHARS) -> str:
    """
    Trims text to a specified character limit, preferably at a sentence boundary.
    """
    logger.debug("Trimming excerpt")
    if not text:
        return ""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    # Cut at sentence boundary if possible
    cutoff = text.rfind(". ", 0, limit)
    return text[: cutoff + 1 if cutoff > 0 else limit].strip()


def _get_external_excerpt(url: str) -> str:
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
