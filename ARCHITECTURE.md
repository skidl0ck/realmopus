# Architecture

## System overview

```
┌─────────────────────┐         ┌─────────────────────┐
│   Public site /      │  JWT    │                     │
│   Client portal       │◀──────▶│                     │
│   (Next.js, browser)  │  HTTPS  │                     │
└─────────────────────┘         │   Django + DRF API   │
                                  │                     │
┌─────────────────────┐         │                     │
│   Staff admin panel   │ session │                     │
│   (server-rendered     │◀──────▶│                     │
│   Django templates)    │  cookie │                     │
└─────────────────────┘         └──────────┬──────────┘
                                             │
                              ┌──────────────┼──────────────┐
                              ▼              ▼              ▼
                         PostgreSQL       Redis            S3
                       (all app data)  (cache, Celery   (photos, PDFs,
                                        queue)           receipts)
```

Two genuinely different frontends talk to the same backend, using two different
authentication mechanisms - see [Authentication](#authentication) below.

## Backend structure

Seven Django apps, each owning a distinct part of the domain:

| App | Owns |
|---|---|
| `accounts` | Users, roles, authentication (JWT issuing, the demo-account mechanism) |
| `properties` | Projects, Lots, Lot photos, Reservations |
| `sales` | Contracts, installment schedules, fees, sales commissions, payment reminders |
| `payments` | Payments (from any source - installment, reservation fee, or a not-yet-reserved lot), Receipts |
| `expenses` | Staff-tracked operational expenses and categories, feeding into cash-flow reporting |
| `core` | Cross-cutting concerns: the AI chatbot, notifications, demo-account reset logic, site-wide settings |
| `admin_panel` | The entire server-rendered staff interface - views, templates, role-based permissions, audit logging |

`django.contrib.admin` is deliberately not installed at all - see `SECURITY.md` for why.

## Frontend structure

Four route groups under `frontend/src/app/`:

| Route group | Contains |
|---|---|
| `(public)` | Homepage, lot listings - no login required |
| `(client-portal)` | Everything under `/portal/*` - reservations, contracts, payment schedule, receipts, checkout flows |
| `(dashboard)` | Staff-facing dashboard views (`admin`, `agent`, `accountant` role variants) |
| `login` / `register` | Top-level, outside any group |

## Authentication

This project deliberately runs **two separate authentication systems**, not one shared
mechanism stretched to cover both use cases:

- **The client-facing API (JWT)** - the Next.js frontend authenticates with a JWT access/
  refresh token pair, sent as an `Authorization: Bearer` header. Stateless, CORS-friendly,
  and appropriate for a separately-hosted SPA-style frontend calling a REST API.
- **The staff admin panel (Django sessions)** - server-rendered pages authenticate with
  Django's standard session + CSRF-cookie mechanism, since the admin panel is same-origin,
  traditional server-rendered HTML, not a separate API client.

This split matters for reasoning about CSRF specifically: `CSRF_TRUSTED_ORIGINS` is
deliberately *not* configured anywhere in this project, and that's correct, not an
oversight - the admin panel is only ever accessed same-origin (staff type the URL directly
into their browser), and the JWT-based API is inherently not vulnerable to CSRF in the
first place, since CSRF specifically exploits cookie-based auth being sent automatically by
the browser, which a bearer token in a header never is.

## Core data model

```
Project ──< Lot ──< LotImage
             │
             ├──< Reservation
             │
             └── Contract (1:1, optional)
                    │
                    ├──< Installment
                    ├──< Fee
                    ├──< PaymentReminder
                    └── Commission (1:1, optional)

Payment ── exactly one of: Contract / Reservation / (pending_reservation_lot + client) / Installment
   │
   └── Receipt (1:1)
```

A few relationships worth calling out specifically:

- **`Contract.lot` is `OneToOneField`, not `ForeignKey`** - a lot can have at most one
  contract ever, enforced at the database level, not just application logic.
- **A `Payment` links to exactly one of four possible targets** - a contract installment, a
  reservation, or (for the "no reservation exists yet until payment succeeds" checkout
  flow) a not-yet-created reservation's lot and client directly. This is what lets the
  same `Payment`/`Receipt` machinery serve every payment scenario in the app without
  needing a separate model per payment type.
- **`Payment.contract` and `Payment.reservation` are both `on_delete=PROTECT`** - a real
  payment can never be silently orphaned by an unrelated delete elsewhere in the codebase.
  This is also exactly why the demo-account reset logic (`core/demo.py`) has to delete
  `Payment` rows before it can delete the `Reservation`/`Contract` rows they reference -
  `PROTECT` would otherwise block the delete outright.

## Key request flow: reserving a lot through to an active contract

1. **Browse** - a visitor views `(public)/lots`, an unauthenticated, publicly cached list.
2. **Reserve** - once logged in, reserving a lot creates a `Reservation` row and moves the
   `Lot.status` to `reserved`. If a reservation fee applies, this routes through the same
   checkout flow as any other payment (step 4) before the reservation is actually created -
   see the "no entry until paid" pattern in `payments/views.py`.
3. **Convert to contract** - a staff member, not the client, creates the `Contract` from
   the admin panel once terms are finalized. This is deliberate: contracts are never
   self-service, only reservations are.
4. **Installment schedule** - `sales/services.py`'s `generate_amortization_schedule()`
   creates the `Installment` rows for the contract's term.
5. **Pay** - a client pays an installment via PayPal or PayMongo (GCash/Maya/card). The
   gateway redirect happens in a popup window, not a full-page navigation, so the checkout
   page's own state survives; `payments/views.py`'s confirm/capture endpoints independently
   re-verify the payment with the gateway itself before ever marking anything paid - the
   frontend's own claim of success is never trusted on its own.
6. **Receipt** - a successful payment automatically generates a `Receipt` with a PDF,
   stored in S3, served back via a presigned URL.
