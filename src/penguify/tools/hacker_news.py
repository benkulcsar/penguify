from abc import ABC, abstractmethod
from typing import Any

import requests


class HackerNewsClient(ABC):
    @abstractmethod
    def top_story_ids(self) -> list[int]: ...

    @abstractmethod
    def item(self, story_id: int) -> Any: ...


class DefaultHackerNewsClient(HackerNewsClient):
    HACKER_NEWS_API_BASE_URL = "https://hacker-news.firebaseio.com/v0"
    HACKER_NEWS_TOP_STORIES_URL = f"{HACKER_NEWS_API_BASE_URL}/topstories.json"
    DEFAULT_TIMEOUT = 10
    DEFAULT_HEADERS = {"User-Agent": "Penguify/1.0"}

    def __init__(self, timeout: int = DEFAULT_TIMEOUT, headers: dict[str, str] = DEFAULT_HEADERS):
        self.timeout = timeout
        self.headers = headers
        self.session = requests.Session()

    def _fetch_json(self, url: str) -> Any:
        r = self.session.get(url, timeout=self.timeout, headers=self.headers)
        return r.json()

    def top_story_ids(self) -> list[int]:
        ids: list[int] = self._fetch_json(self.HACKER_NEWS_TOP_STORIES_URL)
        return ids

    def item(self, story_id: int) -> Any:
        url = f"{self.HACKER_NEWS_API_BASE_URL}/item/{story_id}.json"
        return self._fetch_json(url)


class FakeHackerNewsClient(HackerNewsClient):
    """
    Deterministic HN client for tests.
    """

    def __init__(self, timeout: int = 0, headers: dict[str, str] = {}):
        self._ids = [101, 102, 103]
        self._items: dict[int, dict] = {
            101: {"id": 101, "type": "story", "title": "Test Story A", "url": "https://example.com/a", "score": 1},
            102: {"id": 102, "type": "story", "title": "Test Story B", "url": "https://example.com/b", "score": 2},
            103: {"id": 103, "type": "story", "title": "Test Story C", "url": "https://example.com/c", "score": 3},
        }

    def top_story_ids(self) -> list[int]:
        return list(self._ids)

    def item(self, story_id: int) -> dict:
        return self._items.get(story_id, {"id": story_id, "type": "story", "title": f"Story {story_id}"})
