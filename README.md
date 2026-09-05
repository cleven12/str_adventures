# Structured Adventures

Backend service for Structured Adventures.

## Stack

- Django
- Django REST Framework
- MySQL (SQLite for local dev)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docker

```bash
docker compose up --build
```

## Notes

- API is served under `/api/v1/`.
- Admin panel is at `/admin/`.
- A separate frontend application consumes this API.
