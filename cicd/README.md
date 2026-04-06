# Как устроен GitLab CI/CD

## Структура документации

- [Структура проекта](./stucture.md)
- [Stages и Jobs](./stages_jobs.md)
- [Runner](./runner.md)
- [Rules](./rules.md)
- [Переменные окружения](./environment.md)
- [Docker в GitLab CI/CD](./docker.md)
- [BuildKit](./buildkit.md)
- [Cache, Artifacts, Dependencies](./cache_artifacts_dependencies.md)
- [Deploy](./deploy.md)
- [Базовый пример](./example/README.md)

Пример потока
```
git push → pipeline → stages → jobs → runner → результат
```
## Компоненты

### `Pipeline` - это весь процесс автоматизации.

Он создаётся, когда происходит событие:
- git push
- merge request
- ручной запуск
- cron (schedule)

### `Stage`(этапы) - это набор `jobs`



Пример:
```yaml
stages:
  - lint
  - test
  - build
  - deploy
```

Если один stage `упал` - дальше `не идём` (по умолчанию).

### `Job` - это один шаг в `stage`

`Job` - это конкретная задача. `Job` = "выполни вот эти команды".

```yaml
test_api:
  stage: test
  script:
    - pytest
```

### `Runner` - исполнитель

`Runner` - это процесс (или контейнер), который:

- забирает job
- запускает его
- возвращает результат

Типы runner:
- Shared (от GitLab)
- Specific (твой сервер)
- Docker runner (самый популярный)

## Выполнение кода

```yaml
image: python:3.12
```

Код выполняется в runner:
- runner поднимет контейнер python:3.12
- выполнит команды внутри него

## Особенности
1. `CI/CD` - это декларация

```
Ты описываешь, а GitLab исполняет.
```
2. Jobs независимы
```
Каждый `job`:
- запускается в чистом окружении
- не "помнит" предыдущий

Если нужны объеты прошлы сборок, используют::
- cache
- artifacts
```
3. Pipeline = граф
```
Это не просто последовательность
Можно делать параллельные jobs, зависимости (needs)
```

