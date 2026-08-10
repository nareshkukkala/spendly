# Step 3 — Login and logout

## Goal

Wire up `POST /login` so the existing `login.html` form actually
authenticates a user, and implement `GET /logout` to end the session —
replacing the two current stubs (`login()` is GET-only today; `logout()`
returns a plain placeholder string).

## Current state

- `GET /login` renders `templates/login.html` (`app.py:62-64`). No
  `POST` handler exists yet.
- The form posts to a hardcoded `action="/login"` with fields `email`
  and `password`, and expects an `error` template variable for
  failure messages (`templates/login.html:16-18`), matching the
  pattern `register.html` already uses.
- `/logout` is an unimplemented placeholder — returns the string
  `"Logout — coming in Step 3"` instead of a real response
  (`app.py:81-83`).
- Session/auth already exists: `app.secret_key` is set, and
  `POST /register` stores `session["user_id"]` on success
  (`app.py:7, 56`). Login should follow the same convention.
- `database/db.py` has `get_db()` and a `users` table (`id`, `name`,
  `email` UNIQUE, `password_hash`, `created_at`). `password_hash` is
  written with `werkzeug.security.generate_password_hash`.
- No route currently reads `session["user_id"]` to gate access or
  render user-specific content — `/profile` is still a Step 4
  placeholder that ignores the session entirely.

## Scope

### `POST /login` — add to the existing `login()` view in `app.py`

Change `@app.route("/login")` to `methods=["GET", "POST"]`, matching
how `register()` handles both verbs in one view.

Validation (server-side, in addition to the HTML `required`/`type=email`
attrs):

- `email` and `password` both present and non-blank after `.strip()`
  (email) / as submitted (password — no `.strip()`, matching
  `register()`'s treatment of password).
- Look up the user by email (`SELECT * FROM users WHERE email = ?`).
- If no user found, or
  `werkzeug.security.check_password_hash(user["password_hash"], password)`
  fails: treat both cases identically — same generic error message,
  so the response doesn't leak whether an email is registered.

On any validation failure: re-render `login.html` with `error` set to
`"Invalid email or password."`, HTTP 200 — mirrors `register.html`'s
`{% if error %}` block, no separate error template.

On success:

1. Store `user_id` in Flask's `session` (`session["user_id"] = user["id"]`),
   same key `register()` already uses so downstream code (e.g. a future
   `/profile`) doesn't need to care which route set it.
2. Redirect (`302`, `url_for(...)`) to `/profile` — same
   post-auth landing page `register()` redirects to.

### `GET /logout`

Replace the placeholder body with:

1. `session.pop("user_id", None)` — clear the session; use `.pop` with
   a default rather than `del` so hitting `/logout` while already
   logged out doesn't raise `KeyError`.
2. Redirect (`302`, `url_for(...)`) to `/` (the landing page).

No template needed — logout is a redirect-only action, consistent
with it being a plain link/nav action rather than a form.

### Out of scope for this step

- `/profile` real implementation, and gating it (or any other route)
  behind `session["user_id"]` — that's Step 4. This step only sets and
  clears the session; nothing reads it yet.
- Updating `base.html`'s nav to show "Sign out" / hide "Sign in" based
  on session state — the nav is currently static regardless of auth
  status, and no spec so far has touched it. Flag as a likely Step 4
  follow-up once `/profile` exists to link to.
- "Remember me" / persistent sessions, password reset, rate limiting,
  account lockout — not mentioned anywhere in the existing scaffold.
- CSRF protection — same reasoning as the registration spec: treat as
  future hardening, not blocking this step.

## Files touched

- `app.py` — change `login()` to accept `["GET", "POST"]` and add the
  logic above; replace the `logout()` placeholder body.
- No template changes needed — `login.html` already matches this
  contract (form fields, `error` variable).
- `database/db.py` — no changes; existing `get_db()`/schema already
  supports this.

## Manual test plan

1. `python3 database/db.py` (fresh, seeded DB), then `python3 app.py`.
2. Log in with the seeded demo user (`demo@spendly.dev` /
   `password123`) → redirected to `/profile`, `session["user_id"]`
   set (verify via a temporary `print(session)` or by confirming a
   subsequent request in the same browser session carries the
   session cookie).
3. Log in with a correct email but wrong password → re-rendered form
   with "Invalid email or password.", no redirect.
4. Log in with an email that doesn't exist → same generic error as
   above (not a different message).
5. Submit the form with an empty email or password → re-rendered form
   with the same generic error (or a required-field error — pick one
   and keep it consistent with step 3/4 above).
6. Visit `/logout` after logging in → redirected to `/`, session
   cleared (a second `/logout` visit doesn't error).
