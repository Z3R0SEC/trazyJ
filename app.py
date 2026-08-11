import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

import config

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "myBookings.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = "forMyBrotherSessionHandl3r@3211123"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            contact       TEXT NOT NULL,
            event_type    TEXT,
            event_date    TEXT,
            message       TEXT,
            created_at    TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@app.context_processor
def inject_globals():
    return {
        "cfg": config,
        "current_year": datetime.now(timezone.utc).year,
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        canonical_url=f"{request.host_url}",
        page_title=f"{config.ARTIST_STAGE_NAME} — Official Artist Profile",
    )


@app.route("/contact", methods=["POST"])
def contact():
    name = request.form.get("name", "").strip()
    contact_info = request.form.get("contact", "").strip()
    event_type = request.form.get("event_type", "").strip()
    event_date = request.form.get("event_date", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not contact_info:
        flash("Add your name and a way to reach you before sending.", "error")
        return redirect(url_for("index") + "#bookings")

    db = get_db()
    db.execute(
        """
        INSERT INTO bookings (name, contact, event_type, event_date, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            contact_info,
            event_type,
            event_date,
            message,
            datetime.now(timezone.utc).isoformat(timespec="seconds"),
        ),
    )
    db.commit()

    flash(
        "Sent. Trazy Jay's team will get back to you — for a faster reply, "
        "message the WhatsApp line directly.",
        "success",
    )
    return redirect(url_for("index") + "#bookings")

@app.route("/sitemap.xml")
def sitemap():
    pages = [
        {"loc": f"{request.host_url}", "priority": "1.0", "changefreq": "weekly"},
        {"loc": f"{request.host_url}contact", "priority": "1.0", "changefreq": "weekly"}
    ]
    xml = render_template("sitemap.xml", pages=pages)
    return Response(xml, mimetype="application/xml")


@app.route("/robots.txt")
def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {request.host_url}sitemap.xml",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(_e):
    return render_template("500.html"), 500


init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
