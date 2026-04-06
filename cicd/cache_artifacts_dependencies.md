# cache, artifacts и dependencies

[Вернуться](./README.md)

Отличие:

| Что                  | 	Для чего                                   |
|----------------------|---------------------------------------------|
| cache                | 	ускорение (повторное использование файлов) |
| artifacts            | 	передача результатов между jobs            |
| dependencies / needs | 	управление тем, откуда брать artifacts     |

## cache — ускорение

Используется для:
- pip
- node_modules
- build cache

# Пример (Python)
```yaml
variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

test:
  script:
    - pip install -r requirements.txt
    - pytest
```

Что происходит:
- первый pipeline → скачивает зависимости
- сохраняет cache
- следующий pipeline → использует cache

## artifacts — передача данных

Используется для:
- build → deploy
- test reports
- coverage
- бинарники

Пример:
```yaml
build:
  script:
    - mkdir dist
    - echo "app" > dist/app.txt
  artifacts:
    paths:
      - dist/

deploy:
  script:
    - cat dist/app.txt
```

Что происходит:
- job создаёт файлы
- GitLab сохраняет их
- следующий job скачивает

`expire_in` задает время жизни
```yaml
artifacts:
  paths:
    - dist/
  expire_in: 1 hour
```

## dependencies / needs — управление зависимостями
```yaml
deploy:
  dependencies:
    - build
```
скачай artifacts только из build

```yaml
deploy:
  needs:
    - job: build
      artifacts: true
```
Что происходит:
- ускоряет pipeline
- даёт доступ к artifacts