# Coderr

> Fiverr-style service marketplace — Django REST backend + Vanilla JS frontend.

## Repository structure

| Path        | Purpose                                  | README                                 |
|-------------|------------------------------------------|----------------------------------------|
| `backend/`  | Django + DRF API, SQLite, token auth     | [`backend/README.md`](./backend/README.md)   |
| `frontend/` | Static HTML / CSS / JS, JSDoc            | [`frontend/README.md`](./frontend/README.md) |

The `frontend/` directory is taken from the Developer Akademie reference template at [Developer-Akademie-Backendkurs/project.Coderr](https://github.com/Developer-Akademie-Backendkurs/project.Coderr/blob/main/README.md) and is consumed as-is. All backend code in this repository is original.

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

## Docker deployment

The whole app ships as a **single image**: nginx serves the frontend and
reverse-proxies the API to Gunicorn inside the same container. Everything lives
behind one origin, so the image runs unchanged on **Linux, Windows and macOS**
servers — the only requirement is Docker.

### Build and run

```bash
cd coderr
docker build -t coderr .
docker run -d -p 8080:80 \
  -e DJANGO_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(64))')" \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS="*" \
  -v coderr-data:/app/data \
  --name coderr coderr
```

Prefer a file over inline `-e` flags? Copy `.env.example` to `.env`, edit it,
and pass `--env-file .env` instead.

Open `http://localhost:8080/` — admin at `http://localhost:8080/admin/`.
On a remote server use the host's address (e.g. `http://<server-ip>:8080/`)
and make sure `DJANGO_ALLOWED_HOSTS` covers that host.

### Configuration

| Variable                      | Purpose                                                        |
|-------------------------------|----------------------------------------------------------------|
| `DJANGO_SECRET_KEY`           | **Required.** Long random string.                              |
| `DJANGO_DEBUG`                | Keep `False` for any public deployment.                        |
| `DJANGO_ALLOWED_HOSTS`        | Hosts allowed to serve the app (`*` for a quick trial).        |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Needed for admin login over HTTPS, e.g. `https://coderr.example.com`. |
| `DJANGO_SECURE_SSL`           | `True` once TLS terminates in front: forces HTTPS redirect, HSTS, secure cookies. Leave `False` for plain HTTP. |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Cross-origin browser origins allowed to call the API (only with `DEBUG=False`; same-origin needs none). |
| `SEED_DEMO_DATA`              | `1` to load demo data on first start.                          |

The SQLite database and uploaded media persist in the `/app/data` volume.
Migrations and `collectstatic` run automatically on container start. Gunicorn
runs as an unprivileged user inside the container, and a `HEALTHCHECK` polls
`/api/base-info/`.

> **Production note:** without a `DJANGO_SECRET_KEY` the app refuses to start
> when `DEBUG=False`. For a public deployment put a TLS proxy (Caddy, nginx,
> Cloudflare) in front and set `DJANGO_SECURE_SSL=True`. SQLite suits this
> single-container quick run; for real production use the HTTPS + PostgreSQL
> stack below.

### Manage

```bash
docker logs -f coderr                                       # follow logs
docker exec -it coderr python manage.py createsuperuser     # admin user
docker exec -it coderr python manage.py seed_demo_data --reset
docker rm -f coderr                                         # stop and remove
```

The data volume survives `docker rm`; delete it with `docker volume rm coderr-data`.

### Production stack with HTTPS + PostgreSQL

For a public deployment, `compose.prod.yml` runs three services:
[Caddy](https://caddyserver.com/) (automatic TLS) → the Coderr app →
**PostgreSQL**. Caddy obtains and renews a Let's Encrypt certificate for your
domain, Django's HTTPS hardening (`DJANGO_SECURE_SSL=True`) is switched on, and
setting `POSTGRES_DB` makes the backend use Postgres instead of SQLite.

```bash
cp .env.example .env
# set DJANGO_SECRET_KEY, SITE_ADDRESS=<your-domain>,
#     DJANGO_ALLOWED_HOSTS=<your-domain>,
#     DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-domain>,
#     POSTGRES_PASSWORD=<strong-password>
docker compose -f compose.prod.yml up -d --build
```

Point the domain's DNS at the server first, and open ports 80 and 443. The app
is then reachable at `https://<your-domain>/`. For a quick local test set
`SITE_ADDRESS=localhost` (Caddy issues a self-signed cert). Management commands
target the `coderr` service, e.g.
`docker compose -f compose.prod.yml exec coderr python manage.py createsuperuser`.
Database and media persist in the `pg-data` and `coderr-data` volumes.

A full walkthrough for deploying this stack on a Google Cloud VM (free
`e2-micro` tier, automatic HTTPS) is in
[`docs/gcp-deployment.md`](./docs/gcp-deployment.md).

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
