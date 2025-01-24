## Запуск docker-контейнера

1. Сборка образа (из корневой папки, где лежит Dockerfile):
```bash
docker build -t finance-bot .
```

2. Запуск контейнера:
```bash
docker run -d --name my_finance_bot \
    -e BOT_TOKEN="ваш_реальный_токен" \
    finance-bot
```
Тут: \
``-d`` — запускаем в фоновом режиме. \
``--name my_finance_bot`` — даём контейнеру имя. \
`-e BOT_TOKEN="..."` — задаём переменную окружения.
