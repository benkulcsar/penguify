import json
import logging
from datetime import datetime
from io import BytesIO
from os import getenv, makedirs
from time import sleep

from google import genai
from google.genai import types
from PIL import Image

from models import StoryList

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

MODEL_NAME = getenv("MODEL_NAME", "")
IMAGE_GEN_INSTRUCTIONS = getenv("IMAGE_GEN_INSTRUCTIONS", "")
HN_STORIES_JSON_PATH = getenv("HN_STORIES_JSON_PATH", "")
REQUEST_PAUSE_SECONDS = int(getenv("WAIT_BETWEEN_REQUESTS_SECONDS", "2"))
IMAGE_HEIGHT = getenv("IMAGE_HEIGHT", 256)
IMAGE_WIDTH = getenv("IMAGE_WIDTH", 256)
IMAGES_BASE_DIR = getenv("IMAGES_BASE_DIR", "./imgs")

missing = [
    name
    for name, value in [
        ("MODEL_NAME", MODEL_NAME),
        ("IMAGE_GEN_INSTRUCTIONS", IMAGE_GEN_INSTRUCTIONS),
        ("HN_STORIES_JSON_PATH", HN_STORIES_JSON_PATH),
    ]
    if not value
]
if missing:
    raise Exception(f"Missing required environment variable(s): {', '.join(missing)}")


def load_hackernews_stories() -> StoryList:
    logger.info(f"Loading Hacker News stories from {HN_STORIES_JSON_PATH}")
    with open(HN_STORIES_JSON_PATH, "r") as hn_file:
        hn_data = json.load(hn_file)
    return StoryList.model_validate(hn_data)


def build_image_prompt(instructions: str | None, story_context: str) -> str:
    return f"""
    {instructions}

    {story_context}
    """


def generate_image(prompt: str) -> Image.Image:
    client = genai.Client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"]),
    )

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None and part.inline_data.data is not None:
                image = Image.open(BytesIO(bytes(part.inline_data.data)))
                return image

    blank_image = Image.new(mode="RGB", size=(512, 512), color="white")
    return blank_image


def save_image(image: Image.Image, image_filepath: str) -> None:
    try:
        new_size = (int(IMAGE_WIDTH), int(IMAGE_HEIGHT))
        resized_image = image.resize(new_size)
        resized_image.save(image_filepath)
        logger.info(f"Image saved to {image_filepath}")
    except Exception as e:
        logger.error(f"Failed to save image to {image_filepath}: {e}")


def generate_images_for_stories(stories: StoryList, images_dir: str) -> None:
    logger.info(f"Starting image generation for {len(stories.stories)} stories")
    for idx, story in enumerate(stories.stories):
        prompt = build_image_prompt(instructions=IMAGE_GEN_INSTRUCTIONS, story_context=story.get_story_context())
        image_filepath = f"{images_dir}/{idx}.jpg"
        image = generate_image(prompt)
        if image:
            save_image(image, image_filepath)
            logger.info(f"Generated image for story {idx} at {image_filepath}.Waiting {REQUEST_PAUSE_SECONDS} seconds.")
            sleep(REQUEST_PAUSE_SECONDS)
        else:
            logger.error(f"Failed to generate image for story {idx}")
    logger.info("Completed image generation for all stories")


def create_metadata_json(stories: StoryList, images_dir: str) -> None:
    logger.info(f"Writing metadata to {images_dir}/meta.json")
    metadata: dict[str, list[dict]] = {"images": []}
    for story in stories.stories:
        metadata["images"].append({"title": story.title, "url": story.discussion})
    with open(f"{images_dir}/meta.json", "w") as meta_file:
        json.dump(metadata, meta_file, indent=2)
    logger.info(f"Metadata file created at {images_dir}/metadata.json")


def main():
    datestamp = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"Generating images for: {datestamp}")
    images_dir = f"./{IMAGES_BASE_DIR}/{datestamp}"
    makedirs(images_dir, exist_ok=True)
    stories = load_hackernews_stories()
    generate_images_for_stories(stories, images_dir)
    create_metadata_json(stories, images_dir)


if __name__ == "__main__":
    main()
