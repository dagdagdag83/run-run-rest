# Use Python 3.14 slim image
FROM python:3.14-slim

# Extract uv binary directly from astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Install dependencies (utilizing Docker layer caching effectively)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . /app

# Re-sync to install the application and update state
RUN uv sync --frozen

# Execute server
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
