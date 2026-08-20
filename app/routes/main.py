from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user, login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")


# --- Honest placeholders -----------------------------------------------
# These views exist in the original View enum (types.ts) but were never
# built out beyond a stub / not built at all in the source app. Keeping
# them as plain "coming soon" pages rather than inventing full features.

@bp.route("/calendar")
@login_required
def calendar():
    return render_template("coming_soon.html", feature="Crop Calendar")


@bp.route("/weather")
@login_required
def weather():
    return render_template("coming_soon.html", feature="Weather")


@bp.route("/profile")
@login_required
def profile():
    return render_template("coming_soon.html", feature="Profile")


@bp.route("/admin")
@login_required
def admin():
    return render_template("coming_soon.html", feature="Admin")
