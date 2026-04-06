# .gitlab-ci.yml

Является главным орекстратором.

Что содержит:
- объявляет общие stages
- задаёт глобальные variables
- определяет, когда вообще создавать pipeline через workflow
- подключает остальные файлы через include

## Разбор по модулям

1. `stages` - список этапов pipeline. Указывает порядок выполнения
```yaml
stages:
  - lint # linter, автопроверка качества кода
  - check-build # проверка сборки проекта
  - semantic-release # автоматическое создание релизов
  - build # создание образа и загрузка в registry
  - trigger-deploy # запуск деплоя
```

2. `variables` - глобальные переменные, которые используются во всех pipeline

Их можно использовать в:
- jobs
- scripts
- include-файлы
- Docker image теги
- shell-команды

Каждую переменную можно переопределить в .gitlab-ci.stage-pipeline.yml файлах.

Пример:
```yaml
variables:
  PYTHON_VERSION: "${PYTHON_VERSION:-3.12}" # версия python
  UV_VERSION: "${UV_VERSION:-0.8.0}" # версия uv
  BUILDKIT_ROOTLESS_VERSION: "${BUILDKIT_ROOTLESS_VERSION:-0.23.2}" # версия buildkit
```

Синтаксис `${VARIABLE:-DEFAULT_VALUE}` - если переменная не задана, то берётся значение по умолчанию.

3. `workflow` - определяет при каких условиях создавать pipeline

Пример:
```yaml
workflow:
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - if: '$CI_COMMIT_TAG'
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS'
      when: never
    - when: never
```

### `$CI_COMMIT_BRANCH == "main"`

Если pipeline запущен для ветки main, то pipeline создаётся.

Пример:
- запушил коммит прямо в main
- pipeline стартует

### `$CI_COMMIT_TAG`

Если pipeline запускается по git tag — тоже запускаем.

Пример:
- создан тег v1.2.0
- pipeline стартует

Важно для release/build/deploy процессов.

### `$CI_PIPELINE_SOURCE == "merge_request_event"`

Если pipeline создан в контексте Merge Request, он запускается.

Пример:

- открыл MR из feature/auth в main
- GitLab создаст MR pipeline

Это удобно, потому что можно проверять код до merge.

### `$CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS`
Необходимо, чтобы не запускать pipeline, если есть открытый Merge Request.

Правило:
- если это обычный pipeline ветки
- и у этой ветки уже есть открытый Merge Request
- тогда не запускать branch pipeline

### Последнее правило "- when: never"

Если ни одно условие выше не подошло —
pipeline не создаётся.

4. `include` - подключает другие файлы

Необходимо для разделения кода. 

`.gitlab-ci.yml` не разрастается, а логика раскладывается по отдельным stage-файлам.

#  Пример `Stages` (.lint.gitlab-ci.yml)

Отвечает за статическую проверку Python-кода. Прекращает выполнение pipeline, если есть ошибки.

Обычно запускают:
- ruff
- flake8
- black --check
- mypy

Иногда - pytest, но чаще отдельным job-ом.

## variables

Локальные переменные, которые используются только в этом job. Могут переопределить глобальные.

Пример:
```yaml
variables:
  WORKING_DIR: "src/"
  UV_VERSION: "0.11.1"
  PYTHON_VERSION: "3.12"
  BASE_LAYER: "alpine"
  UV_CACHE_DIR: ".uv_cache"
```

## stage
Явно указываем, что эта job относится к этапу(stage) `lint`

```yaml
stage: lint
```

## tags

Говорит о том, что эту job нужно отправлять только на runner, у которого есть тег `formatter`.

## image
```yaml
image: ghcr.io/astral-sh/uv:$UV_VERSION-python$PYTHON_VERSION-$BASE_LAYER
```
Контейнер, внутри которого job будет исполняться.

## script

Это основная логика job.

```yaml
script:
  - |
    uv sync --all-groups --frozen --no-editable
    echo "🧹 Запуск Ruff..."
    uv run ruff check --diff --config .ruff.toml .
    echo "🔍 Запуск MyPy..."
    uv run mypy --config-file .mypy.ini --exclude build .
    echo "🏁 Завершено линтинг UV (Ruff + MyPy) для ${WORKING_DIR}"
```

Что происходит:
- uv sync устанавливает зависимости проекта в окружение.
- запускает Ruff внутри окружения, созданного uv.
- MyPy проверяет типизацию Python-кода.

## after_script
Команды, которые выполнятся после script, даже если основной script упал.
```yaml
after_script:
  - uv cache prune --ci || true
```
Чистит кэш uv, оставляя только то, что полезно для CI.

`|| true` - если команда очистки по какой-то причине завершится с ошибкой, job всё равно не упадёт.

Необходимо, так как не критичная часть проверки кода.

## cache
```yaml
cache:
  key: # ключ кэша строится на основе файла
    files:
      - uv.lock
  paths: # кэширование директорий
    - .venv/
    - $UV_CACHE_DIR/
  policy: pull-push # сначала попытаться скачать существующий cache, после успешного выполнения обновить его
  when: on_success # Сохранять кэш только если job завершился успешно.
  untracked: false # Не включать в cache все неотслеживаемые файлы подряд.
```

## retry

Инструкция перезапуска job.

```yaml
retry:
  max: 2
  when:
    - runner_system_failure
    - stuck_or_timeout_failure
```

## rules

Условия, при которых должна срабатывать job.

```yaml
rules:
  - if: '$CI_COMMIT_BRANCH == "main" || $CI_PIPELINE_SOURCE == "merge_request_event"' # это ветка main или это pipeline Merge Request
    changes:
      - src/**/* # Изменения в основной директории
      - Dockerfile # Изменения в Dockerfile 
    when: always # Если правило совпало, job нужно запускать.
```