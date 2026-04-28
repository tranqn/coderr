# Coderr Backend

A Django REST Framework backend for the Coderr marketplace.

> **Status:** work in progress. The full setup and endpoint
> documentation will land on the final day of the build.

## Quickstart (dev)

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is mounted under `/api/`.
