# Maize Disease Detection API

FastAPI service for maize leaf disease detection from uploaded images and videos.

## Requirements

- Python 3.13+
- `model.pt` in the project root

## Run

Start the API with:

```bash
uv run uvicorn main:app --reload
```

The interactive API reference is available at `http://127.0.0.1:8000/docs` and uses Scalar.

## Endpoints

- `GET /health`
- `POST /image`
- `POST /video`
- `GET /docs` for the Scalar API reference

### `POST /image`

Send a single file field named `file` using `multipart/form-data`.

Accepted image MIME types must start with `image/`, and the filename extension must be one of:

- `.jpg`
- `.jpeg`
- `.png`
- `.webp`

The response includes the uploaded filename, prediction, and confidence.

### `POST /video`

Send a single file field named `file` using `multipart/form-data`.

Accepted video MIME types must start with `video/`, and the filename extension must be one of:

- `.mp4`
- `.avi`
- `.mov`
- `.mkv`

The API saves the upload to a temporary file, extracts clear frames, runs each frame through the classifier, and returns the most common prediction plus the average confidence.
