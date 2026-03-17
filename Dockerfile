# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy source and install the project itself
COPY . .
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.13-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8080"]
