# Deployment Runbook

This is the real, complete production setup - AWS EC2 (backend), RDS (database),
ElastiCache (Redis), S3 (file storage), and Amplify Hosting (frontend). It's written as an
actionable reference for rebuilding this infrastructure, not a general AWS tutorial - it
includes the specific gotchas that actually came up, since those are exactly the kind of
thing worth not rediscovering the hard way a second time.

## Architecture

```
                                    ┌─────────────┐
Browser ──HTTPS──▶ Amplify Hosting  │  Next.js SSR │
   │                                └──────┬───────┘
   │                                       │ HTTPS (CORS)
   ▼                                       ▼
Browser ──HTTPS──▶ nginx ──▶ gunicorn ──▶ Django ──┬──▶ RDS (Postgres)
              (EC2, Let's                          ├──▶ ElastiCache (Redis)
               Encrypt TLS)                         └──▶ S3 (files)
                    │
                    └──▶ Celery worker + beat (same EC2 instance, systemd services)
```

## 1. RDS (PostgreSQL)

Console → RDS → Create database → **PostgreSQL**, **Full configuration** (not Express -
Express makes networking decisions for you, including public accessibility on some engine
choices, which is the opposite of what's needed here).

- Template: Free tier (or Production for Multi-AZ, at extra cost)
- Instance: `db.t3.micro` / `db.t4g.micro`
- **Public access: No** - the database should only ever be reachable from the EC2 instance,
  never directly from the internet
- Create a new security group for it now; its inbound rule gets locked down to the EC2
  instance's own security group once that exists (step 3)

## 2. ElastiCache (Redis)

Console → ElastiCache → Create → **Redis OSS**, **Design your own cache** (not Serverless -
provisioned nodes are free-tier eligible for 12 months, Serverless isn't).

- Cluster mode: **Disabled** (this app doesn't need sharding, and disabled mode keeps the
  connection string simple)
- Node type: `cache.t3.micro` / `cache.t4g.micro`, 0 replicas
- Same VPC as RDS/EC2, new security group (locked down in step 3)
- **Encryption in transit: On**, with an **AUTH token** enabled

  > **Gotcha:** with encryption in transit on, the connection scheme changes from `redis://`
  > to `rediss://`. More importantly: the username segment in the URL must be **explicitly
  > `default`**, not left blank. `rediss://:TOKEN@host:6379` (empty username before the
  > colon) gets rejected as invalid credentials by some Redis clients even with the
  > completely correct token - it has to be `rediss://default:TOKEN@host:6379`.
  >
  > **Gotcha:** if the AUTH token itself contains characters like `@`, `:`, or `/`, it needs
  > URL-encoding before being embedded in the connection string, or the URL parser
  > misreads where the password ends and the host begins. In Python:
  > `python -c "from urllib.parse import quote; print(quote('TOKEN', safe=''))"`

## 3. EC2

Launch an instance: Ubuntu 24.04 LTS, `t3.small` recommended (`t3.micro` is free-tier
eligible but genuinely tight running gunicorn + Celery worker + Celery beat + nginx
together - memory exhaustion tends to show up as confusing crashes, not a clear error).

Security group:
- SSH (22) - restrict to your own IP for interactive access. **Note:** if using GitHub
  Actions for automated deploys later, this will need broadening (see the CI/CD section) -
  GitHub's runners don't have a fixed IP to allowlist individually.
- HTTP (80) - anywhere, needed for Let's Encrypt validation and the HTTPS redirect
- HTTPS (443) - anywhere

Once the instance exists, go back to RDS's and ElastiCache's security groups and set their
inbound rules to reference the EC2 security group specifically, not an IP range - removing
any broader rule used to create them.

20GB gp3 storage is comfortable headroom.

## 4. Server setup

SSH in, then:

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip git nginx libpq-dev build-essential postgresql-client redis-tools
```

Clone the repo (a GitHub deploy key, scoped read-only to this one repo, if private -
`ssh-keygen -t ed25519`, add the public half under the repo's Settings → Deploy keys),
then set up the Python environment:

```
cd ~/realmopus/backend
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

Create `.env` with the production values - see `ENVIRONMENT_VARIABLES.md`. A few
production-specific notes:
- `SECURE_SSL_REDIRECT=False` and `SECURE_HSTS_SECONDS=0` **until TLS is actually working**
  (section 6) - enabling either one first will break all access to the site, since there's
  no HTTPS listener yet to redirect to.
- `ALLOWED_HOSTS` and `DJANGO_ALLOWED_HOSTS` should include both the EC2 public IP and,
  once available, the real domain.

```
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py seed_demo_accounts
python manage.py createsuperuser
```

### gunicorn (systemd service, `/etc/systemd/system/gunicorn.service`)

```ini
[Unit]
Description=RealmOpus gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/home/ubuntu/realmopus/backend
ExecStart=/home/ubuntu/realmopus/backend/venv/bin/gunicorn --workers 3 --umask 007 --bind unix:/run/gunicorn/gunicorn.sock config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

> **Gotcha:** the socket binds inside `/run/gunicorn/` (via `RuntimeDirectory=gunicorn`),
> not inside the home directory. Binding it under `/home/ubuntu/` causes nginx (which runs
> as a different user, `www-data`) to get a **502 Bad Gateway** - it can't get through the
> home directory's own permissions to reach the socket at all, regardless of the socket
> file's own permissions. `RuntimeDirectory` + `Group=www-data` + `--umask 007` together
> are what make the socket actually shared correctly between the two users.

### Celery worker + beat (same pattern, separate services)

`/etc/systemd/system/celery-worker.service` and `celery-beat.service`, both identical to
the gunicorn service above except `WorkingDirectory`/`User`/`Group` the same, and:
```
ExecStart=/home/ubuntu/realmopus/backend/venv/bin/celery -A config worker --loglevel=info
```
(swap `worker` for `beat` in the second file).

```
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn celery-worker celery-beat
```

### nginx (`/etc/nginx/sites-available/realmopus`)

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    client_max_body_size 20M;

    location /static/ {
        alias /home/ubuntu/realmopus/backend/staticfiles/;
    }

    location / {
        proxy_pass http://unix:/run/gunicorn/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

No `/media/` location block - user-uploaded and generated files (photos, contract PDFs,
receipts) go straight to S3 and are served via presigned URLs, never through nginx.

```
sudo rm /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/realmopus /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

## 5. TLS (Let's Encrypt via Certbot)

Requires a real domain pointed at the EC2 instance's IP first (an A record).

```
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your.domain.com
```

Certbot updates the nginx config's `server_name` to the domain and adds the HTTPS server
block automatically. Afterward:

1. Update `.env`: `ALLOWED_HOSTS`/`DJANGO_ALLOWED_HOSTS` to include the domain,
   `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS` - raise this gradually (e.g. `300`
   first, confirm it works, then step up toward the full `31536000` over subsequent
   deploys - HSTS is unusually unforgiving about being wrong).
2. `sudo systemctl restart gunicorn`

## 6. S3

Create a bucket (General purpose, Block all public access **on** - everything is served
via presigned URLs, nothing is ever meant to be public). Create a dedicated IAM user with
a policy scoped to only that one bucket (`s3:GetObject`/`PutObject`/`DeleteObject` on
`bucket/*`, `s3:ListBucket` on the bucket itself) - never use root account keys. Set the
four `AWS_*` variables in `.env` (see `ENVIRONMENT_VARIABLES.md`).

## 7. Amplify (frontend)

Console → Amplify Hosting → connect the GitHub repo → **check "Monorepo"**, set the app
root to `frontend`. This is important: without it, Amplify tries to build the entire
monorepo as one Next.js app, including the unrelated Django code, and fails outright. With
it set correctly, the auto-detected build command/output directory should already be
correctly scoped (`.next`, not `frontend/.next`).

Environment variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY`.

Amplify auto-deploys on every push to `main` - no separate CI/CD setup needed for the
frontend specifically.

## 8. CI/CD (backend)

The frontend deploys automatically via Amplify. The backend deploy is deliberately
**manual-trigger-only** (`workflow_dispatch`), given it runs real database migrations -
see `.github/workflows/deploy-backend.yml`.

It works via a **forced-command SSH key**: a dedicated key pair whose `authorized_keys`
entry restricts it to running exactly one script (`~/deploy.sh`) regardless of what command
is actually sent, with `no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty`
closing off everything else an SSH session could otherwise do. Even a fully compromised
copy of this specific key could only ever trigger that one deployment, nothing broader.

```
# ~/deploy.sh on the server
#!/bin/bash
set -e
cd /home/ubuntu/realmopus/backend
git pull
venv/bin/pip install -r requirements.txt
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

The matching `sudo` permission for the three restart commands needs to be passwordless
(`NOPASSWD`) but scoped to exactly those three commands - never a blanket passwordless
`sudo`.

GitHub secrets needed: `EC2_SSH_PRIVATE_KEY` (the forced-command key's private half),
`EC2_HOST`, `EC2_USER`.

> **Gotcha:** GitHub Actions runners execute on GitHub's own infrastructure with
> constantly-changing IP addresses - never your own. If SSH is restricted to "my IP only"
> (the correct default for your own interactive access), the automated deploy will fail
> with a network-level connection error, not an authentication one. The two real fixes are
> broadening port 22 (justifiable here specifically because the forced-command restriction
> above already contains the actual risk) or migrating to AWS Systems Manager Session
> Manager, which needs no open SSH port at all. If broadening the port, consider adding a
> passphrase to any other, less-restricted personal key that also has access to the
> server - `ssh-keygen -p -f your-key.pem` - since an open port removes IP-based
> protection as a safety net for that key too, not just the new automated one.

## CI checks (every pull request)

`.github/workflows/ci.yml` runs on every PR: a Django system check and a
missing-migrations check for the backend (no real database needed - `DEBUG=True` alone is
enough, since that's what the app's own fail-loud `SECRET_KEY`/`ALLOWED_HOSTS` checks key
off, and `DB_ENGINE` defaults to SQLite), plus a real `npm ci` + `npm run build` for the
frontend - deliberately the same strict `npm ci` Amplify itself uses, so a `package.json`/
`package-lock.json` drift gets caught on every PR rather than only when an actual deploy is
attempted.

> **Gotcha:** a migration file can exist locally and even be applied to the actual
> production database, while never having been pushed to GitHub at all - nothing catches
> this until a `makemigrations --check --dry-run` genuinely runs against a clean checkout.
> Worth spot-checking after any batch of local model changes: `git log --all --oneline --
> path/to/migration.py` returning nothing means it was never actually committed anywhere.
