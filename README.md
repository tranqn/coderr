# Coderr

> Fiverr-style service marketplace — Django REST backend + Vanilla JS frontend.

## Repository structure

| Path        | Purpose                                  | README                                 |
|-------------|------------------------------------------|----------------------------------------|
| `backend/`  | Django + DRF API, SQLite, token auth     | [`backend/README.md`](./backend/README.md)   |
| `frontend/` | Static HTML / CSS / JS, JSDoc            | [`frontend/README.md`](./frontend/README.md) |

## Quickstart

```bash
git clone https://github.com/tranqn/coderr.git
cd coderr/backend
python -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser    # optional — admin user for /admin/
python manage.py seed_demo_data     # optional — demo data
python manage.py runserver
```

In a second terminal:

```bash
cd ../frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500/`.

## Demo logins

After running `seed_demo_data`. Password for every demo account: `demo-pw-12345`.

| Role     | Usernames                                                       |
|----------|-----------------------------------------------------------------|
| Business | `b_designer`, `b_developer`, `b_translator`, `b_copywriter`     |
| Customer | `c_anna`, `c_ben`, `c_clara`, `c_dario`                         |

## Tests

```bash
cd backend
python manage.py test     # Django built-in runner
pytest                    # alternative via pytest-django
```

Coverage target: ≥ 95 %. See [`backend/README.md`](./backend/README.md) for the full coverage command.

## Tech stack

Python 3.13 / 3.14 · Django 6.0 · Django REST Framework 3.17 · SQLite · django-filter · Pillow · Vanilla JavaScript

## License

All rights reserved unless a `LICENSE` file says otherwise.
