# Step 2 — Registration

## Goal

Wire up `POST /register` so the existing `register.html` form actually
creates a user, instead of only being served as a GET-rendered stub.

## Current state

- `GET /register` renders `templates/register.html` (`app.py:15-17`).
- The form posts to a hardcoded `action="/register"` with fields
  `name`, `email`, `password`, and expects an `error` template variable
  for validation/failure messages (`templates/register.html`).
- `database/db.py` already has `get_db()`, `init_db()`, and a `users`
  table (`id`, `name`, `email` UNIQUE, `password_hash`, `created_at`).
  No route in `app.py` uses it yet.
- No session/auth mechanism exists anywhere in `app.py`.

## Scope

Add a `POST` handler for `/register` in `app.py`. Keep it in the same
file, no blueprints, matching the rest of the codebase.

### Validation (server-side, in addition to the HTML `required`/`type=email` attrs)

- `name`, `email`, `password` all present and non-blank after `.strip()`.
- `password` at least 8 characters (the placeholder text already
  promises this).
- `email` not already registered (`SELECT id FROM users WHERE email = ?`).

On any validation failure: re-render `register.html` with `error` set
to a user-facing message, HTTP 200 (this matches the template's
existing `{% if error %}` block — no separate error template needed).

### On success

1. Hash the password with `werkzeug.security.generate_password_hash`
   (same helper `seed_db()` already uses).
2. Insert into `users` via `get_db()`, matching the parameterised-query
   pattern used in `database/db.py`.
3. Commit.
4. Log the new user in — store `user_id` in Flask's `session` (needs
   `app.secret_key` to be set; not currently configured anywhere).
5. Redirect (`302`, `url_for(...)`) to `/profile` — the natural
   post-registration landing page, even though it's still a Step 4
   placeholder today.

### Out of scope for this step

- `/login` POST handler (separate step).
- `/logout`, `/profile` real implementation (Steps 3–4).
- CSRF protection / rate limiting / email verification — not mentioned
  anywhere in the existing scaffold, treat as future hardening rather
  than blocking this step.

## Files touched

- `app.py` — change `register()` to accept `["GET", "POST"]`, add the
  logic above.
- No template changes needed — `register.html` already matches this
  contract.
- `database/db.py` — no changes; existing `get_db()`/schema already
  supports this.

## Manual test plan

1. `python3 database/db.py` (fresh DB), then `python3 app.py`.
2. Submit the form with a new name/email/password ≥ 8 chars →
   redirected to `/profile`, new row exists in `users` with a hashed
   (not plaintext) password.
3. Resubmit the same email → re-rendered form with a duplicate-email
   error, no second row inserted.
4. Submit with a 5-character password → re-rendered form with a
   length error.
5. Submit with an empty name → re-rendered form with a required-field
   error.
