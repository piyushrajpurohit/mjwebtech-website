from functools import wraps
from flask import request, session, redirect, url_for, flash, jsonify
from app.models import User


def login_required(view_func):
    """Require a logged-in user session for Flask routes."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Authentication required.",
                    "error": "unauthorized",
                }), 401

            flash("Please log in to access that page.", "warning")
            next_url = request.full_path if request.query_string else request.path
            if next_url.endswith("?"):
                next_url = next_url[:-1]
            return redirect(url_for("auth.login", next=next_url))

        user = User.query.get(session["user_id"])
        if not user or not user.is_active:
            session.pop("user_id", None)
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Authentication required.",
                    "error": "unauthorized",
                }), 401
            flash("Please log in to access that page.", "warning")
            return redirect(url_for("auth.login"))

        return view_func(*args, **kwargs)

    return wrapper


def admin_required(view_func):
    """Require an authenticated admin user for Flask routes."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Authentication required.",
                    "error": "unauthorized",
                }), 401

            flash("Please log in to access that page.", "warning")
            next_url = request.full_path if request.query_string else request.path
            if next_url.endswith("?"):
                next_url = next_url[:-1]
            return redirect(url_for("auth.login", next=next_url))

        user = User.query.get(session["user_id"])
        if not user or not user.is_active or not user.is_admin:
            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "message": "Admin access required.",
                    "error": "forbidden",
                }), 403

            flash("You do not have access to this page.", "danger")
            return redirect(url_for("main.index"))

        return view_func(*args, **kwargs)

    return wrapper
