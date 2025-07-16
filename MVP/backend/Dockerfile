# Builder Stage
FROM docker.io/python:3.11-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential \
        gcc \
        pkg-config && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.1.39 /uv /usr/local/bin/uv

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY pyproject.toml .
RUN uv pip compile pyproject.toml -o requirements.txt
RUN uv pip install --no-cache-dir -r requirements.txt

# Final Stage
FROM docker.io/python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy virtual environment and application code
COPY --from=builder /opt/venv /opt/venv
COPY . .
COPY .env /app/.env

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

EXPOSE 8000

CMD ["sh", "-c", "python download_models.py && uvicorn api:app --host 0.0.0.0 --port 8000"]