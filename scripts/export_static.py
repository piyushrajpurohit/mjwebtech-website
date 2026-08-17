"""Render Flask routes to static HTML and copy static assets into `dist/`.

Usage: python scripts/export_static.py

This script imports the application factory and uses the test client to
request public routes and save their rendered HTML into a directory named
`dist/`. Static files from `app/static/` are copied to `dist/static/`.

Important: This creates a static snapshot. Dynamic features (forms, login,
OTP verification, server-side email) will not function in the static export.
Review the README for recommended production architecture and limitations.
"""
import os
import shutil
from pathlib import Path

from app import create_app


BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist"
STATIC_SRC = BASE / "app" / "static"
STATIC_DST = DIST / "static"


def ensure_dist():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)


def copy_static():
    if not STATIC_SRC.exists():
        return
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
    app = create_app("production")
    client = app.test_client()

    ensure_dist()
    copy_static()

    routes = [
        "/",
        "/about",
        "/services",
        "/contact",
        "/blog",
    ]

    # Add blog articles dynamically from the module
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
            # Save / -> index.html, /about -> /about/index.html
            if route == "/":
                save("index.html", resp.data)
            else:
                save(f"{route.lstrip('/')}/index.html", resp.data)
        else:
            print(f"Warning: {route} returned {resp.status_code}; skipping")

    # Create basic security headers file for Netlify
    headers_text = (
        "/*\n"
        "  X-Frame-Options: DENY\n"
        "  X-Content-Type-Options: nosniff\n"
        "  Referrer-Policy: no-referrer-when-downgrade\n"
        "  Permissions-Policy: geolocation=(), microphone=()\n"
        "  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload\n"
        "  Content-Security-Policy: default-src 'self' https:; script-src 'self' https://cdn.jsdelivr.net https://challenges.cloudflare.com 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://fonts.gstatic.com https://fonts.googleapis.com https://cdn.jsdelivr.net\n"
    )
    (DIST / "_headers").write_text(headers_text)

    # Create a simple redirects file to ensure clean URLs
    redirects_text = (
        "/blog/*  /blog/:splat  200\n"
    )
    (DIST / "_redirects").write_text(redirects_text)

    print("Static export complete. Output ->", DIST)


if __name__ == "__main__":
    main()
