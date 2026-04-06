# Docker

Пример Docker файла:
```dockerfile
FROM python:3.12-slim AS builder

# Полезные флаги Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Копируем uv из официального образа Astral
COPY --from=ghcr.io/astral-sh/uv:0.11.1 /uv /uvx /bin/

WORKDIR /app

# Сначала только файлы зависимостей — ради кэша Docker
COPY pyproject.toml uv.lock ./

# Ставим только runtime-зависимости, без dev и без самого проекта
RUN uv sync --frozen --no-dev --no-install-project

# Теперь копируем код проекта
COPY . .

# Ставим уже сам проект
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8000

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Пример с включенным BuildKit
```dockerfile
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:0.11.1 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app /app

CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
UV агрессивно использует кэш зависимостей, и официальная документация рекомендует сохранять этот кэш между запусками, чтобы не скачивать и не пересобирать зависимости повторно.

# CI/CD
Прмиер:
```yaml
stages:
  - lint
  - test
  - build

variables:
  UV_VERSION: "0.11.1"
  PYTHON_VERSION: "3.12"
  BASE_LAYER: "bookworm-slim"
  UV_LINK_MODE: "copy"
  UV_CACHE_DIR: ".uv-cache"

cache:
  key:
    files:
      - uv.lock
  paths:
    - .uv-cache

lint:
  stage: lint
  image: ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-${BASE_LAYER}
  script:
    - uv sync --frozen --dev
    - uv run ruff check .
    - uv run ruff format --check .
  after_script:
    - uv cache prune --ci

test:
  stage: test
  image: ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-${BASE_LAYER}
  script:
    - uv sync --frozen --dev
    - uv run pytest
  after_script:
    - uv cache prune --ci

build:
  stage: build
  image: docker:27
  services:
    - docker:27-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker build -t my-backend:${CI_COMMIT_SHORT_SHA} .
```