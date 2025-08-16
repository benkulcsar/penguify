.PHONY: lint images stories run upload

lint:
	@pre-commit run -a

stories:
	@uv run fetch_stories.py

images:
	@uv run generate_images.py

upload:
	@uv run upload_to_s3.py

run: stories pics upload
