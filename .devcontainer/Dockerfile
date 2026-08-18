FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

# Install a pinned uv version.
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*