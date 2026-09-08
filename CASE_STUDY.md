# The Story Behind This Project

This isn't a changelog - a traditional version-by-version log doesn't fit a continuously
deployed project with no release tags, and it would just duplicate what GitHub's own
commit history already does better. This is the story instead: the actual phases this
project went through, the real decisions made along the way, and the real bugs found. For
the technical detail behind any of it, `SECURITY.md`, `ARCHITECTURE.md`, and
`DEPLOYMENT.md` go deeper - this is the narrative version.

## Starting point

This project didn't begin from a blank repository. It started as an already-functioning
real estate sales and operations platform - reservations, contracts, installment
schedules, payments, a role-based staff admin panel - and the work from here was about
taking something that worked and making it something that could actually be trusted in
production, deployed for real, and shown to people.

## Phase 1: The security audit

Not a quick pass. A dependency audit against known CVEs, a full OWASP Top 10 (2025)
review, direct IDOR testing between real accounts, injection testing, STRIDE threat
modeling, and - closer to the end - an adversarial walkthrough framed as "if I were
actually trying to break this, what would I try first."

The real findings were the kind that matter. A payment could be double-applied under
concurrent requests - two near-simultaneous confirmation calls for the same payment both
read it as "still pending" before either had committed, so both went through. Reproducing
that convincingly meant setting up genuine concurrent threads against a real PostgreSQL
database, not just reasoning about the code - SQLite doesn't enforce real row-level
locking, so a test against it would have passed regardless of whether the bug was actually
fixed. Once fixed, the same concurrent-thread test confirmed exactly one payment applied,
not two.

Login had no rate limiting at all. Neither did registration, or the AI chatbot endpoint -
each one open to unlimited scripted attempts. An uploaded project snapshot turned out to
contain a real `.env` file with live API keys, sitting in a backend that had never had a
`.gitignore` at all. Small, human mistakes, the kind that happen on real projects - found
and fixed rather than assumed away.

## Phase 2: Making the project experienceable

An audited, hardened app that nobody can actually try isn't worth much for a portfolio. So
the next phase was building a real demo mode - not a stripped-down sandbox, but the actual
application, with a shared public login that resets to a clean, realistic state (an active
contract, a partial payment history, real receipts) on every single visit, so one visitor's
poking around never leaks into the next person's experience.

Getting the isolation right took real thought. The reset logic needed to survive a
visitor reserving a completely different lot mid-session, and - a bug caught during actual
production testing - every login was re-triggering the same "you have a new payment"
notifications, stacking a few more onto the pile every single time anyone tried the demo.
Fixed and re-verified by simulating several consecutive logins and confirming the count
actually stayed flat instead of climbing.

## Phase 3: A name that was actually available

The project's original name turned out to belong to an active, real company selling
software in the exact same category. Worth taking seriously for anything that might
actually be shown to an employer or a client - a name collision with a genuine competitor
isn't a good look, and in the worse case, a legal one.

What followed was less "pick a nicer name" and more "discover how saturated proptech
naming actually is in 2026." Several strong candidates in a row turned out to already
belong to real, live products - one collision was severe enough (three separate active
businesses on the same name, one of them a direct competitor with a ™ already in use) that
it was worth walking away from entirely rather than risk it. The name that survived actual
scrutiny - checked properly, not just googled once and hoped - became the project's real
identity, applied in a full rename sweep across the entire codebase. That sweep caught its
own bug along the way: a CSS class renamed in one file but not in a second file that also
referenced it, found only because the fix was verified with a real browser, not just a
text search confirming the word had changed everywhere it appeared.

## Phase 4: From a laptop to real infrastructure

Then the actual deployment - not a one-click platform, but real AWS infrastructure built
piece by piece: a managed Postgres database, a managed Redis instance, an EC2 server
configured from a bare Ubuntu image up through gunicorn, Celery, and nginx, a genuine
Let's Encrypt TLS certificate, and a separately-hosted frontend on Amplify, all wired
together and talking to each other correctly.

This is where the gap between "the code is correct" and "the system actually runs in
production" showed up most clearly. A working local setup doesn't automatically become a
working production one - reaching that point took working through nginx unable to reach
the application process at all (a Linux permissions problem, not a code problem), a Redis
connection that failed in a way that took real investigation to trace to a single missing
word in a connection string, and more than one moment of "this should work" followed by
figuring out precisely why it didn't. The full account, including what actually went
wrong and why, lives in `DEPLOYMENT.md` - worth reading if any of that sounds
interesting, since a runbook that only shows the happy path isn't nearly as useful as one
that shows the real one.

## Phase 5: A pipeline that proved itself immediately

The last major piece was real CI/CD - automated checks on every pull request, a
deliberately manual-trigger deploy for anything touching the database. Its very first real
run, on its very first real feature (a GDPR-compliant cookie consent system, built
properly with genuine functional/necessary categorization, not just a banner), immediately
caught two real problems: a database migration that had quietly never made it to GitHub at
all despite already running in production, and a security group gap that would have
silently blocked every future automated deployment. Exactly the kind of thing a pipeline
like this exists to catch - and it did, on the first try, before either problem became a
real incident.

## Where it stands now

A live, working application - a real AWS deployment, real TLS, a tested CI/CD pipeline,
and a security posture that's been genuinely exercised, not just asserted. Still a single
production incident away from teaching another lesson, the way every real system is - but
built, at every stage, by actually testing the claim rather than trusting that it should
be true.
