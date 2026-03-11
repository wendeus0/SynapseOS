FROM golang:1.24-bookworm AS github-mcp-builder

ARG GITHUB_MCP_SERVER_VERSION=v0.32.0

RUN GOBIN=/out go install github.com/github/github-mcp-server/cmd/github-mcp-server@"${GITHUB_MCP_SERVER_VERSION}"

FROM python:3.12-slim-bookworm

ARG DEV_UID=1000
ARG DEV_GID=1000
ARG CODEX_NPM_PACKAGE=@openai/codex@0.112.0

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        bash \
        ca-certificates \
        git \
        less \
        nodejs \
        npm \
        openssh-client \
        procps \
        ripgrep \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${DEV_GID}" codex \
    && useradd --uid "${DEV_UID}" --gid "${DEV_GID}" --create-home --shell /bin/bash codex \
    && mkdir -p \
        /workspace \
        /home/codex/.codex \
        /home/codex/.cache/uv \
        /home/codex/.local/state \
        /home/codex/.local/share \
    && chown -R codex:codex /workspace /home/codex

RUN python -m pip install --upgrade pip uv \
    && npm install --global "${CODEX_NPM_PACKAGE}" \
    && npm cache clean --force

COPY --from=github-mcp-builder /out/github-mcp-server /usr/local/bin/github-mcp-server

WORKDIR /workspace
USER codex
