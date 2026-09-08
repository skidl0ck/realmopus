# Contributing

## Workflow

Changes go through a branch and pull request - not committed straight to `main`:

```
git checkout -b feature/short-description
# make the change
git add .
git commit -m "Clear, specific description of the change"
git push -u origin feature/short-description
```

Open a pull request on GitHub. This automatically triggers the CI checks
(`.github/workflows/ci.yml`) - a Django system check, a check for any model change
missing its migration file, and a real production frontend build. Both need to pass
before merging.

Once merged: the frontend deploys automatically (Amplify watches `main`). The backend
does **not** deploy automatically - go to the repo's Actions tab → "Deploy Backend" →
"Run workflow" to trigger it manually. This is deliberate, not a missing feature - the
backend deploy runs real database migrations, and that's not something that should happen
silently on every merge without a deliberate decision to do so.

## Before opening a PR

- Run the app locally and actually exercise the change - see `docs/SETUP.md`. CI catches
  build breaks and missing migrations, but it doesn't run the app itself or click through
  any UI flow.
- If the change touches a model, confirm `python manage.py makemigrations` was actually
  run and the resulting migration file is committed - `git status` should show it. A
  migration that exists locally but was never `git add`ed is a real, easy mistake to make,
  and CI's migration-check step is specifically there to catch it (see `DEPLOYMENT.md`'s
  CI section for a real instance of this happening).
- If the change affects an environment variable - a new one, a renamed one, a changed
  default - update `docs/ENVIRONMENT_VARIABLES.md` in the same PR, not as a follow-up.
  That document is only useful if it stays in sync with the actual code.

## Branch naming

`feature/short-description` for new functionality, `fix/short-description` for bug fixes.
Nothing enforced by tooling - just a convention worth keeping consistent.

## Commit messages

A clear, specific sentence describing what changed and, where it's not obvious, why.
"Fix bug" or "Update code" convey nothing to someone reading `git log` later; "Fix demo
account notifications stacking on repeated logins" does.

## A note on scope

This project deliberately keeps its automated checks narrow - a system check, a
migration-drift check, and a real build, not a full test suite (there isn't one yet). That
means passing CI is a necessary signal, not a sufficient one: manual verification of
whatever the change actually does is still the main way correctness gets confirmed on this
project right now.
