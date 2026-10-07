# Agro Scoring API

REST API на FastAPI для оценки риска сельскохозяйственных предприятий.
Прогнозы хранятся в памяти и удаляются после перезапуска приложения.

## Структура проекта

- `main.py` — приложение, endpoints, middleware и логирование.
- `schemas.py` — Pydantic-модели запросов и ответов.
- `model.py` — расчёт риска.
- `services.py` — проверка региона, уровень риска и рекомендации.
- `storage.py` — временное хранилище прогнозов.
- `requirements.txt` — зависимости.
- `.gitignore` — исключения для Git.
- `README.md` — инструкция запуска.

## Установка

Открой терминал в папке с `main.py` и создай виртуальное окружение:

```bash
python -m venv venv
```

Активируй окружение в Windows (cmd):

```bat
venv\Scripts\activate
```

Установи зависимости:

```bash
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn main:app --reload
```

Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Endpoints

- `GET /health`
- `GET /model-info`
- `POST /predict`
- `GET /predictions`
- `GET /predictions/{request_id}`
