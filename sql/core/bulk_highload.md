# Bulk-операции и Highload

Почему bulk-операции особые?

Обычные conn.execute(insert(...)):
- отправляют один statement за раз
- совершают много round-trips
- работают медленно при больших данных

Bulk-операции используют:
- executemany
- batched INSERT/UPDATE
- prepared statements (server-side prepared statements)
- psycopg2 fast execution helpers
- SQLAlchemy параметризацию (expanding)

## executemany — основа массовых вставок

SQLAlchemy автоматически использует executemany, если вы передаёте массив данных:

Пример — вставка 10k строк
```python
rows = [
    {"name": f"user_{i}", "age": i % 50}
    for i in range(10000)
]

stmt = insert(users)

with engine.begin() as conn:
    conn.execute(stmt, rows)

```

Что SQLAlchemy делает:
- одна подготовка запроса
- много “executemany” отправок драйверу

## Bulk insert через Core (самый быстрый способ)

Если готов массив словарей — это лучший вариант.
```python
data = [{"id": i, "value": f"v{i}"} for i in range(100_000)]

with engine.begin() as conn:
    conn.execute(insert(table), data)
```

## batch inserts — разделение на пачки

Для больших загрузок (100k–10M записей) важно разбивать на чанки.
```python
BATCH = 5000
data = [...]

with engine.begin() as conn:
    for i in range(0, len(data), BATCH):
        chunk = data[i:i+BATCH]
        conn.execute(insert(table), chunk)
```

Почему важно:
- снижает память драйвера
- уменьшает размер TCP-пакетов
- оптимально для PostgreSQL

## Bulk UPDATE (батчами)

SQLAlchemy не умеет делать multi-row UPDATE “по умолчанию”,
но можно выполнить батчи UPDATE по условиям.

Пример:
```python
updates = [
    {"id": i, "value": f"new_{i}"}
    for i in range(50_000)
]

stmt = (
    update(table)
    .where(table.c.id == bindparam("id"))
    .values(value=bindparam("value"))
)

with engine.begin() as conn:
    conn.execute(stmt, updates)

```
Это выполняет:
- один prepared statement
- executemany параметров

Скорость: до 10k updates/sec.

## Prepared statements в SQLAlchemy (server-side)

В PostgreSQL можно заставить драйвер использовать server-side prepared statements.

Пример с psycopg2:
```python
engine = create_engine(
    URL,
    execution_options={"prepared": True}
)
```

Теперь все запросы автоматически используют prepare → execute.

Плюсы:

- ускорение 10–30% на highload
- особенно полезно для UPDATE/INSERT

## Bulk операции через text() + executemany

Самый низкоуровневый вариант.
```python
stmt = text("INSERT INTO logs (level, msg) VALUES (:level, :msg)")

with engine.begin() as conn:
    conn.execute(stmt, bulk_data)
```
Это:
- использует executemany
- максимально близко к драйверу
- быстрее ORM/Expression API