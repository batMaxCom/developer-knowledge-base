# Rules — условия запуска pipeline и jobs

rules определяют:

- запускать job или нет
- когда запускать
- в каком режиме запускать

## Базовый синтаксис
```yaml
rules:
  - if: условие1
  - if: условие2
  - when: never
```
Что происходит:
- первая подошедшая rule — применяется
- остальные игнорируются

Пример:
```yaml
job:
  script: echo "Run"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```

`job` выполнится только в ветке main.

## Типы условий

1. По ветке

```
- if: '$CI_COMMIT_BRANCH == "main"'
```
2. По merge request
```
- if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
```
3. По тегу
```
- if: '$CI_COMMIT_TAG'
```
4. По изменённым файлам
```
- changes:
    - backend/**
```
`job` выполнится, если изменились файлы

5. Комбинации
```
- if: '$CI_COMMIT_BRANCH == "main" && $CI_PIPELINE_SOURCE == "push"'
```

##  When - Управляет поведением job

1. Авто (по умолчанию)
```
when: on_success
```
2. Ручной запуск
```
when: manual
```
появится кнопка в UI

3. Всегда
```
when: always
```
даже если предыдущие jobs упали

4. Никогда
```
when: never
```
отключает job

