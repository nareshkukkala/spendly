from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, close_db
import sqlite3

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"  # dev-only; replace with env var in production
app.teardown_appcontext(close_db)


@app.template_filter("format_date")
def format_date(value):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%b %d, %Y")
        except ValueError:
            continue
    return value


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        error = None
        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()
            if existing:
                error = "An account with that email already exists."

        if error:
            return render_template("register.html", error=error)

        db = get_db()
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="An account with that email already exists.",
            )

        session["user_id"] = cursor.lastrowid
        return redirect(url_for("landing"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = None
        if email and password:
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("landing"))

        return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()

    if user is None:
        session.pop("user_id", None)
        return redirect(url_for("login"))

    edit_error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        password_hash_to_set = None

        if not name or not email:
            edit_error = "Name and email are required."
        elif email != user["email"]:
            existing = db.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                (email, user["id"]),
            ).fetchone()
            if existing:
                edit_error = "An account with that email already exists."

        if not edit_error and new_password:
            if not current_password or not check_password_hash(
                user["password_hash"], current_password
            ):
                edit_error = "Current password is incorrect."
            elif len(new_password) < 8:
                edit_error = "Password must be at least 8 characters."
            elif new_password != confirm_password:
                edit_error = "New passwords do not match."
            else:
                password_hash_to_set = generate_password_hash(new_password)

        if not edit_error:
            try:
                if password_hash_to_set:
                    db.execute(
                        "UPDATE users SET name = ?, email = ?, password_hash = ? WHERE id = ?",
                        (name, email, password_hash_to_set, user["id"]),
                    )
                else:
                    db.execute(
                        "UPDATE users SET name = ?, email = ? WHERE id = ?",
                        (name, email, user["id"]),
                    )
                db.commit()
            except sqlite3.IntegrityError:
                edit_error = "An account with that email already exists."

        if not edit_error:
            return redirect(url_for("profile"))

    expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC",
        (session["user_id"],),
    ).fetchall()

    total = sum(row["amount"] for row in expenses)

    category_sums = {}
    for row in expenses:
        category_sums[row["category"]] = category_sums.get(row["category"], 0) + row["amount"]
    category_totals = sorted(category_sums.items(), key=lambda item: item[1], reverse=True)

    return render_template(
        "profile.html",
        user=user,
        expenses=expenses,
        total=total,
        category_totals=category_totals,
        edit_error=edit_error,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
