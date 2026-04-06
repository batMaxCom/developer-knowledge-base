# Deploy

Стратегия:
```yaml
test → build image → push image → deploy to staging → verify → deploy to production
```

Что происходит:

- сначала проверяем код;
- потом собираем immutable artifact — обычно Docker image;
- потом деплоим один и тот же образ в разные окружения.

Это важный принцип: `не пересобирать` заново на production, а выкатывать уже проверенный артефакт.

# Environments в GitLab

GitLab рекомендует описывать окружения через environment, чтобы видеть историю деплоев и текущее состояние окружений.

```yaml
deploy_staging:
  stage: deploy
  script:
    - ./deploy.sh staging
  environment:
    name: staging
    url: https://staging.example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "develop"'

deploy_prod:
  stage: deploy
  script:
    - ./deploy.sh production
  environment:
    name: production
    url: https://example.com
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual
```