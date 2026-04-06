# Транзакции

SQLAlchemy Core НЕ делает автокоммит.
Любое изменение данных (INSERT/UPDATE/DELETE) — выполняется внутри транзакции.

Варианта управления транзакциями:

1. `connection.begin()` — контекстная транзакция
```python
with engine.connect() as conn:
    with conn.begin():
        conn.execute(insert(users).values(name="John"))
        conn.execute(insert(users).values(name="Mike"))
```

Автоматически делает:
- BEGIN
- ваши операции
- COMMIT при выходе
- ROLLBACK при исключении

2) Явная транзакция
```python
conn = engine.connect()
trans = conn.begin()

try:
    conn.execute(insert(users).values(name="Alice"))
    trans.commit()
except:
    trans.rollback()
    raise
```
## SAVEPOINT (точки сохранения)

Используется в сложных сценариях, когда нужно откатить только часть транзакции.
```python
with engine.connect() as conn:
    with conn.begin() as trans:
        conn.execute(insert(users).values(name="A"))

        sp = trans.begin_nested()  # SAVEPOINT

        try:
            conn.execute(insert(users).values(id=1, name="DuplicateID"))
            sp.commit()  # OK
        except:
            sp.rollback()  # откатить только вложенную часть

        conn.execute(insert(users).values(name="B"))
```
SQLAlchemy автоматически генерирует:
```sql
BEGIN
INSERT ...
SAVEPOINT sa_savepoint_1
INSERT ...
ROLLBACK TO SAVEPOINT sa_savepoint_1
RELEASE SAVEPOINT sa_savepoint_1
INSERT ...
COMMIT
```

## Nested transactions (вложенные)

Это не настоящие "nested transactions", а цепочка SAVEPOINT’ов.

Пример:
```python
with conn.begin() as trans1:
    ...

    with conn.begin_nested() as trans2:
        ...

    with conn.begin_nested() as trans3:
        ...
```

Используется, например, в тестах.