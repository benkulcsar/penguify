from pydantic import BaseModel


class Story(BaseModel):
    id: int | None = None
    title: str | None = None
    url: str | None = None
    discussion: str | None = None
    excerpt: str | None = None
    text: str | None = None

    def is_valid(self) -> bool:
        return bool(
            self.title is not None and len(self.title) > 10 and self.excerpt is not None and len(self.excerpt) > 50
        )

    def get_story_context(self) -> str:
        return f"""
        News article:
        Title: {self.title}
        Excerpt: {self.excerpt}
        """


class StoryList(BaseModel):
    stories: list[Story] = []
