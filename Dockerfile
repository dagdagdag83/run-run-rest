# Use Python 3.14 slim image
FROM python:3.14-slim

# Extract uv binary directly from astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Install system dependencies required by Kaleido (Chromium headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    fontconfig \
    libfontconfig1 \
    libnss3 \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libcups2 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Install dependencies (utilizing Docker layer caching effectively)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY . /app

# Re-sync to install the application and update state
RUN uv sync --frozen

# Cloud Run injects the PORT environment variable (default 8080)
ENV PORT=8080

# Execute server
CMD ["sh", "-c", "uv run uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips=\"*\""]
