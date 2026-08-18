"""
routes/errors.py — Custom HTTP error handlers (404, 500, 413, 403).
"""
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError


def register_error_handlers(app):

    def _api_error_response(message: str, status_code: int, error_code: str):
        return jsonify({"success": False, "error": error_code, "message": message}), status_code

    @app.errorhandler(CSRFError)
    def csrf_error(e):
        app.logger.warning("CSRF failed on %s %s: %s", request.method, request.path, e.description)
        if request.path.startswith("/api/"):
            return _api_error_response(
                "Your session expired. Refresh the page and try again.",
                400,
                "csrf_failed",
            )
        flash("Your session expired. Please try again.", "warning")
        if request.endpoint == "auth.login" or request.path.rstrip("/") == "/login":
            return redirect(url_for("auth.login"))
        if request.endpoint == "auth.register" or request.path.rstrip("/") == "/register":
            return redirect(url_for("auth.register"))
        return render_template("errors/400.html"), 400

    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return _api_error_response("The request could not be processed.", 400, "bad_request")
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith("/api/"):
            return _api_error_response("Access denied.", 403, "forbidden")
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return _api_error_response("The requested endpoint was not found.", 404, "not_found")
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        if request.path.startswith("/api/"):
            return _api_error_response("The uploaded payload is too large.", 413, "payload_too_large")
        return render_template("errors/413.html"), 413

    @app.errorhandler(500)
    def server_error(e):
        if request.path.startswith("/api/"):
            return _api_error_response("An internal server error occurred.", 500, "internal_server_error")
        return render_template("errors/500.html"), 500
