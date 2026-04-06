# Raw SQL

SQLAlchemy позволяет работать как с ORM/Expression Language, так и с чистым SQL.

1. text() — написание чистого SQL
from sqlalchemy import text
```python
stmt = text("SELECT * FROM users WHERE id = :x")
result = conn.execute(stmt, {"x": 1})
```
Именованные параметры обязательно начинаются с `:`.

2. bindparams() — жёсткая привязка параметров

Позволяет задать тип, значение по умолчанию, NULL:
```python
stmt = (
    text("SELECT * FROM users WHERE age > :min_age")
    .bindparams(bindparam("min_age", type_=Integer))
)
```

3. columns() — описать структуру результата
Когда SQLAlchemy не знает структуру ответа (например, функция возвращает JSONB), мы можем её указать:
```python
stmt = (
    text("SELECT id, data FROM users")
    .columns(id=Integer, data=JSONB)
)
result = conn.execute(stmt).fetchall()
```
4. Raw SQL с JSON / JSONB
- Фильтр по JSONB:
```python
stmt = text("""
    SELECT *
    FROM users
    WHERE data->>'country' = :country
""")
result = conn.execute(stmt, {"country": "USA"})
```
- Извлечение вложенного JSON:
```python
stmt = text("""
    SELECT data->'address'->>'city' AS city
    FROM users
""")
```
- JSONB existence operator "?":
```python
stmt = text("""
    SELECT *
    FROM logs
    WHERE metadata ? :key
""")
conn.execute(stmt, {"key": "error"})
```
5. Вызов PostgreSQL функций
Функция, возвращающая scalar:
CREATE FUNCTION add_two(a int, b int)
RETURNS int AS $$
BEGIN
    RETURN a + b;
END;
$$ LANGUAGE plpgsql;


Вызов:

stmt = text("SELECT add_two(:a, :b)")
result = conn.execute(stmt, {"a": 10, "b": 20}).scalar()

6. Вызов stored procedures (CALL)

В PostgreSQL:
```sql
CREATE PROCEDURE log_event(msg text)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO events (message) VALUES (msg);
END;
$$;
```

Вызов:
```python
stmt = text("CALL log_event(:msg)")
conn.execute(stmt, {"msg": "Hello"})
```
7. Вызов функции, возвращающей SETOF (таблица)
```sql
CREATE FUNCTION get_users()
RETURNS TABLE(id INT, email TEXT)
AS $$
BEGIN
    RETURN QUERY SELECT id, email FROM users;
END;
$$ LANGUAGE plpgsql;
```

SQLAlchemy:
```python
stmt = text("SELECT * FROM get_users()").columns(
    id=Integer,
    email=String,
)

rows = conn.execute(stmt).fetchall()
```