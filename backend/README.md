# Coderr — Backend (Django + DRF)

Coderr is a Fiverr-like service marketplace where business users publish tiered offers (basic / standard / premium) and customers can place orders, leave reviews, and browse the public catalogue. This repository contains the **backend only** — a Django REST Framework API consumed by a separate static frontend.

## Stack

- Python 3.13 or 3.14
- Django 6.0
- Django REST Framework 3.17
- Token authentication
- SQLite (development)
- django-filter, django-cors-headers, Pillow

## Quickstart

Copy-paste block for a runnable instance in under a minute, including
realistic demo data:

```bash
git clone https://github.com/tranqn/coderr.git
cd coderr/backend
python -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser      # optional — admin user for /admin/
python manage.py seed_demo_data       # optional — fills the DB with demo content
python manage.py runserver
```

**Demo logins** (after running `seed_demo_data`). Password for every
demo account is `demo-pw-12345`.

| Role     | Usernames                                       |
|----------|-------------------------------------------------|
| Business | `b_designer`, `b_developer`, `b_translator`, `b_copywriter` |
| Customer | `c_anna`, `c_ben`, `c_clara`, `c_dario`         |

The full demo blueprint is in
`base_info_app/management/commands/seed_demo_data.py`.

To wipe and reseed: `python manage.py seed_demo_data --reset`.

## Setup (manual / production-style)

```bash
cd backend
python -m venv env
source env/bin/activate            # Windows: env\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # then edit DJANGO_SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is reachable at `http://127.0.0.1:8000/api/`, the admin at `http://127.0.0.1:8000/admin/`.

## Running the frontend

The static frontend lives at `../frontend/`. From a second terminal:

```bash
cd ../frontend
python -m http.server 5500
```

Then open `http://127.0.0.1:5500/`. CORS is enabled for development.

## API endpoints

| Method               | Path                                             | Notes                                                                                                                     |
| -------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| POST                 | `/api/registration/`                             | Public; returns `{token, username, email, user_id}`                                                                       |
| POST                 | `/api/login/`                                    | Public                                                                                                                    |
| GET / PATCH          | `/api/profile/{user_id}/`                        | PATCH: owner only                                                                                                         |
| GET                  | `/api/profiles/business/`                        | Authenticated                                                                                                             |
| GET                  | `/api/profiles/customer/`                        | Authenticated                                                                                                             |
| GET / POST           | `/api/offers/`                                   | GET: public; POST: `business` profile only; supports `creator_id`, `min_price`, `max_delivery_time`, `ordering`, `search`, `page_size` |
| GET / PATCH / DELETE | `/api/offers/{id}/`                              | GET: public; PATCH/DELETE: creator only                                                                                   |
| GET                  | `/api/offerdetails/{id}/`                        | Public                                                                                                                    |
| GET / POST           | `/api/orders/`                                   | POST: `customer` profile only                                                                                             |
| PATCH                | `/api/orders/{id}/`                              | Business user of the order only                                                                                           |
| DELETE               | `/api/orders/{id}/`                              | Staff (admin) only                                                                                                        |
| GET                  | `/api/order-count/{business_user_id}/`           | Counts `in_progress` orders                                                                                               |
| GET                  | `/api/completed-order-count/{business_user_id}/` | Counts `completed` orders                                                                                                 |
| GET / POST           | `/api/reviews/`                                  | POST: `customer` profile only; one review per (business_user, reviewer)                                                   |
| PATCH / DELETE       | `/api/reviews/{id}/`                             | Author only; PATCH limited to `rating`, `description`                                                                     |
| GET                  | `/api/base-info/`                                | Public; aggregated stats                                                                                                  |

## Notable behaviour

- **Empty-string convention**: profile responses never return `null` for `first_name`, `last_name`, `location`, `tel`, `description`, `working_hours`, or `file` — empty values are returned as `""`.
- **Offer PATCH**: nested details are matched by `offer_type`, not by `id`. Existing detail IDs remain stable across updates.
- **Snapshot orders**: an order copies title, revisions, delivery time, price, features, and offer_type from the source `OfferDetail` at creation time. Subsequent edits to the offer do not change historical orders.
- **Pagination**: `/api/offers/` uses page-number pagination with a default of 6 items per page; the frontend's `PAGE_SIZE` constant matches.

## Authentication

Send `Authorization: Token <key>` on every authenticated request. Tokens are returned by `/api/registration/` and `/api/login/`.

## Tests & coverage

Two runners are supported — pick either, the tests are identical.

```bash
# Django built-in runner
python manage.py test

# pytest (via pytest-django, see pytest.ini)
pytest
```

With coverage:

```bash
coverage run --source=auth_app,profile_app,offer_app,order_app,review_app,base_info_app manage.py test
coverage report -m
```

Coverage target: ≥ 95 %.
