from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image

from .logger import get_logger

logger = get_logger(__name__)


class ImageSaver(ABC):
    @abstractmethod
    def save(self, image: Image.Image, path: Path, width: int, height: int) -> None: ...


class FileImageSaver(ImageSaver):
    def save(self, image: Image.Image, path: Path, width: int, height: int) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            resized_image = image.resize((width, height))
            resized_image.save(path)
            logger.info("Image saved to %s", path)
        except Exception as e:
            logger.error("Failed to save image to %s: %s", path, e)
