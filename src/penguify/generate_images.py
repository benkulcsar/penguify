# generate_images.py

from pathlib import Path

from .common.models import ImageMetadata, Metadata, StoryList
from .common.settings import Settings, production_settings
from .tools.image_generator import GeminiImageGenerator, ImageGenerator
from .tools.image_saver import FileImageSaver, ImageSaver
from .tools.logger import get_logger
from .tools.repo import JsonFilePydanticRepository, PydanticRepository

logger = get_logger(__name__)


class ImagePipeline:
    def __init__(
        self,
        settings: Settings,
        image_generator: ImageGenerator,
        image_saver: ImageSaver,
        stories_repo: PydanticRepository,
        metadata_repo: PydanticRepository,
    ):
        self.settings = settings
        self.image_generator = image_generator
        self.image_saver = image_saver
        self.stories_repo = stories_repo
        self.metadata_repo = metadata_repo

    def run(self) -> None:
        images_dir = Path(self.settings.IMAGES_BASE_DIR) / self.settings.DATESTAMP
        logger.info("Generating images for: %s", self.settings.DATESTAMP)

        stories = self._load_stories()
        self._generate_images_for_stories(stories, images_dir)
        self._create_metadata_json(stories)

    def _load_stories(self) -> StoryList:
        logger.info("Loading Hacker News stories from %s", self.settings.HN_STORIES_JSON_PATH)
        return self.stories_repo.load(StoryList)

    def _build_prompt(self, context: str) -> str:
        return f"""
        {self.settings.IMAGE_GEN_INSTRUCTIONS}

        {context}
        """

    def _generate_images_for_stories(self, stories: StoryList, images_dir: str | Path) -> None:
        logger.info("Starting image generation for %d stories", len(stories.stories))

        for idx, story in enumerate(stories.stories):
            prompt = self._build_prompt(context=story.get_story_context())
            image_filepath = Path(images_dir) / f"{idx}.jpg"
            image = self.image_generator.generate_image(prompt)

            if image:
                self.image_saver.save(
                    image=image,
                    path=image_filepath,
                    width=self.settings.IMAGE_WIDTH,
                    height=self.settings.IMAGE_HEIGHT,
                )
            else:
                logger.error("Failed to generate image for story %d", idx)

            self.image_generator.wait(self.settings.WAIT_BETWEEN_REQUESTS_SECONDS)

        logger.info("Completed image generation for all stories")

    def _create_metadata_json(self, stories: StoryList) -> None:
        logger.info("Writing metadata via metadata_repo")
        metadata = Metadata(
            images=[ImageMetadata(title=story.title, url=story.discussion) for story in stories.stories]
        )
        self.metadata_repo.save(metadata)
        logger.info("Metadata saved successfully")


def main() -> None:
    settings = production_settings

    images_dir = f"{settings.IMAGES_BASE_DIR}/{settings.DATESTAMP}"
    meta_path = Path(images_dir) / "meta.json"

    pipeline = ImagePipeline(
        settings=settings,
        image_generator=GeminiImageGenerator(model_name=settings.MODEL_NAME),
        image_saver=FileImageSaver(),
        stories_repo=JsonFilePydanticRepository(settings.HN_STORIES_JSON_PATH),
        metadata_repo=JsonFilePydanticRepository(meta_path),
    )
    pipeline.run()


if __name__ == "__main__":
    main()
