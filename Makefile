.PHONY: lint images stories run upload

lint:
	@pre-commit run -a

stories:
	@uv run -m src.penguify.fetch_stories

images:
	@uv run -m src.penguify.generate_images

upload:
	@uv run -m penguify.upload_to_s3

run: stories pics upload
