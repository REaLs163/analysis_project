# Разметка PDF-файлов анализов с отклонениями при помощи Yandex Cloud Functions и Object Storage
При помощи объектного хранилища, триггера и функции можно легко определять отклонения в анализах людей.

# ⚙️ Настройка и запуск

1. Клонируй репозиторий на локальную машину:
```bash
git clone <repository_url>
```
2. Зарегистрируйте аккаунт в Yandex Cloud по инструкции ниже:
```text
https://yandex.cloud/ru/docs/billing/quickstart/
```
3. Создайте бакет по инструкции ниже:
```text
https://yandex.cloud/ru/docs/storage/operations/buckets/create
```

4. Создайте версию функции и поместите файлы из репозитория в редактор функции.
```text
Подробнее об этом можно прочитать в документации: https://yandex.cloud/ru/docs/functions/operations/function/version-manage
```

5. Создайте триггер функции для Object Storage.
```text
Подробнее об этом в документации: https://yandex.cloud/ru/docs/functions/operations/trigger/os-trigger-create
```

6. Создайте необходимые переменные окружения:
```env
AWS_ACCESS_KEY_ID=KEY_ID
AWS_SECRET_ACCESS_KEY=ACCESS_KEY
AWS_REGION=ru-central1
S3_ENDPOINT=https://storage.yandexcloud.net   
S3_BUCKET=BUCKET_NAME
INPUT_PREFIX=input/
OUTPUT_PREFIX=output/
```

# Требования к функции

- Python 3.12+
- Таймер 5 сек.
- Объём памяти 384 МБ.