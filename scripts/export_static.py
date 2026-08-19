"""Render Flask routes to static HTML and copy static assets into `dist/`.

Usage: python scripts/export_static.py

This creates a static snapshot of public marketing pages. Dynamic features
(login, admin, job applications) are redirected to the Render backend via
netlify.toml. Contact OTP/submit calls use API_BASE_URL when set.
"""
import os
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

# Configure the snapshot environment BEFORE importing the Flask app.
# ProductionConfig requires DATABASE_URL when FLASK_ENV=production.
# Force SQLite for the HTML snapshot so a local/Netlify .env cannot
# pull in Render PostgreSQL.
os.environ.pop("FLASK_ENV", None)
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("API_BASE_URL", "https://mjwebtech-website.onrender.com")

from app import create_app  # noqa: E402

DIST = BASE / "dist"
STATIC_SRC = BASE / "app" / "static"
STATIC_DST = DIST / "static"


def ensure_dist():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)


def copy_static():
    if STATIC_SRC.exists():
        shutil.copytree(STATIC_SRC, STATIC_DST)


def save(path: str, content: bytes):
    target = DIST / path.lstrip("/")
    if path.endswith("/"):
        target.mkdir(parents=True, exist_ok=True)
        target = target / "index.html"
    else:
        if target.name == "":
            target = target / "index.html"
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)


def main():
    app = create_app("development")
    client = app.test_client()

    ensure_dist()
    copy_static()

    routes = [
        "/",
        "/about",
        "/services",
        "/contact",
        "/blog",
        "/careers",
        "/privacy",
    ]

    try:
        from app.routes.blog import ARTICLES
        for a in ARTICLES:
            routes.append(f"/blog/{a['slug']}")
    except Exception:
        pass

    for route in routes:
        print("Rendering:", route)
        resp = client.get(route)
        if resp.status_code == 200:
            if route == "/":
                save("index.html", resp.data)
            else:
                save(f"{route.lstrip('/')}/index.html", resp.data)
        else:
            print(f"Warning: {route} returned {resp.status_code}; skipping")

    print("Static export complete. Output ->", DIST)
    print("API_BASE_URL ->", os.environ.get("API_BASE_URL"))


if __name__ == "__main__":
    main()
