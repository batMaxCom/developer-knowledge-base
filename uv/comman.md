# Комманды

## Создание проекта
```bash
uv init
```

Создаёт:

- pyproject.toml
- .python-version

## Установка зависимостей
```bash
uv add fastapi
uv add sqlalchemy
```

Dev-зависимости:
```bash
uv add --dev pytest
```

## Обновить зависимости
```bash
uv add fastapi@latest
```

## Запуск проекта
```bash
uv run python main.py
```
автоматически поднимет окружение

## Работа с Python
```bash
uv python list
uv python install 3.11
uv python use 3.11
```

## Аналог pip
```bash
uv pip install requests
uv pip list
uv pip freeze
```

##Синхронизация зависимостей
```bash
uv sync
```
Что происходит:
- читает uv.lock
- ставит точные версии
- создаёт venv (если нет)

## Удаление зависимостей
```bash
uv remove fastapi
```

## Виртуальное окружение
```bash
uv venv
```
Но обычно сам создаёт и управляет venv

## Обновить lock
```bash
uv lock
```

## ruff - линтер и форматтер для Python

Установка 
```bash
uv add --dev ruff
```
Проверка кода
```bash
uv run ruff check .
```
Авто-исправление
```bash
uv run ruff check . --fix
```
Форматирование (аналог black)
```bash
uv run ruff format .
```
Конфиг Ruff (в pyproject.toml)
```yaml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I"]
ignore = ["E501"]
```
Что означают правила:

| Код | 	Значение     |
|-----|---------------|
| E   | 	стиль (PEP8) |
| F   | 	ошибки       |
| I   | 	импорты      |

Использование локально:
```bash
uv run ruff check . --fix
uv run ruff format .
```

Использование в CI:
```bash
uv run ruff check .
uv run ruff format --check .
```