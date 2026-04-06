# Runner 

[Вернуться](./README.md)

`GitLab Runner` — это приложение-исполнитель, которое берёт job из pipeline и запускает его на выделенной инфраструктуре.

Что делает `GitLab Runner`:
- клонирует проект 
- подготавливает окружение 
- выполняет команды из script 
- работает с cache/artifacts
- возвращает статус job в GitLab

# Типы Runner
GitLab различает `instance runners`, `group runners` и `project runners`.
Это значит, что runner может быть доступен всему инстансу GitLab, группе проектов или только одному проекту. 

`Instance runners` используют `fair usage queue`, чтобы один проект не забирал все ресурсы.

Практически это значит:

- project runner — самый предсказуемый вариант для своего проекта;
- group runner — удобно для нескольких сервисов одной команды;
- instance runner — общий пул для многих проектов.

## Executors

У runner есть `executor` — `механизм выполнения job`.

GitLab Runner поддерживает несколько executor’ов:
- shell
- docker

Есть и другие, включая `custom executor` и `autoscaling instance executor`.

### Shell executor

Запускает job как обычный процесс на хостовой машине.
Пример:
- `script` выполняется почти так же, как если бы ты сам вошёл по SSH на машину и запустил команды.

### Docker executor

Запускает job внутри `Docker-образа`. Это даёт одинаковое окружение для каждого job и делает pipeline воспроизводимее.

Пример:
```yaml
image: python:3.12

test:
  script:
    - python --version
    - pytest
```
Что происходит: 
- поднимет контейнер python:3.12
- выполнит job внутри него 

# Теги runner

Чтобы `job` запускался именно на нужном `runner`, обычно используют `tags`. Тогда GitLab подберёт runner с совпадающими тегами.

```yaml
test:
  tags:
    - docker
  script:
    - pytest
```

Что происходит:
- runner зарегистрирован с тегом docker;
- job тоже просит docker;
- значит job уйдёт именно туда.
