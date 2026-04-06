# Переменные и секреты

Это значения, которые доступны внутри job как environment variables.

```yaml
variables:
  APP_ENV: "dev"
```
Использование:
```yaml
variables:
  APP_ENV: "dev"
```

### Уровни переменных

Уровни переменных:

1. .gitlab-ci.yml
variables:
  DEBUG: "true"

НЕ безопасно - видно всем, у кого есть доступ к репозиторию.

2. Project Variables
```
Settings → CI/CD → Variables
```

Для чего использовать:
- токены
- пароли
- ключи

3. Group Variables - для нескольких проектов

## Типы переменных

### Masked - скрывает значение в логах

```yaml
echo $PASSWORD
# → ******
```
### Protected

Доступно только на:
- protected branches (main)
- protected tags

### File variables - хранит значение как файл

Пример:
- SSH ключ
- сертификат

Использование:
```yaml
echo "$SSH_KEY" > id_rsa
chmod 600 id_rsa
```
## Встроенные переменные

Пример:
```
$CI_COMMIT_BRANCH
$CI_COMMIT_SHA
$CI_PROJECT_DIR
$CI_PIPELINE_ID
```
Применение:

```yaml
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t myapp .
    - docker push myapp
```

## Приоритет переменных

Если одно и то же имя:

- job variables
- .gitlab-ci.yml
- project variables
- group variables

Верхний уровень перезапишет нижний

Пример:
```yaml
test:
  variables:
    DEBUG: "false"
  script:
    - echo $DEBUG
```

`DEBUG` перекрывает глобальные переменные с аналогичным именем.
