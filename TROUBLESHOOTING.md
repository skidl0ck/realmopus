# Troubleshooting & Lessons Learned

Real issues hit during development, organized by symptom rather than chronologically -
deployment-specific gotchas (nginx socket permissions, the Redis AUTH URL format, GitHub
Actions' IP problem) live inline in `DEPLOYMENT.md` instead of being duplicated here.

## "The header/page shows a stale or wrong value briefly after a refresh, or React logs a hydration error"

This is what happens when client-only browser storage (`localStorage`, in this case) gets
read *during* a component's very first render instead of after it. The server has no
concept of `localStorage` at all - it always renders using the fallback value. If the
client's first render (during hydration) reads real cached data right away, it can produce
different output than what the server sent in the same pass, and React throws a mismatch
error over the difference, then discards and re-renders the whole tree from scratch.

**The fix, generalized:** any code reading `localStorage`/`sessionStorage` to influence
what a component shows must gate that read behind a piece of state that starts `false`
(matching what the server sees) and only flips `true` inside a `useEffect` - guaranteed by
React to run only *after* hydration has already committed, never during it. See
`frontend/src/lib/site-config.ts`'s `hydrated` state for a working example of this exact
pattern, and the reasoning documented inline there.

## "A throttled/429 response's wait time isn't showing correctly in the UI, even though the backend definitely sends it"

Browsers only expose a small, fixed set of response headers to cross-origin JavaScript by
default (`fetch`/`XMLHttpRequest`) - a server can set any header it wants, but unless it's
one of that small safelisted set, frontend code asking for it back gets `undefined`, even
though the header genuinely was sent and is visible in the browser's own Network tab.

`Retry-After` (which DRF automatically includes on every throttled response) is not one of
the default-exposed headers. Fixed with `CORS_EXPOSE_HEADERS` in `settings.py`. Worth
remembering for *any* custom response header a frontend needs to read across origins, not
just this one.

## "A concurrency fix seems to work when I test it, but I'm not fully confident it's actually correct"

If the test used SQLite, that confidence isn't earned yet. SQLite doesn't implement real
row-level locking - `select_for_update()` against it doesn't raise an error, but it also
doesn't actually prevent the race condition it's meant to prevent. A test against SQLite
can pass cleanly while the exact same code would still have the bug in production, where
this project actually runs PostgreSQL.

Anything involving `select_for_update()`, database-level locking, or a real concurrency
guarantee needs testing against a real PostgreSQL instance, with genuinely concurrent
requests (real threads or processes racing against the same row) - not sequential calls,
which can't trigger the race at all regardless of which database is behind them.

One more Postgres-specific trap worth knowing: `select_for_update()` combined with
`select_related()` across a **nullable** foreign key fails outright on Postgres
(`NotSupportedError`) - SQLite silently allows it. `Payment.contract`,
`Payment.reservation`, etc. are all nullable by design (exactly one is ever set per
payment), so locking a `Payment` row specifically needs `select_for_update(of=("self",))`
to scope the lock to just that table, not whatever nullable relation happens to be joined
in alongside it.

## "The frontend builds and runs fine locally, but Amplify's (or CI's) build fails"

Check whether `package.json` and `package-lock.json` have actually drifted out of sync -
a dependency version bumped in one without the other being regenerated to match. Local
development commonly uses `npm install`, which silently repairs this kind of drift on the
spot. Stricter environments (Amplify, and this project's own CI) use `npm ci`, which
refuses to proceed at all if the two files don't match exactly - specifically so builds
stay reproducible. Fix: `npm install` locally to regenerate the lock file correctly, then
commit and push it.

## "Pasting a multi-line block into a remote SSH session produces a file that looks right but isn't"

Multi-line pastes into an interactive terminal (`nano`, a raw shell prompt) aren't always
reliable - a dropped first line, collapsed newlines merging several lines into one, or
commands arriving in an unexpected order have all genuinely happened during this project's
own deployment. The safest pattern for anything long or exact (a systemd unit file, an
`.env` file): build it as a single, complete command using a heredoc
(`cat > file << 'EOF' ... EOF` or, for a privileged file, `sudo tee file << 'EOF' ...`),
and always verify the result afterward (`cat` it back, or in `nano` specifically, jump to
the end with Ctrl+End and check the reported line count matches what was actually pasted)
before trusting it and moving on.

## A meta-lesson about searching a codebase for something

A few points in this project's own documentation process, a "find every occurrence of X"
grep search turned out to be silently incomplete - missing a match because the search
pattern didn't account for a digit in a name (`AWS_S3_REGION_NAME`), or because the actual
code was split across multiple lines in a way a single-line pattern couldn't see. Neither
failure produced an error; the search just quietly returned less than the true answer.
Worth treating any "I searched for every occurrence" claim as provisional until it's been
cross-checked at least one more way (a broader pattern, a manual read-through of the
surrounding context) - especially before using that search's result to write documentation
that claims to be complete.
