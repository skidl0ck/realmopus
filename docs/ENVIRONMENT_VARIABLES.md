# Environment Variables

Every value listed here is read directly from the actual source code (`config('NAME', default=...)`
calls in `backend/config/settings.py`, and `process.env.NEXT_PUBLIC_...` reads in the frontend) -
not from memory, and re-verified while writing this doc after finding a couple of real
blind spots in an earlier, cruder search (variable names containing a digit, and multi-line
declarations, were both silently missed the first time around).

"Default" means what happens if the variable is left unset entirely - many of these are
genuinely optional for local development and only need a real value in production.

## Backend (`backend/.env`)

### Core Django

| Variable | Default | Required in production? | Notes |
|---|---|---|---|
| `SECRET_KEY` | *(none)* | **Yes** | Signs session cookies, CSRF tokens, and password-reset tokens. The app fails to start at all if this is unset and `DEBUG=False` - deliberately, rather than silently falling back to something insecure. Generate one with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. |
| `DEBUG` | `False` | Must be `False` | `True` is for local development only - enables Django's debug error pages (which leak internals) and relaxes several other safety checks. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | **Yes** | Comma-separated list of hostnames Django will accept requests for. The app also refuses to start with `DEBUG=False` if this is still at its localhost-only default. |
| `TRUST_PROXY_HEADERS` | `False` | **Yes**, when behind nginx | Tells Django to trust `X-Forwarded-Proto`/`X-Forwarded-For` from the reverse proxy - needed for correct HTTPS detection and for the IP-based login rate limiter to see the real client IP rather than nginx's. |
| `SECURE_SSL_REDIRECT` | `True` | Set to `False` only until TLS is actually working | Forces HTTP→HTTPS redirects. Enabling this before a TLS certificate exists will break all access to the site. |
| `SECURE_HSTS_SECONDS` | `31536000` (1 year) | Roll out gradually | Same caution as above - HSTS is unusually unforgiving, since a browser that receives this header will refuse plain HTTP for the full duration even if something breaks later. Start low (e.g. `300`) when first enabling HTTPS, confirm it works, then raise it. |

### Database (PostgreSQL in production, SQLite by default)

| Variable | Default | Notes |
|---|---|---|
| `DB_ENGINE` | `django.db.backends.sqlite3` | Set to `django.db.backends.postgresql` in production. |
| `DB_NAME` | a local `db.sqlite3` file | |
| `DB_USER` | *(empty)* | The RDS master username - not the RDS instance identifier, an easy mix-up. |
| `DB_PASSWORD` | *(empty)* | |
| `DB_HOST` | *(empty)* | The RDS endpoint. |
| `DB_PORT` | *(empty)* | `5432` for Postgres. |

### Cache & Celery (Redis)

| Variable | Default | Notes |
|---|---|---|
| `CACHE_URL` | `redis://localhost:6379/1` | Django's cache backend - used for rate-limit counters and the chatbot's own throttle. |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Deliberately a different DB number (`/0`) than `CACHE_URL` (`/1`), keeping Celery's queue and Django's cache logically separated on the same Redis instance. |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` | |
| `CELERY_TIMEZONE` | `Asia/Manila` | |
| `CELERY_TASK_ALWAYS_EAGER` | `False` | `True` runs tasks synchronously inline instead of queuing them - useful for local testing without a running worker, never set this in production. |
| **If using ElastiCache with encryption in transit** | | The scheme changes from `redis://` to `rediss://` (two s's), and the username segment must be explicitly `default` (e.g. `rediss://default:TOKEN@host:6379/0`) - an empty username before the colon is silently treated differently by some Redis clients and gets rejected as invalid credentials, even with the correct token. |

### File storage (S3)

| Variable | Default | Notes |
|---|---|---|
| `AWS_STORAGE_BUCKET_NAME` | *(empty)* | Leaving this unset is what makes the whole S3 integration inactive - the app falls back to local disk storage automatically. Set it to switch over. |
| `AWS_ACCESS_KEY_ID` | *(empty)* | Only read at all if `AWS_STORAGE_BUCKET_NAME` is set. Use a scoped IAM user limited to this one bucket - never root account keys. |
| `AWS_SECRET_ACCESS_KEY` | *(empty)* | |
| `AWS_S3_REGION_NAME` | `us-east-1` | Must match the bucket's actual region. |
| `AWS_QUERYSTRING_EXPIRE` | `3600` (1 hour) | How long a generated presigned file URL stays valid before expiring. |

### CORS

| Variable | Default | Notes |
|---|---|---|
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated list of frontend origins allowed to call the API cross-origin. Must include the real frontend's production URL (Amplify domain and/or custom domain) once deployed. |

### Payment gateways

| Variable | Default | Notes |
|---|---|---|
| `PAYPAL_CLIENT_ID` | *(empty)* | |
| `PAYPAL_CLIENT_SECRET` | *(empty)* | |
| `PAYPAL_MODE` | `sandbox` | `sandbox` or `live`. |
| `PAYMONGO_SECRET_KEY` | *(empty)* | Server-side only - never expose this one to the frontend. |
| `PAYMONGO_PUBLIC_KEY` | *(empty)* | Safe to expose publicly by design - also needs setting as `NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY` on the frontend (see below), since card/e-wallet payment attachment happens directly from the browser to PayMongo's API. |
| `PAYMONGO_WEBHOOK_SECRET` | *(empty)* | Optional - safe to leave unset if not using PayMongo webhooks. |

### AI chatbot

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | |
| `GEMINI_CHAT_MODEL` | `gemini-3.6-flash` | |

### Email

| Variable | Default | Notes |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | The console backend just prints emails to the server log instead of sending them - a safe default until a real SMTP provider (SES, SendGrid, Gmail app password, etc.) is configured. |
| `EMAIL_HOST` | *(empty)* | |
| `EMAIL_PORT` | `587` | |
| `EMAIL_HOST_USER` | *(empty)* | |
| `EMAIL_HOST_PASSWORD` | *(empty)* | |
| `EMAIL_USE_TLS` | `True` | |
| `DEFAULT_FROM_EMAIL` | `noreply@realmopus.local` | |

## Frontend (`frontend/.env.local`, and as Amplify environment variables in production)

| Variable | Required? | Notes |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | **Yes** | The backend's base API URL (e.g. `https://api.realmopus.online/api`). |
| `NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY` | **Yes**, for GCash/Maya/card payments to work | Card/e-wallet attachment happens directly from the browser to PayMongo, bypassing the backend entirely - this key has to be present at build time, since Next.js inlines `NEXT_PUBLIC_` variables into the compiled JavaScript bundle. Adding or changing this value requires triggering a new Amplify build, not just updating the setting. |
| `NEXT_PUBLIC_DEMO_CLIENT_USERNAME` | No | Overrides the demo login button's username, if the backend's demo account was ever seeded with something other than the default. |
| `NEXT_PUBLIC_DEMO_CLIENT_PASSWORD` | No | Same, for the password - must be changed together with the backend's `seed_demo_accounts` command if the demo password is ever rotated, or the one-click demo button silently breaks. |
