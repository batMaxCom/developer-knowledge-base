# Relationship

relationship() — это способ связать Python-классы между собой.

Он `НЕ создаёт колонку в БД`.
Колонку `создаёт ForeignKey`.

Пример:
```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
```

`ForeignKey` - создаёт связь на уровне SQL.
`relationship` - описывает поведение на уровне Python.
## Связи
### One-to-Many (один ко многим)

Типичный пример:
User → Post

Модель User:
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    posts = relationship("Post", back_populates="user")
```
Модель Post:
```python
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="posts")
```
Поведение:

- user.posts → список постов
- post.user → объект владельца

### Many-to-One (многие к одному)

Это просто "обратная сторона" one-to-many:

Post → User
```python
post.user     # many-to-one
user.posts    # one-to-many
```
## Many-to-Many

Используется вспомогательная таблица.

Вспомогательная таблица:
```python
article_category = Table(
    "article_category",
    Base.metadata,
    Column("article_id", ForeignKey("articles.id"), primary_key=True),
    Column("category_id", ForeignKey("categories.id"), primary_key=True),
)
```
Модель Article:
```python
class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)

    categories = relationship(
        "Category",
        secondary=article_category,
        back_populates="articles"
    )
```
Модель Category:
```python
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)

    articles = relationship(
        "Article",
        secondary=article_category,
        back_populates="categories"
    )
```

## back_populates vs backref
### back_populates

— Чёткое двустороннее определение связей
```python
posts = relationship("Post", back_populates="user")
user = relationship("User", back_populates="posts")
```
### backref

— Одной строчкой создаёт связь в обоих направлениях
```python
posts = relationship("Post", backref="user")
```
`back_populates` предпочтительнее, потому что:
- более прозрачен
- легче читать
- можно задавать параметры отдельно

## Каскады в relationship

Каскады описывают правила:

Что должно происходить с дочерними объектами при изменениях родителя?

Основные каскады
1) `save-update`

Передача Session родителю → детям

Это поведение по умолчанию.

2) `delete`

Удаление родителя удаляет детей.
```python
relationship(..., cascade="delete")
```
3) `delete-orphan`

Удаление ребёнка из коллекции → удаляет его из БД.

Пример ORM поведения:
```python
user.posts.remove(post)

# post будет удалён из таблицы posts
```
Использовать ТОЛЬКО если:
- пост не может существовать без user