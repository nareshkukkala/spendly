# Step 5 — Backend routes for the profile page (edit profile)

## Goal

Add the write-side route the profile page is still missing: let a
logged-in user update their name, email, and (optionally) password
from `/profile`. Spec 04 built `/profile` as read-only and explicitly
deferred this ("Editing profile fields (name, email, password) — this
step is display-only; no form, no `POST /profile`.").

## Current state

- `/profile` (`app.py`) is `GET`-only, session-gated, and renders
  `profile.html` with `user`, `expenses`, `total`, and
  `category_totals`. No route currently reads or writes edited
  profile fields.
- `templates/profile.html` shows `user["name"]`, `user["email"]`, and
  `user["created_at"]` read-only inside `.profile-header`. No form.
- `users` table (`database/db.py`): `id`, `name`, `email` (UNIQUE),
  `password_hash`, `created_at`. No `updated_at` column.
- Validation precedent already exists in `register()`: required
  fields, `len(password) >= 8`, a duplicate-email check
  (`SELECT id FROM users WHERE email = ?`) before insert, with
  `sqlite3.IntegrityError` handled as a fallback net. Password
  verification precedent exists in `login()` via
  `check_password_hash`.
- No flash-messaging system exists anywhere in the app (`base.html`
  has no message block). Every existing form (`register`, `login`)
  reports errors by re-rendering the same template with an `error`
  variable, HTTP 200 — this step should follow that same pattern
  rather than introducing session-based flashing.
- Reusable form CSS already exists and isn't auth-specific despite
  its class names: `.form-group`, `.form-input`, `.btn-submit`,
  `.auth-error` (`static/css/style.css:474-526`), used as-is by both
  `register.html` and `login.html`.

## Scope

### `POST /profile` — extend the existing `profile()` view

Change `@app.route("/profile")` to `methods=["GET", "POST"]`.

On `POST`:

1. Still require `session.get("user_id")` first (existing check) —
   redirect to `/login` if absent, same as today.
2. Read `name`, `email` (both `.strip()`), and optional
   `current_password`, `new_password`, `confirm_password`.
3. Validate:
   - `name` and `email` required, non-blank.
   - If `email` differs from the user's current email, check
     uniqueness (`SELECT id FROM users WHERE email = ? AND id != ?`)
     — same idea as `register()`'s duplicate check, but excluding the
     current user.
   - Password change is optional: only validate/apply it if
     `new_password` is non-blank.
     - `current_password` must be provided and must pass
       `check_password_hash` against the stored hash, else error
       `"Current password is incorrect."`.
     - `new_password` must be 8+ characters (same rule as
       registration).
     - `confirm_password` must match `new_password`, else error
       `"New passwords do not match."`.
4. On any validation failure: re-run the same `expenses` /
   `total` / `category_totals` queries the `GET` branch uses (the
   template needs them regardless) and re-render `profile.html` with
   `edit_error` set, HTTP 200 — don't blank the expense list just
   because the edit form failed.
5. On success: `UPDATE users SET name = ?, email = ? [, password_hash
   = ?] WHERE id = ?`, `db.commit()`, redirect (`302`) back to
   `/profile` — PRG pattern, consistent with `register`/`login`
   redirecting after a successful write.
6. Wrap the update in `try/except sqlite3.IntegrityError` as a
   fallback for the email-uniqueness race, same defensive pattern
   `register()` uses.

### `templates/profile.html` — add an edit form

- New section below `.profile-header` (always-visible, no
  show/hide toggle — `main.js` is an empty placeholder and this step
  shouldn't add page JS).
- One `<form method="POST" action="{{ url_for('profile') }}">`
  containing:
  - Name / email fields, prefilled with `user["name"]` /
    `user["email"]`.
  - Optional password-change fields — current password, new
    password, confirm new password — all blank by default, none
    marked `required` (changing password is optional).
- Reuse `.form-group` / `.form-input` / `.btn-submit` / `.auth-error`
  unchanged; show `{% if edit_error %}` above the form, same pattern
  as `register.html`/`login.html`'s `{% if error %}`.

### `static/css/style.css`

Only add layout CSS to place the new form within `.profile-section`
(e.g. a `.profile-edit` wrapper and spacing), in the existing
`/* Profile page */` section. No new input/button/error styles —
`.form-group`/`.form-input`/`.btn-submit`/`.auth-error` are reused
as-is.

### Out of scope for this step

- Account deletion.
- Email verification / re-confirmation on email change.
- "Forgot password" flow (resetting without knowing the current
  password).
- An `updated_at` tracking column or audit trail — not in the
  current schema, not requested.
- CSRF protection — same deferred reasoning as specs 02/03.
- Avatar/profile picture — no such column on `users` (already
  flagged out of scope in spec 04).

## Files touched

- `app.py` — `profile()` becomes `methods=["GET", "POST"]`; add the
  validation/update logic above.
- `templates/profile.html` — add the edit form section.
- `static/css/style.css` — small additions to the existing
  `/* Profile page */` section for form placement; no new
  form-control styles.
- `database/db.py` — no changes; existing schema and `get_db()`
  already support this.

## Manual test plan

1. `python3 database/db.py` (fresh, seeded DB), then `python3 app.py`.
2. Log in as the demo user, go to `/profile`. Change just the name,
   submit → redirected back to `/profile`, header shows the new
   name, expense list/total unaffected.
3. Change the email to one already used by another account → page
   re-rendered with an error, expense list still shown (not
   blanked), email unchanged in the DB.
4. Change the email to a new, unused address → success; log out and
   log back in with the new email.
5. Fill in "new password" without "current password" (or with a
   wrong current password) → error "Current password is incorrect.",
   password unchanged (verify by logging out and back in with the
   old password).
6. Fill in current password correctly, a new password meeting the
   8-char minimum, and a matching confirm field → success; log out,
   confirm login fails with the old password and succeeds with the
   new one.
7. Leave all password fields blank while updating name/email →
   succeeds, password untouched.
