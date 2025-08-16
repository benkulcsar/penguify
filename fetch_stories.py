import logging
from datetime import datetime
from os import getenv
from typing import Any

import requests

from excerpt_getter import get_story_excerpt
from models import Story, StoryList

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

HACKER_NEWS_API_BASE_URL = "https://hacker-news.firebaseio.com/v0"
HACKER_NEWS_TOP_STORIES_URL = f"{HACKER_NEWS_API_BASE_URL}/topstories.json"
HACKER_NEWS_WEB_URL = "https://news.ycombinator.com"
FETCH_TIMEOUT = int(getenv("FETCH_TIMEOUT", "12"))
TOP_STORY_COUNT = 9
HEADERS = {"User-Agent": "Penguify/1.0 (https://github.com/benkulcsar/penguify)"}
HN_STORIES_JSON_PATH = getenv("STORIES_FILE", "hackernews.json")


def fetch_json_from_url(url: str) -> Any:
    r = requests.get(url, timeout=FETCH_TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()


def build_hacker_news_url(item_id: int) -> str:
    return f"{HACKER_NEWS_WEB_URL}/item?id={item_id}"


def fetch_top_story_ids() -> list[int]:
    top_story_id_list: list[int] = fetch_json_from_url(HACKER_NEWS_TOP_STORIES_URL)
    logger.info(f"Fetched {len(top_story_id_list)} top story IDs")
    return top_story_id_list


def fetch_story_by_id(story_id: int) -> Story:
    item_url = f"{HACKER_NEWS_API_BASE_URL}/item/{story_id}.json"
    item = fetch_json_from_url(item_url)
    if not item or item.get("type") != "story":
        return Story()

    story = Story(
        id=item.get("id"),
        title=item.get("title"),
        url=item.get("url") or build_hacker_news_url(story_id),
        discussion=build_hacker_news_url(story_id),
        text=item.get("text"),
    )
    return story


def fetch_stories_by_ids(story_id_list: list[int], max_count: int) -> StoryList:
    logger.info(f"Fetching up to {max_count} stories")
    story_list = StoryList(stories=[])
    for story_id in story_id_list:
        story = fetch_story_by_id(story_id)
        story.excerpt = get_story_excerpt(story)
        if not story.is_valid():
            logger.info(f"Skipped invalid story {story_id}")
            continue
        story_list.stories.append(story)
        logger.info(f"Fetched story {story_id}")
        if len(story_list.stories) >= max_count:
            break
    logger.info(f"Fetched {len(story_list.stories)} valid stories")
    return story_list


def save_stories_to_json(story_list: StoryList, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(story_list.model_dump_json(indent=2))


def fetch_and_save_top_stories():
    datestamp = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Starting fetch of Hacker News top stories on {datestamp}")
    top_story_id_list = fetch_top_story_ids()
    top_story_list = fetch_stories_by_ids(story_id_list=top_story_id_list, max_count=TOP_STORY_COUNT)
    save_stories_to_json(top_story_list, HN_STORIES_JSON_PATH)
    logger.info("Finished fetching and saving top stories")


if __name__ == "__main__":
    fetch_and_save_top_stories()
