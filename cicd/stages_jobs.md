# Stages - линейный порядок этапов

```yaml
stages:
  - lint
  - test
  - build
  - deploy
```

Слеледующий этап не может начаться, пока предыдущий не завершился.

# Jobs - параллельные этапы
Прмиер:
```yaml
lint_backend:
  stage: lint
  script:
    - ruff check .

lint_frontend:
  stage: lint
  script:
    - npm run lint
```

Что происходит:
- выполняются параллельно
- в рамках одного stage
- если один job завершился с ошибкой, то stage считается неуспешным, процесс сборки прерывается

Можно обойти проблему с параллельными job-ами, используя `needs`:
```yaml
build_a:
  stage: build

build_b:
  stage: build

deploy:
  stage: deploy
  needs: ["build_a"]
```
Что происходит:
- deploy стартует сразу после build_a
- не ждёт build_b

В случае с needs, для ускорения процесса можно использовать артефакты

```yaml
build:
  stage: build
  script:
    - mkdir dist
    - echo "app" > dist/app.txt
  artifacts: # сохраняем артефакты
    paths:
      - dist/

deploy:
  stage: deploy
  needs: ["build"]
  script:
    - cat dist/app.txt
```