# GenAI Gallery Backend

Backend service for the GenAI Gallery application.

## Installation

No installation required, just use `uvx genai_gallery`, but at least one environment variable is required: `IMAGES_DIR`.


## running locally for development

You can run the backend with hot reload enabled for development:

```bash
uv run uvicorn genai_gallery.main:app --reload
```

## Running as a tool (Simulated PyPI)

You can build the package and run it as if it were installed from PyPI:

```bash
# Build the package
uv build

# Run the package from the built wheel (replace version as needed)
export IMAGES_DIR=/path/to/images
uv tool run --from ./dist/genai_gallery-0.1.0-py3-none-any.whl genai_gallery
```
