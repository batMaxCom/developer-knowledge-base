# Структура проекта
После команды
```bash
uv init
```
Получаем:
```yaml
project/
├── pyproject.toml   👈 главный файл
├── uv.lock          👈 lock-файл (аналог poetry.lock)
├── .python-version  👈 версия Python
├── README.md
└── src/
    └── project_name/
        └── __init__.py
```
## pyproject.toml

### [project] — основа
```yaml
[project]
name = "my-app"
version = "0.1.0"
requires-python = ">=3.12"
```


### dependencies
```yaml
dependencies = [
    "fastapi",
    "uvicorn",
]
```

### dev зависимости
```yaml
[dependency-groups.dev]
dev = [
    "pytest",
    "ruff"
]
```

### scripts (очень полезно)

Можно добавить:
```yaml
[project.scripts]
start = "uvicorn main:app --reload"
```
Можно запустить командой:
```bash
uv run start
```

## uv.lock
uv.lock - это детерминированные версии зависимостей

