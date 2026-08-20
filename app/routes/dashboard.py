from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import DiagnosisScan, ChatSession

bp = Blueprint("dashboard", __name__)

# 7-day rainfall forecast. Kept as clearly-labeled mock data, matching the
# original React app's MOCK_WEATHER array — there was no live weather API
# wired into the source project. Swap this for a real call (e.g. to the
# free, keyless Open-Meteo API) if/when you want live data.
MOCK_WEATHER = [
    {"day": "Mon", "temp": 28, "condition": "Sunny", "rainChance": 0},
    {"day": "Tue", "temp": 27, "condition": "Cloudy", "rainChance": 20},
    {"day": "Wed", "temp": 24, "condition": "Rainy", "rainChance": 80},
    {"day": "Thu", "temp": 25, "condition": "Rainy", "rainChance": 60},
    {"day": "Fri", "temp": 29, "condition": "Sunny", "rainChance": 10},
    {"day": "Sat", "temp": 31, "condition": "Sunny", "rainChance": 0},
    {"day": "Sun", "temp": 30, "condition": "Cloudy", "rainChance": 15},
]


@bp.route("/dashboard")
@login_required
def index():
    last_scan = (
        DiagnosisScan.query.filter_by(user_id=current_user.id)
        .order_by(DiagnosisScan.created_at.desc())
        .first()
    )
    return render_template("dashboard/index.html", last_scan=last_scan, weather=MOCK_WEATHER)


@bp.route("/crop-doctor")
@login_required
def crop_doctor():
    return render_template("dashboard/crop_doctor.html")


@bp.route("/chat")
@login_required
def chat():
    session = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.created_at.desc()).first()
    messages = [m.to_dict() for m in session.messages] if session else []
    return render_template("dashboard/chat.html", messages=messages)
