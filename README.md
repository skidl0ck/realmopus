# RealmOpus

A real estate sales & operations platform - reservation-to-contract-to-installment-payments,
end to end, for a real estate firm still running on spreadsheets and manual paperwork.

**Live demo:** https://main.d28tjv1ja32pvs.amplifyapp.com
Click **"Try the demo - no signup needed"** on the login screen. It logs you straight into a
populated client account (a real contract, a partial payment history, live receipts) - no
account creation needed, and every visitor gets a fresh, reset slate.

**Want the story behind how this got built** - the security audit, a real production race
condition found and fixed, a name change forced by a trademark collision, the actual AWS
deployment - rather than just a feature list? See [`CASE_STUDY.md`](CASE_STUDY.md).

## What it does

- **Public site** - browse available lots across a project, filterable inventory, an AI chat
  widget that answers questions about pricing and the buying process.
- **Client portal** - reserve a lot, pay online (PayPal or local e-wallets via PayMongo),
  track a payment schedule, download receipts and contract PDFs, get notified on upcoming
  due dates.
- **Staff admin panel** - manage projects/lots/clients/contracts, record payments, generate
  reports (aging, cash flow, commissions), role-based permissions, a full audit log.
- **Background processing** - automated late-payment penalties, payment reminders, and
  report generation via Celery.

## Tech stack

**Backend:** Django 5.2 + Django REST Framework, PostgreSQL, Redis (cache + Celery broker),
Celery (background tasks), S3-compatible storage for uploaded/generated files.

**Frontend:** Next.js 16 (App Router) + React 19 + TypeScript, Tailwind CSS, React Query.

**Infrastructure:** AWS - EC2 (backend, behind nginx + gunicorn), RDS (PostgreSQL),
ElastiCache (Redis), S3 (file storage), Amplify Hosting (frontend), with a genuine
Let's Encrypt TLS certificate and HSTS enforced in production.

**CI/CD:** GitHub Actions - automated checks (Django system check, migration-drift
detection, a real production frontend build) on every pull request; a manually-triggered,
access-restricted deploy workflow for the backend, with the frontend auto-deploying via
Amplify on merge to `main`.

## Documentation

- [`CASE_STUDY.md`](CASE_STUDY.md) - the story behind this project, told as a narrative
- [`docs/SETUP.md`](docs/SETUP.md) - running this locally
- [`docs/ENVIRONMENT_VARIABLES.md`](docs/ENVIRONMENT_VARIABLES.md) - every configuration
  value the app reads, what it's for, and whether it's required
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - the full production infrastructure setup,
  as an actual runbook

## A note on security

This project went through a real, methodical security audit - dependency pinning, an
OWASP-2025-mapped review, IDOR/injection/auth testing, STRIDE threat modeling, and an
adversarial "how would an attacker approach this" walkthrough - not just a cursory pass.
Concrete outcomes include rate limiting (verified against real repeated requests), a
payment-double-charge race condition found and fixed (verified against real concurrent
threads on Postgres, not just reasoned about), and scoped IAM credentials throughout
rather than broad or root-level access anywhere in the infrastructure.