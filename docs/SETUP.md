# Local Development Setup

## Prerequisites

- Python 3.12+
- Node.js 20+
- Redis (used for the cache, rate limiting, and as Celery's broker - needed even for local
  development, not just production). The simplest way to get one running locally:
  ```
  docker run -d --name redis -p 6379:6379 redis
  ```
  If you don't have Docker, install it from docker.com, or run `redis-server` directly if
  you have it installed natively.

You do **not** need PostgreSQL, AWS credentials, or real payment gateway keys for local
development - the app falls back to SQLite and local disk storage automatically when those
aren't configured (see [`ENVIRONMENT_VARIABLES.md`](ENVIRONMENT_VARIABLES.md) for exactly
which variables are optional).

## Backend

```
cd backend
python3 -m venv venv
```

Activate it - on Mac/Linux: `source venv/bin/activate`. On Windows (PowerShell):
`venv\Scripts\Activate.ps1`.

```
pip install --upgrade pip
pip install -r requirements.txt
```

Create `backend/.env`:

```
DEBUG=True
SECRET_KEY=dev-only-key-change-me
```

That's genuinely enough to start - `DB_ENGINE` defaults to SQLite and `CACHE_URL`/
`CELERY_BROKER_URL` default to `localhost:6379`, matching the Redis container above. Add
any of the other variables from `ENVIRONMENT_VARIABLES.md` only if you're testing the
specific feature they enable (S3 uploads, real payment gateways, the AI chatbot).

```
python manage.py migrate
python manage.py seed_demo_accounts
python manage.py createsuperuser
python manage.py runserver
```

`seed_demo_accounts` creates the shared demo client/staff logins with a pre-populated
sample contract - safe to re-run anytime, and not required if you only need your own
superuser account.

The API is now running at `http://localhost:8000`.

### Optional: running Celery for real

By default, background tasks (payment reminders, late-penalty calculation) don't run
unless a worker is actually listening. For most local development this doesn't matter -
but if you're specifically working on a Celery task, open two more terminals (with the
venv activated in each):

```
celery -A config worker --loglevel=info
celery -A config beat --loglevel=info
```

## Frontend

```
cd frontend
npm install
```

Create `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Add `NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY` too if you're testing the GCash/Maya/card payment
flow specifically - it needs a real PayMongo sandbox public key to work at all.

```
npm run dev
```

The site is now running at `http://localhost:3000`.

## Trying it out

- Public site: `http://localhost:3000`
- Client portal: click "Client login" → "Try the demo - no signup needed" for a
  pre-populated account, or log in with the superuser you created
- Staff admin panel: `http://localhost:8000/admin_panel/login/`, using the superuser
  account (not the demo accounts - those are deliberately restricted to their own roles)
