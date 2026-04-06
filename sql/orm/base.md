# Основы ORM

ORM (Object–Relational Mapping) — это техника связывания объектов Python с строками в SQL-таблицах.

Основной элемент ORM — Declarative Base

Это центральная точка, из которой создаются все ORM-модели.

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

Теперь каждый ORM-класс нужно наследовать от Base.

## Объявление модели

```python
from sqlalchemy import Column, Integer, String
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False, unique=True)
    age = Column(Integer)
```

SQLAlchemy автоматически создаёт:

таблицу users

объект Table

мэппинг класса <-> строки таблицы

## Column() и типы данных
Основной синтаксис
```python
Column(<тип>, параметры...)
```

Основные типы:
- Integer
- String
- Boolean
- Float
- Date, DateTime
- JSON
- ARRAY
- Enum

Часто используемые параметры:
- primary_key=True
- unique=True
- nullable=False
- default=...
- server_default=text('NOW()')
- ForeignKey(...)
- 
Пример:
```python
from sqlalchemy import Boolean, DateTime, func

is_active = Column(Boolean, default=True)
created_at = Column(DateTime, server_default=func.now())
```

## Primary Key и Foreign Key
- Primary Key
```python
id = Column(Integer, primary_key=True)
```
- Foreign Key
```python
user_id = Column(Integer, ForeignKey("users.id"))
```

## Как объекты связаны со строками таблицы

Когда ты создаёшь объект:

```python
user = User(email="a@b.c", age=20)
```
Он ещё не в базе → это состояние называется transient.

Порядок:
- После session.add(user) → pending
- После commit → persistent
- Если session закрылась → detached

## Session и Unit of Work

Session — это:

- менеджер состояний объектов
- кэш
- UoW (Unit of Work) — механизм откладывания изменений до commit

Создание Session:
```python
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

engine = create_engine("postgresql+psycopg://user:pass@localhost/db")

with Session(engine) as session:
    ...
```