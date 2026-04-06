# Docker в GitLab CI

Цель:
- собрать Docker image
- запушить в registry
- задеплоить

Где происходит:
- внутри runner

## Есть 2 варианта:

1. Docker-in-Docker (DinD)
```yaml
services:
  - docker:dind
```
Что происходит:
внутри контейнера запускается Docker daemon

2. Docker socket (production чаще)
```yaml
/var/run/docker.sock
```
Что происходит:
- runner использует Docker хоста

## Пример
```yaml
Docker pipeline
image: docker:latest

services:
  - docker:dind

variables:
  DOCKER_TLS_CERTDIR: ""

build:
  script:
    - docker build -t myapp .
    
```

Почему `DOCKER_TLS_CERTDIR=""`:
- отключает TLS
- иначе docker client не сможет подключиться к dind

# Registry

GitLab даёт встроенный registry

Встроенные переменные:
```yaml
$CI_REGISTRY
$CI_REGISTRY_USER
$CI_REGISTRY_PASSWORD
```
## Логин

```yaml
script:
  - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
```
## Сборка и push
```yaml
build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:latest .
    - docker push $CI_REGISTRY_IMAGE:latest
```

Для автоматического присвоения:
`$CI_REGISTRY_IMAGE` = `registry.gitlab.com/username/project`

## Тэги образов
Пример:
```yaml
- docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
```
Лучший вариант:
```yaml
- docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .
- docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA $CI_REGISTRY_IMAGE:latest
```
```yaml
image: docker:latest

services:
  - docker:dind

variables:
  DOCKER_TLS_CERTDIR: ""

stages:
  - build
  - push

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA .

push:
  stage: push
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
```

## Ускорение (Docker layer caching) 
```yaml
- docker build --cache-from=$CI_REGISTRY_IMAGE:latest -t ...
```

## Пример деплоя

```yaml
deploy:
  stage: deploy
  script:
    - ssh user@server "
        docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA &&
        docker stop app || true &&
        docker run -d --name app $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
      "
```