Session — это:

- Менеджер состояний объектов
Отвечает за то, какие объекты вставлять, обновлять, удалять.

- Кэш (Identity Map)
Одна строка таблицы = один объект Python в пределах сессии.

- Unit of Work
Сессия собирает изменения и отправляет их в базу одним пакетом.

- Транзакция
Каждая Session управляет транзакцией (автоматически или вручную).

## Жизненный цикл ORM-объекта

SQLAlchemy определяет 4 состояния ORM-объектов:
```
transient -> pending -> persistent -> detached
```
1. `transient` (ничейный объект)

Создан, но:

- нет связи с Session
- нет PK
- нет строки в БД
```python
user = User(name="Bob")  # transient
```

2. `pending` (ожидающий вставки)

После добавления в Session:
```python
session.add(user)  # pending
```

SQL ещё не выполнен.
Объект просто стоит в очереди UoW.

3. `persistent` (живой объект в сессии)

После flush или commit:
```python
session.commit()  # теперь persistent
```

Теперь:

- объект имеет PK
- связан с записью в БД
- отслеживается Session

4. `detached` (отсоединённый объект)

После закрытия сессии:
```python
session.close()
# или commit при expire_on_commit=True
```

Доступны только те поля, которые не expire'нулись.

## Автоматическое поведение Session

### autoflush
autoflush=True → перед каждым:
- query
- select
- join
- commit

… SQLAlchemy делает flush().

Пример
```python
user = User(name="Bob")
session.add(user)

session.query(User).all()  # flush произойдет автоматически
```
Выключение:

```python
Session(engine, autoflush=False)
```

### expire_on_commit
По умолчанию `expire_on_commit=True`.

Это значит, что после `commit` все объекты становятся `полусырыми`.

Доступ к любому полю приводит к автоматическому SELECT.

Выключение:
```python
Session(engine, expire_on_commit=False)
```
Для чего нужно?
- экономия памяти
- согласованность с БД: данные всегда актуальны

## flush vs commit
### flush
`flush` = слить изменения в SQL (но НЕ завершить транзакцию)

Что делает:
- формирует SQL: INSERT/UPDATE/DELETE
- отправляет их
- но транзакция остаётся открытой
```python
session.flush()
```

Когда происходит автоматически?
- на query()
- перед commit()
- на ручной flush()
- при autoflush=True

### commit
`commit` = завершить транзакцию
```python
session.commit()
```

commit:
- вызывает flush()
- завершает транзакцию
- делает expire всех объектов (если expire_on_commit=True)

## refresh — ручная перезагрузка объекта

Если объект:
- изменён извне
- устарел
- вы хотите получить только что обновлённые данные
```python
session.refresh(user)
```

Это выполняет:
```sql
SELECT * FROM users WHERE id = ...
```

И обновляет объект из БД.