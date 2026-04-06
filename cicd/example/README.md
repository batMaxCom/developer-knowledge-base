## .gitlab-ci.yml

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