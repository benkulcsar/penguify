from typing import Any

from pydantic import BaseModel, HttpUrl, TypeAdapter, ValidationError


class Story(BaseModel):
    id: int
    title: str
    url: str
    discussion: str
    excerpt: str | None = None
    text: str | None = None

    @classmethod
    def from_hn_item(cls, item: dict[str, Any]) -> "Story":
        HACKER_NEWS_WEB_URL = "https://news.ycombinator.com"

        if not isinstance(item, dict):
            raise TypeError("item must be a dict")

        if "id" not in item or "title" not in item:
            raise ValueError("Missing required fields: 'id' and 'title'")

        if not isinstance(item["id"], int):
            raise ValueError("'id' must be an int")

        if not isinstance(item["title"], str):
            raise ValueError("'title' must be a str")

        if len(item["title"]) <= 5:
            raise ValueError("'title' must be longer than 5 characters")

        discussion = f"{HACKER_NEWS_WEB_URL}/item?id={item['id']}"
        url = item.get("url") or discussion
        TypeAdapter(HttpUrl).validate_python(url)

        try:
            return cls(
                id=item["id"],
                title=item["title"],
                url=url,
                discussion=discussion,
                excerpt=item.get("excerpt"),
                text=item.get("text"),
            )
        except ValidationError as e:
            raise ValueError(f"Invalid Story data: {e}") from e

    def get_story_context(self) -> str:
        return f"""
        News article:
        Title: {self.title}
        Excerpt: {self.excerpt}
        """


class StoryList(BaseModel):
    stories: list[Story] = []


class ImageMetadata(BaseModel):
    title: str
    url: str


class Metadata(BaseModel):
    images: list[ImageMetadata]
