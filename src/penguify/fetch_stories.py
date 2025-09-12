from itertools import islice
from typing import Generator, Iterable

from .common.models import Story, StoryList
from .common.settings import Settings, production_settings
from .tools.content_fetcher import TrafilaturaContentFetcher
from .tools.excerpt_getter import DefaultExcerptGetter, ExcerptGetter
from .tools.hacker_news import DefaultHackerNewsClient, HackerNewsClient
from .tools.logger import get_logger
from .tools.repo import JsonFilePydanticRepository, PydanticRepository

logger = get_logger(__name__)


class StoryFetcher:
    def __init__(
        self, settings: Settings, hn: HackerNewsClient, excerpt_getter: ExcerptGetter, repo: PydanticRepository
    ):
        self.settings = settings
        self.hn = hn
        self.excerpt_getter = excerpt_getter
        self.repo = repo

    def fetch_and_save_top_stories(self) -> None:
        logger.info("Starting fetch of HN top stories on %s", self.settings.DATESTAMP)
        top_ids = self.hn.top_story_ids()
        stories = self._take_valid_stories(self._iter_stories(top_ids), self.settings.TOP_STORY_COUNT)
        story_list = StoryList(stories=list(stories))
        self.repo.save(story_list)
        logger.info("Finished fetching and saving top stories")

    def _iter_stories(self, story_ids: list[int]) -> Generator[Story, None, None]:
        """Lazy stream: fetch item -> filter non-stories -> assemble -> enrich -> yield."""
        MAX_ITEMS_TO_FETCH = 25

        for sid in story_ids[:MAX_ITEMS_TO_FETCH]:
            item = self.hn.item(sid)

            try:
                story = Story.from_hn_item(item=item)
            except (TypeError, ValueError) as e:
                logger.warning("Failed to parse story %s: %s", sid, e)
                continue

            excerpt = self.excerpt_getter.get_excerpt(text_html=story.text, url=story.url)

            if len(excerpt) < self.settings.MIN_EXCERPT_LENGTH:
                logger.info("Skipped story %s with too short excerpt.", sid)
                continue

            story.excerpt = excerpt

            logger.info("Prepared story %s", sid)
            yield story

    @staticmethod
    def _take_valid_stories(stories: Iterable[Story], max_count: int) -> Iterable[Story]:
        taken = list(islice(stories, max_count))
        logger.info("Fetched %d valid stories", len(taken))
        return taken


def main() -> None:
    fetcher = StoryFetcher(
        settings=production_settings,
        excerpt_getter=DefaultExcerptGetter(content_fetcher=TrafilaturaContentFetcher()),
        hn=DefaultHackerNewsClient(
            timeout=production_settings.FETCH_TIMEOUT,
            headers=production_settings.HEADERS,
        ),
        repo=JsonFilePydanticRepository(production_settings.HN_STORIES_JSON_PATH),
    )
    fetcher.fetch_and_save_top_stories()


if __name__ == "__main__":
    main()
