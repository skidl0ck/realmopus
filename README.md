# Greenview Estates — Real Estate Sales & Property Management Platform

A full-stack real estate sales management system: lot inventory, reservations,
installment contracts with amortization + penalties, online payments (PayPal +
PH e-wallet), sales agent commissions, expense tracking, and a cash flow
dashboard. Stack mirrors the Sikaty platform.

## Stack

- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, React Query, Zustand
- **Backend:** Django REST Framework, SimpleJWT auth, django-cors-headers
- **Database:** SQLite locally, Postgres (RDS free tier) in production
- **Payments:** PayPal + PayMongo (GCash/Maya/cards) — sandbox keys for demo
- **Deployment target:** AWS free tier (EC2/Elastic Beanstalk + RDS + S3/CloudFront)

## Roles

Admin · Sales Agent · Accountant/Finance · Client (portal)

## Project structure

```
backend/
  accounts/     custom User model, roles, agent/client profiles, audit log
  properties/   Project, Lot, Reservation
  sales/        Contract, Fee, Installment, Commission, amortization engine
  payments/     Payment, Receipt
  expenses/     Expense, ExpenseCategory
  core/         Notification, shared concerns
frontend/
  src/app/(public)/       marketing site + public lot browsing
  src/app/(dashboard)/    admin / agent / accountant views
  src/app/(client-portal)/ client-facing portal
  src/lib/                API client, React Query provider, auth store
  src/types/              shared TypeScript types
```

## Local setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Core business logic

`sales/services.py` contains:
- `generate_amortization_schedule(contract)` — builds fixed monthly installments
  from down payment, term, flat annual interest, and recurring fees.
- `apply_late_penalties(as_of=None)` — meant to run daily (cron or Celery beat),
  applies each contract's penalty rate to overdue installment balances.

## Roadmap

1. ✅ Repo scaffold + core Django models
2. Admin & inventory management (project/lot CRUD, role permissions)
3. ✅ Contracts & amortization engine
4. Payments module (manual + PayPal/PayMongo integration)
5. Client portal (browse lots, view schedule, pay online)
6. Expenses & cash flow dashboard
7. Deploy to AWS free tier
