# join и оптимизация

## join() — обычный SQL JOIN

Используется, когда тебе нужно фильтровать, сортировать, группировать по связанной таблице.

Пример:
```python
stmt = (
    select(User)
    .join(User.orders)
    .where(Order.price > 1000)
)
```

Это превращается в:
```sql
SELECT user.*
FROM user
JOIN orders ON orders.user_id = user.id
WHERE orders.price > 1000
```
join делает:
- соединение таблиц в один SQL
- доступ к полям второй таблицы для WHERE / ORDER BY / GROUP BY

join НЕ загружает связи автоматически!

### Типы join
1. INNER JOIN
По умолчанию join() = INNER JOIN
2. OUTER JOIN

LEFT OUTER JOIN:
```python
stmt = (
    select(User, Order)
    .join(User.orders, isouter=True)
)
```
или
```python
select(User).outerjoin(User.orders)
```
3. JOIN по явному условию

Если нет relationship:
```python
stmt = (
    select(User, Order)
    .join(Order, User.id == Order.user_id)
)
```
4. join_from()

Используется, когда:

- связь сложная
- несколько JOIN подряд
- ORM не может догадаться "откуда"

Пример JOIN с непредсказуемым порядком:
```python
stmt = (
    select(User, Order, Product)
    .join_from(User, Order)
    .join_from(Order, Product)
)
```

## ORM JOIN vs Core JOIN

SQLAlchemy Core:
```python
select(User, Order).join(Order, User.id == Order.user_id)

```
ORM:
```python
select(User).join(User.orders)
```

Особенность	ORM:
- Работает с объектами ORM
- Можно использовать FK автоматически
- join по relationship
- автозагрузка связанных моделей

## Оптимизация
### Проблема N+1
Что такое N+1?

Представьте, что у нас есть:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    orders = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    user = relationship("User", back_populates="orders")
```

И мы выполняем:
```python
users = session.execute(select(User)).scalars().all()

for u in users:
    print(len(u.orders))
```

Что произойдёт:

- Первый запрос: SELECT * FROM users;
- Далее, для каждого пользователя отдельный запрос:
Варианты ORM-загрузки

SQLAlchemy предоставляет несколько стр атегий предзагрузки.

Таблица стратегий 

| Стратегия      | 	Тип      | 	Кол-во запросов | 	Годится для            |
|----------------|-----------|------------------|-------------------------|
| lazyload       | 	lazy     | 	N+1             | 	не рекомендуется       |
| selectinload   | 	eager    | 	2	              | большинство случаев     |
| joinedload     | 	eager    | 	1	              | маленькие связи         |
| subqueryload   | 	eager    | 	2	              | устаревшее, редко нужно |
| raiseload      | 	защитная | 	—	              | проверка против N+1     |
| contains_eager | 	ручная   | 	1	              | кастомные JOIN-запросы  |

### lazyload — стратегия по умолчанию
Как работает

SQLAlchemy загружает связанную коллекцию только при обращении к атрибуту.

То есть:
```python
u.orders
```

→ вызывает новый SQL-запрос.

Минусы:
- генерирует N+1
- непредсказуемо
- почти всегда хуже других методов

Где допустимо?
- при малой выборке (1–2 объекта)
- при использовании raiseload как защиты

### selectinload() — жадная загрузка через второй запрос

Используется, когда связанных данных много.

SQLAlchemy сначала `загружает родителей`, затем одним запросом — все `дочерние`:

```sql
stmt = select(User).options(selectinload(User.orders))
```

SQL:

1-й запрос — только users:
```sql
SELECT * FROM user;
```

2-й запрос — заказы только нужных пользователей:
```sql
SELECT * FROM orders WHERE user_id IN (1,2,3,...)
```
selectinload делает:
- НЕ использует JOIN
- Загружает связи во втором запросе
- Отлично масштабируется на большой one-to-many (миллионы строк)

Идеально для:

- User → Orders (1 → много)
- Blog → Posts
- Category → Products

Не подходит для:
- фильтрации (нет JOIN → нет доступа в WHERE)
- сортировки по связанным полям


### joinedload() — жадная загрузка через JOIN

Это не JOIN как фильтр, а JOIN как `способ получения связанных объектов`.

Пример:
```python
stmt = select(User).options(joinedload(User.orders))
```

SQL:
```sql
SELECT user.*, orders.*
FROM user
LEFT OUTER JOIN orders ON orders.user_id = user.id
```
joinedload делает:
- Загружает User и его orders за один SQL
- Вызывает LEFT JOIN
- Сохраняет ORM-структуру (User → list(Order))

Хорошо подходит для:
- one-to-one
- many-to-one
- небольших списков many-to-many / one-to-many (до ~100 элементов на сущность)

Недостатки
- дубликаты строк (картезианский продукт)
- плох для больших коллекций (много заказов)
- делает тяжёлые запросы

### raiseload — защита от N+1

`Запрещает` lazy loading.

Пример
```python
stmt = select(User).options(raiseload(User.orders))
```

Теперь, если код попытается обратиться к u.orders,
но связь не загружена явно — будет исключение.

Зачем нужно:
- для больших проектов: защита от случайных N+1
- для API: запрет скрытой подгрузки
- для безопасности и предсказуемости производительности



## Лучшие практики JOIN в ORM
- Используй selectinload для списков
- Используй joinedload только для 1:1
- Для фильтрации — всегда .join()
- Для загрузки без фильтрации — options()
- Не пиши условия join вручную, если есть relationship
- Избегай больших joinedload для коллекций (dupe rows)
- При сложных цепочках используй join_from()