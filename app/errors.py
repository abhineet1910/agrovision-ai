from flask import render_template, request, jsonify
from app.extensions import db


def register(app):
    def wants_json():
        return request.path.startswith("/api/")

    @app.errorhandler(400)
    def bad_request(e):
        if wants_json():
            return jsonify({"error": "Bad request."}), 400
        return render_template("errors/generic.html", code=400, message="Bad request."), 400

    @app.errorhandler(401)
    def unauthorized(e):
        if wants_json():
            return jsonify({"error": "Authentication required."}), 401
        return render_template("errors/generic.html", code=401, message="Please log in."), 401

    @app.errorhandler(403)
    def forbidden(e):
        if wants_json():
            return jsonify({"error": "Forbidden."}), 403
        return render_template("errors/generic.html", code=403, message="You don't have access to that."), 403

    @app.errorhandler(404)
    def not_found(e):
        if wants_json():
            return jsonify({"error": "Not found."}), 404
        return render_template("errors/generic.html", code=404, message="Page not found."), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large."}), 413

    @app.errorhandler(429)
    def rate_limited(e):
        if wants_json():
            return jsonify({"error": "Too many requests. Please slow down."}), 429
        return render_template("errors/generic.html", code=429, message="Too many requests."), 429

    @app.errorhandler(500)
    def server_error(e):
        # Always log the real exception to the console/log file, even though
        # the user only ever sees the friendly page. Without this, a 500
        # looks identical whether it's a DB issue, a bad Gemini key, or a
        # code bug — and you're stuck guessing.
        app.logger.exception("Unhandled server error: %s", e)
        db.session.rollback()
        if wants_json():
            return jsonify({"error": "Something went wrong on our end."}), 500
        return render_template("errors/generic.html", code=500, message="Something went wrong on our end."), 500
