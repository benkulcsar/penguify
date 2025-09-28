from abc import ABC, abstractmethod
from io import BytesIO
from time import sleep

from google import genai
from google.genai import types
from PIL import Image


class ImageGenerator(ABC):
    @abstractmethod
    def __init__(self, model_name: str): ...

    @abstractmethod
    def generate_image(self, prompt: str) -> Image.Image: ...

    @abstractmethod
    def wait(self, seconds: float) -> None: ...


class GeminiImageGenerator(ImageGenerator):
    DEFAULT_WAIT_SECONDS = 2

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.client = genai.Client()

    def generate_image(self, prompt: str) -> Image.Image:
        response = self.client.models.generate_content(
            model=self.model_name,
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

    def wait(self, seconds: float = DEFAULT_WAIT_SECONDS) -> None:
        sleep(seconds)


class FakeImageGenerator(ImageGenerator):
    """A fake image generator that always returns a blank image."""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_image(self, prompt: str) -> Image.Image:
        return Image.new(mode="RGB", size=(60, 50), color="red")

    def wait(self, seconds: float) -> None:
        pass
