# Security

This document summarizes a real, methodical security review of this project - not a
checklist run once, but an iterative process that found genuine bugs, some of which were
verified with actual exploit attempts against real infrastructure, not just reasoned about.
Where a claim below says "verified," it means an actual test was run and its result
observed - not that the code merely looks correct.

## Scope of the review

- Dependency audit (known CVEs, supply-chain risk)
- Authentication, session, and authorization testing
- Direct IDOR (Insecure Direct Object Reference) testing between real accounts
- Injection testing (SQL, XSS, template injection)
- File upload and PDF-generation (SSRF) review
- Concurrency / race-condition testing under real simulated load
- A full OWASP Top 10 (2025 revision) coverage pass
- STRIDE threat modeling
- An adversarial "how would an attacker actually approach this" walkthrough
- Infrastructure and secrets-management review of the production deployment

## Notable findings, and how each was actually confirmed

### A payment could be double-applied under concurrent requests
Two near-simultaneous confirm/capture requests for the same payment (triggered by a
frontend bug - an unguarded effect double-firing) both read the payment as "still pending"
before either had committed its update, so both proceeded. PayPal's own API rejected the
second attempt with a raw, unhandled `ORDER_ALREADY_CAPTURED` error; PayMongo's flow had
no equivalent gateway-side rejection, and actually applied the payment twice.

**Fix:** `select_for_update()` inside a transaction around the whole confirm/capture
sequence, so a concurrent duplicate now blocks until the first request commits, then
correctly sees the payment as already completed.

**Verification:** reproduced the exact race with genuine concurrent threads against a real
PostgreSQL database (not SQLite, which doesn't enforce real row-level locking and would
have silently passed either way) - confirmed the bug applied a payment twice before the
fix, and confirmed exactly one application after it.

### The same race condition, same fix, different endpoint
A reservation's extension-count cap had the identical shape - two concurrent "extend"
requests could both read the count as still under the limit before either committed. Same
`select_for_update()` fix, same concurrent-thread verification against real Postgres:
confirmed one request succeeds and the other is correctly rejected once the cap is
genuinely reached, not one request later.

### No rate limiting on login, registration, or the AI chatbot
All three were open to unlimited automated attempts. Fixed with request throttling -
login keyed by the submitted username (not just source IP, so distributing an attack
across many IPs doesn't help), registration and the chatbot keyed by IP.

**Verification:** scripted the actual attack in each case - repeated login attempts against
a real account (confirmed lockout after 5, confirmed the correct password still failed
while locked out, confirmed it worked again once the window passed), repeated registration
attempts (confirmed exactly 5 succeeded before a 429), and a rate-limit test against the
chatbot endpoint.

### A password change didn't invalidate existing sessions
Changing a password didn't blacklist previously-issued JWTs - a stolen token would have
kept working indefinitely even after the legitimate user changed their password.

**Fix:** password changes now blacklist every outstanding token for that user.
**Verification:** captured a real token, changed the password, confirmed the old token was
then rejected.

### Sequential filenames on stored documents
Contract and receipt PDFs were named predictably (`contract_GV-2026-0001.pdf`,
`...0002.pdf`, ...) - if ever served directly from disk with no auth check, this would let
someone walk the entire customer list by guessing filenames.

**Fix:** file storage moved to S3 with presigned, time-limited URLs (default 1 hour) -
knowing or guessing a filename alone grants nothing without a valid, freshly-generated
signature.

### Leaked credentials in an uploaded `.env` file
An early project snapshot included a real `.env` with live API keys (payment gateways, AI
API key). Rotated, and a proper `.gitignore` added - this had never existed for the
backend at all before, meaning nothing had actually been preventing a future accidental
commit of secrets.

## Access control

Every reservation, contract, payment, and receipt endpoint was tested directly with two
real accounts - confirmed cross-account access returns 404, not 403 (403 would confirm
the resource exists, leaking information even while denying access) - and confirmed access
to one's own data returns 200 normally.

Every staff-facing admin panel view was checked programmatically (AST-parsed, not
eyeballed) for a missing permission decorator - zero gaps found. `django.contrib.admin` is
deliberately excluded from this project entirely (see `backend/config/settings.py`) - it
would otherwise provide raw, unrestricted CRUD access to every model, completely bypassing
the role-based permission system and audit logging that `admin_panel` carefully implements.

## Injection & input handling

No raw SQL, `.extra()`, `.raw()`, `eval`, `exec`, `pickle`, or `subprocess` anywhere in the
backend - everything goes through the Django ORM. No `dangerouslySetInnerHTML` anywhere in
the frontend. PDF generation (`xhtml2pdf`) was checked specifically for SSRF risk via
external image references - no exploitable path found in any current template, though the
underlying library capability is noted as an architectural risk worth re-checking if new
templates are ever added with user-influenced image sources.

## Infrastructure & secrets

- Every AWS credential in this project is a narrowly-scoped IAM user - the S3 credentials
  can only touch that one bucket, nothing else in the AWS account. Nothing uses root
  account keys anywhere.
- The database and Redis are both network-isolated - reachable only from the application
  server's own security group, never directly from the internet.
- The automated deployment's SSH key is restricted at the protocol level to running exactly
  one predefined script, regardless of what command is actually sent to it - even a fully
  compromised copy of that key can't be used for anything beyond that one deployment
  action.
- Production runs over genuine TLS (Let's Encrypt) with HSTS enforced, not self-signed or
  optional HTTPS.
- `DEBUG` and `SECRET_KEY` both fail loud at startup if misconfigured for production,
  rather than silently running in a less-safe state.

## OWASP Top 10 (2025) coverage

| Category | Status |
|---|---|
| A01 Broken Access Control (incl. SSRF) | Direct IDOR testing, PDF/SSRF review, admin view permission audit |
| A02 Security Misconfiguration | `DEBUG`/`SECRET_KEY` fail-safe startup checks, HTTPS/HSTS enforced, CORS explicitly scoped |
| A03 Software Supply Chain Failures | Dependencies pinned to exact tested versions, Dependabot configured for update PRs |
| A04 Cryptographic Failures | Token blacklisting on password change, TLS enforced end to end, `pbkdf2_sha256` password hashing (Django's current default, verified - not overridden to anything weaker) |
| A05 Injection | ORM-only, no raw SQL, no XSS vectors found |
| A06 Insecure Design | Payment amounts always server-computed from the database, never trusted from the client - tested directly by attempting to submit a manipulated amount |
| A07 Authentication Failures | Rate limiting (login, registration, chatbot), account deactivation tested directly, session invalidation on password change |
| A08 Software/Data Integrity Failures | Pinned dependencies, Dependabot, no insecure deserialization anywhere |
| A09 Logging & Alerting Failures | Dedicated security logger for auth events (failed/successful logins, deactivated-account attempts), tested against a log-injection attempt specifically |
| A10 Mishandling of Exceptional Conditions | Permission checks fail closed throughout - verified no `AllowAny`-by-default gaps |

## Known limitations

This was a thorough internal review, not a substitute for professional, independent
penetration testing - no external firm or bug bounty has evaluated this project. The
threat model covers this application's own code and infrastructure; it does not cover the
security practices of third-party services it depends on (PayPal, PayMongo, AWS, GitHub)
beyond how this project's own credentials and integrations with them are scoped and
secured.

## Reporting a vulnerability

This is a portfolio/demonstration project rather than a company with a formal disclosure
program - if you find something, opening a GitHub issue (or contacting the maintainer
directly, for anything sensitive enough to want kept private until fixed) is the right way
to report it.
