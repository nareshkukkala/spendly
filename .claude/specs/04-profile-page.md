# Step 4 — Profile page

## Goal

Replace the `/profile` placeholder with a real, session-gated page that
shows the logged-in user's account info and their logged expenses —
and make `base.html`'s nav reflect whether someone is signed in, since
it now has a real page to link to.

## Current state

- `/profile` is an unimplemented placeholder — returns the plain
  string `"Profile page — coming in Step 4"`, doesn't render a
  template, and doesn't check `session` at all, so it's reachable
  whether or not anyone is logged in (`app.py:110-112`).
- Session handling already works end-to-end: `register()` and
  `login()` both set `session["user_id"]` on success, `logout()`
  clears it (`app.py`). Per spec 03, no route currently *reads*
  `session["user_id"]` to gate access — this step is the first to do
  so.
- `database/db.py` already fully implements `users` (`id`, `name`,
  `email`, `password_hash`, `created_at`) and `expenses` (`id`,
  `user_id`, `category`, `amount`, `description`, `date`,
  `created_at`) tables, and `seed_db()` seeds the demo user
  (`demo@spendly.dev` / `password123`) with 7 sample expenses across
  Food/Travel/Bills/Shopping categories. No schema changes needed.
- No `templates/profile.html` exists yet.
- `base.html`'s nav is static — it always renders "Sign in" /
  "Get started", regardless of session state (`base.html:21-24`).
  Flask exposes `session` to Jinja templates automatically, no
  context processor needed.
- `landing.html`'s `mock-card` / `mock-stats` / `mock-bars` markup and
  the matching CSS (`static/css/style.css:209-319`) are illustrative
  only — static numbers baked into the landing page template, not
  reused anywhere. They establish the visual language (stat tiles,
  category bars) this step should echo for the *real* dashboard, but
  per CLAUDE.md's convention ("scoped with distinct class names so
  sections stay independently editable") this step adds its own
  `profile-*` classes rather than repurposing `mock-*`.
- `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete` are
  still Step 7/8/9 placeholders (plain strings). This step links to
  them from the profile page but doesn't change their behavior.

## Scope

### `GET /profile` — implement the real view in `app.py`

Replace the placeholder body:

1. If `not session.get("user_id")`: redirect (`302`, `url_for(...)`)
   to `/login` — mirrors the inverse check `register()`/`login()`
   already do (`if session.get("user_id"): redirect to profile`).
2. Look up the user: `SELECT * FROM users WHERE id = ?` with
   `session["user_id"]`. If no row comes back (stale session — e.g.
   the user was deleted), treat it like a logged-out request:
   `session.pop("user_id", None)` and redirect to `/login`, rather
   than letting it 500 on `None`.
3. Query the user's expenses:
   `SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC`.
4. Compute summary stats in Python (no new DB helper needed —
   `get_db()` is enough):
   - `total` — sum of `amount` across the fetched rows.
   - `category_totals` — dict of category → summed amount, built
     dynamically from whatever categories are present (don't hardcode
     Food/Travel/Bills/Shopping), sorted descending by amount so the
     largest category bar renders first.
5. Render `profile.html` with `user`, `expenses`, `total`, and
   `category_totals`.

### `templates/profile.html` — new template

Extends `base.html`, following the structural pattern of
`register.html`/`landing.html` (a `content` block, no page-specific
CSS file per CLAUDE.md).

- **Header**: user's `name`, `email`, and "Member since" formatted
  from `created_at`.
- **Summary**: total spent and a category breakdown rendered as bars
  (same visual idea as `mock-bars`, new `profile-*` classes), driven
  by `category_totals` — however many categories exist, not a fixed
  three.
- **Expense list**: table/list of all fetched expenses (date,
  category, description, amount), read-only. Each row links "Edit" /
  "Delete" to `url_for('edit_expense', id=...)` /
  `url_for('delete_expense', id=...)` — those still hit the Step
  8/9 placeholder strings today, which is expected at this stage.
- **Add expense**: a button/link to `url_for('add_expense')` (Step 7
  placeholder today — expected).
- **Empty state**: if `expenses` is empty, show a friendly message
  ("No expenses yet — add your first one") instead of an empty
  table and a `total` of 0 with no explanation.

### `base.html` — auth-aware nav

Wrap the `nav-links` block in `{% if session.get('user_id') %}`:

- Logged in: link to `/profile` and a "Sign out" link
  (`url_for('logout')`) instead of "Sign in" / "Get started".
- Logged out: current behavior, unchanged.

### `static/css/style.css`

Add a new `/* Profile page */` section (after `/* Auth pages */`,
before `/* Legal pages */`, matching the existing section-header
convention) with `profile-*` classes for the header, stat/category
bars, expense list rows, and empty state. Reuse existing tokens
(`--paper-card`, `--border`, `--accent`, `--accent-2`, `--radius-md`,
etc.) rather than introducing new ones.

### Out of scope for this step

- Editing profile fields (name, email, password) — this step is
  display-only; no form, no `POST /profile`.
- Real add/edit/delete expense behavior — Steps 7-9. This page only
  links to those routes; their responses stay placeholder strings
  until those steps land.
- Pagination, filtering, or sorting controls on the expense list —
  just the full list ordered by date descending.
- CSRF protection — same reasoning as the registration/login specs:
  future hardening, not blocking this step.
- Avatar/profile picture — no such column on `users`.

## Files touched

- `app.py` — replace the `profile()` placeholder with the real view
  described above.
- `templates/profile.html` — new.
- `templates/base.html` — wrap `nav-links` in a session check.
- `static/css/style.css` — new "Profile page" section.
- `database/db.py` — no changes; existing schema and `get_db()`
  already support this.

## Manual test plan

1. `python3 database/db.py` (fresh, seeded DB), then `python3 app.py`.
2. Visit `/profile` while logged out → redirected to `/login`.
3. Log in as the demo user (`demo@spendly.dev` / `password123`) →
   redirected to `/profile`; page shows "Demo User" /
   `demo@spendly.dev`, all 7 seeded expenses newest-first, a total of
   ₹7,399.50, and a category breakdown across Food/Travel/Bills/
   Shopping.
4. While logged in, check the nav on any page (e.g. landing) shows
   "Profile" and "Sign out" instead of "Sign in"/"Get started".
5. Click "Sign out" → session cleared, redirected to `/`, nav reverts
   to the logged-out state, and `/profile` redirects to `/login`
   again.
6. Register a brand-new account (no expenses yet) → `/profile` shows
   the empty state, not a blank table or an unexplained ₹0 total.
7. Click an expense's "Edit"/"Delete" link, and the "Add expense"
   button → each lands on its existing Step 7/8/9 placeholder string
   (expected; not a 404 or 500).
