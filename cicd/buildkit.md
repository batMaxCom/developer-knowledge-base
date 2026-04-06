# BuildKit

[Вернуться](./README.md)

`BuildKit` — это новый backend для сборки Docker-образов, который:

быстрее классического docker build
умеет кэшировать шаги
поддерживает параллельные сборки
лучше работает с секретами и зависимостями

`buildctl` — это способ управлять BuildKit напрямую, без Docker CLI.
Пример:
```yaml
buildctl build \
      buildctl-daemonless.sh build \
        --frontend dockerfile.v0 \ # "используй Dockerfile как источник сборки"
        --opt target="${TARGET}" \ # аналог FROM ... AS builder
        --local context=./ \ # "путь к исходникам"
        --local dockerfile=./ \ # "путь к Dockerfile"
        --import-cache type=s3,endpoint_url=${MINIO_ENDPOINT},bucket=${MINIO_BUCKET},region=us-east-1,use_path_style=true,access_key_id=${MINIO_ACCESS_KEY},secret_access_key=${MINIO_SECRET_KEY},name=${NAME_CACHE} \
        --export-cache type=s3,endpoint_url=${MINIO_ENDPOINT},bucket=${MINIO_BUCKET},region=us-east-1,use_path_style=true,access_key_id=${MINIO_ACCESS_KEY},secret_access_key=${MINIO_SECRET_KEY},name=${NAME_CACHE},mode=max \
        --output type=image,push=false,name=dummy:latest # собрать Docker image, НЕ пушить, назвать dummy:latest
```

Что происходит:
- берется Dockerfile
- собирается образ через BuildKit
- результат — Docker image

Параметры:
- 

## Кэширование

###`import-cache` - “скачай кэш перед билдом и попробуй его использовать”

Что происходит:
- Подключается к S3 (MinIO)
- Скачивает metadata кэша
- При каждом шаге:
  - проверяет: есть ли такой слой?
  - если да → НЕ выполняет команду

Аналогично:
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
```
Если:
- requirements.txt не менялся
- RUN pip install не выполнится вообще


Без import-cache каждый CI билд:
- начинается с нуля
- даже если ничего не изменилось

### `export-cache` - “сохрани результат билда как кэш для будущих сборок”

Что проиходит:
- BuildKit берёт все слои
- Сохраняет их в S3
- Добавляет metadata (граф зависимостей)

`mode=min`:
- сохраняет только финальные слои
- меньше размер
- хуже кэш

`mode=max`:
- сохраняет ВСЕ промежуточные слои
- лучший performance
- больше storage

### Совместная работа

Как они работают вместе
Первый билд (кэша нет):
- import-cache → пусто
- build → всё собирается
- export-cache → сохраняем

Второй билд:
- import-cache → подтянули кэш
- build → 80–95% шагов пропущено
- export-cache → обновили

### Типы кэша

`type=s3` - общий кэш между CI раннерами

`type=registry,ref=my-image:cache` - кэш, который хранится в Docker registry

`type=local,dest=./cache` - локально (для dev)

`--build-arg BUILDKIT_INLINE_CACHE=1` кэш внутри image