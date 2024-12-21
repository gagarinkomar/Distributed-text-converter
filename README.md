# Распределенный обработчик картинок
Над Проектом работали
- **Комаров Иван** — gagarinkomar
- **Скворцов Алексей** — rattysed
- **Куков Жирилл** — llirikh


## Инструкция по запуску проекта

Вместо `example.com` ваш домен

```bash
git clone https://github.com/gagarinkomar/distributed-text-converter.git
cd distributed-text-converter

sudo certbot certonly --standalone -d example.com
sed -i 's/yourdomain\.com/example.com/g' nginx/nginx.conf

cp .env.example .env
```

Настраиваете переменные в .env

```
docker compose up --build -d
```

Если хотите запускать без https:

```
cp nginx/nginx.conf.http_only nginx/nginx.conf
```

## Сценарий использования
- Пользователь заходит на сайт, чтобы добавить вотермарку.
- Загружает одну или несколько картинок в форму.
- Система редиректит на страницу ожидания завершения задачи с уникальным uuid.
- После того, как задача завершится, на странице 
появляется ссылка для скачивания архива с результатом. Ссылка будет жить 1 час.
- Через час после завершения задачи все файлы будут удалены

## Пособие для администратора
Можно расширить функционал сервиса.

В `backend/requests/image_tasking.py` есть абстрактный класс,
наследуясь от которого и дополняя метод edit можно создавать задачи обработки картинки, подходящие для приложения

Пример с вотермаркой находится в `backend/requests/custom_image_handler.py`

## Архитектура

- Использованные технологии:
  - Django
  - S3 (Minio)
  - Postgres
  - Celery
  - Redis
- Загруженные пользователем файлы обрабатываются параллельно с помощью Celery.
Любое количество воркеров (в примере их 2) подключаются по http к Redis и получают команды от контроллера
- Синхронизация состояний производится засчёт Postgres
- Файлы синхронизируются засчёт S3
- Система масштабируема на любое число воркеров. Воркеры могут быть запущенны на хостах
независимо от контроллера