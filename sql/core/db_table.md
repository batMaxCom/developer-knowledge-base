from psutil import users

#  SQLAlchemy Core

SQLAlchemy Core — это низкоуровневый слой, который даёт:
- управление соединениями (Engine, Connection)
- описание схемы (MetaData, Table, Column)
- типы данных (Integer, String, DateTime, Numeric…)
- генерацию SQL (SQL Expression Language)
- выполнение запросов (select, insert, update, delete)

## Engine — подключение к базе

Engine — фабрика соединений, входная точка в SQLAlchemy.
```python
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg2://user:pass@localhost:5432/dbname")
```

Engine:
- не открывает соединение сразу
- создаёт пул соединений
- управляет транзакциями
- используется для получения Connection

### Connection — реальное соединение
```python
with engine.connect() as conn:
    result = conn.execute(...)
```

Connection:
- отправляет SQL в БД
- управляет транзакциями (begin())

Пример транзакции:
```python
with engine.begin() as conn:
    conn.execute(...)
    conn.execute(...)
```

`begin()` автоматически делает COMMIT/ROLLBACK.

## MetaData — контейнер для таблиц

Это объект, который хранит все Table.
```sql
from sqlalchemy import MetaData

metadata = MetaData()
```

## Table — описание таблицы
from sqlalchemy import Table, Column, Integer, String
```python
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50)),
    Column("email", String(100)),
)
```

## Композиция запросов (самая сильная часть SQLAlchemy Core)

SQLAlchemy Core умеет:
- объединять запросы
- строить подзапросы
- алиасы (alias)
- CTE

### Пример JOIN
```python
stmt = (
    select(users.c.name, orders.c.price)
    .select_from(users.join(orders, users.c.id == orders.c.user_id))
)
```

### Подзапрос
```python
subq = (
    select(orders.c.user_id)
    .where(orders.c.price > 1000)
    .subquery()
)

stmt = select(users).where(users.c.id.in_(subq))
```

### CTE
```python
cte = (
    select(orders.c.*, orders.c.price * 0.9)
    .cte("discounted")
)

stmt = select(cte).where(cte.c.price > 100)
```

### RAW SQL
```python
from sqlalchemy import text

stmt = text("SELECT * FROM users WHERE id = :id")

conn.execute(stmt, {"id": 20})
```

# Примеры
1) Найти пользователя, у которого максимальный заказ (MAX)
```python

subq = (
    select(
        orders.c.user_id, 
        func.max(orders.c.price).label("max_amount"))
    .group_by(orders.c.user_id)
    .subquery()
)

stmt = (
    select(users, subq.c.max_amount)
    .join(subq, users.c.id == subq.c.user_id)
    .order_by(subq.c.max_amount.desc())
    .limit(1)
)

result = connection.execute(query).fetchone()
```

2) Написать JOIN users + orders + фильтр по дате
```python
stmt = (
    select(users, orders)
    .join(orders, users.c.id == orders.c.user_id)
    .where(orders.c.created_at == date_filter)
)

result = connection.execute(query).all()
```

3) Переписать запрос с подзапросом через join (оптимизация)
```python
stmt = (
    select(users)
    .join(orders, users.c.id == orders.c.user_id)
    .where(orders.c.created_at == date_filter)
)
```
4) Создать CTE, в котором к каждому заказу добавляется скидка 10%, и выбрать из него только заказы > 2000 после скидки
```python
sale_price_cte = (
    select(
        orders.c.id,
        orders.c.price,
        (orders.c.price * 0.9).label("discount_price")
    )
).cte("sale_price_cte")

stmt = (
    select(
        sale_price_cte.c.id,
        sale_price_cte.c.price,
        sale_price_cte.c.discount_price
    )
    .where(sale_price_cte.c.discount_price > 2000)
)

rows = connection.execute(stmt).all()
```

## Создание индексов

SQLAlchemy позволяет создать индекс прямо из Core.

Пример:
from sqlalchemy import Index
```python
index_users_name = Index("ix_users_name", users.c.name)
index_users_name.create(engine)
```
Удалить индекс:
```python
index_users_name.drop(engine)
```
## Constraints (ограничения)
- UNIQUE
```python
from sqlalchemy import UniqueConstraint

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String),
    UniqueConstraint("email")
)
```
- CHECK
```python
from sqlalchemy import CheckConstraint

orders = Table(
    "orders",
    metadata,
    Column("price", Integer),
    CheckConstraint("price > 0")
)
```
- FOREIGN KEY
```
from sqlalchemy import ForeignKey

orders = Table(
    "orders",
    metadata,
    Column("user_id", Integer, ForeignKey("users.id"))
)
```