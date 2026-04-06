# Структура .gitlab-ci.yml

[Вернуться](./README.md)

## Базовый пример:
```yaml
image: python:3.12 # Это Docker-образ, в котором выполняются jobs

stages: # Определяет порядок выполнения
  - test
  - build

variables: # Глобальные переменные. Для использования - $APP_ENV
  ENV: "test"

before_script: # Выполняется перед каждым job (напрмиер, установки зависимостей, подготовки окружения...)
  - pip install -r requirements.txt

test: # Job (ключевая сущность)
  stage: test
  script:
    - pytest

build:
  stage: build
  script:
    - echo "Build done"
```

## Элементы `Job`

### Управляет, когда job запускается

1. only / except (устаревающее)
```yaml
only:
  - main
```
```yaml
rules:
  - if: '$CI_COMMIT_BRANCH == "main"'
```
### Указывает, какой runner использовать
```yaml
tags:
  - docker
```
### Job может упасть, но pipeline не упадёт
```yaml
allow_failure: true
```
### Ручной запуск
```yaml
when: manual
```

### script (скрипты)
```yaml
script:
  - echo "Start"
  - pytest
```

`Важно`:

- каждая строка = отдельная команда
- выполняется как bash
### cache (ускоряет pipeline)
```yaml
cache:
  paths:
    - .cache/pip
```

### artifacts (сохраняет файлы между jobs)
```yaml
artifacts:
  paths:
    - dist/
  expire_in: 1 hour
```
### needs (запускает job после завершения другого)
```yaml
build:
  stage: build

deploy:
  stage: deploy
  needs: ["build"]
```