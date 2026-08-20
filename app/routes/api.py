import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import DiagnosisScan, ChatSession, ChatMessage
from app.services.llm_service import analyze_crop_image, chat_reply, LLMError

bp = Blueprint("api", __name__, url_prefix="/api")


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


@bp.route("/scan", methods=["POST"])
@login_required
def create_scan():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use JPG, PNG, or WEBP."}), 400

    image_bytes = file.read()
    max_bytes = current_app.config["MAX_UPLOAD_MB"] * 1024 * 1024
    if len(image_bytes) > max_bytes:
        return jsonify({"error": f"File too large. Max {current_app.config['MAX_UPLOAD_MB']}MB."}), 400

    ext = secure_filename(file.filename).rsplit(".", 1)[-1].lower()
    stored_name = f"{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)

    try:
        with open(stored_path, "wb") as f:
            f.write(image_bytes)
    except OSError:
        return jsonify({"error": "Could not save the uploaded image."}), 500

    mime_type = file.mimetype or "image/jpeg"

    try:
        diagnosis = analyze_crop_image(image_bytes, mime_type=mime_type)
    except LLMError as exc:
        current_app.logger.warning("Crop analysis failed: %s", exc)
        return jsonify({"error": "AI analysis failed. Please try again."}), 502

    scan = DiagnosisScan(
        user_id=current_user.id,
        image_path=f"uploads/{stored_name}",
        disease_name=diagnosis["diseaseName"],
        severity=diagnosis["severity"],
        confidence=diagnosis["confidence"],
        description=diagnosis["description"],
        treatments=diagnosis["treatments"],
        fertilizer_name=diagnosis["fertilizer"]["name"],
        fertilizer_dosage=diagnosis["fertilizer"]["dosage"],
        fertilizer_schedule=diagnosis["fertilizer"]["schedule"],
    )
    db.session.add(scan)
    db.session.commit()

    return jsonify(scan.to_dict()), 201


@bp.route("/chat", methods=["POST"])
@login_required
def send_chat_message():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    session = (
        ChatSession.query.filter_by(user_id=current_user.id)
        .order_by(ChatSession.created_at.desc())
        .first()
    )
    if session is None:
        session = ChatSession(user_id=current_user.id)
        db.session.add(session)
        db.session.commit()

    history = [{"role": m.role, "text": m.text} for m in session.messages]

    user_msg = ChatMessage(session_id=session.id, role="user", text=message)
    db.session.add(user_msg)
    db.session.commit()

    try:
        reply_text = chat_reply(history, message)
    except LLMError as exc:
        current_app.logger.warning("Chat reply failed: %s", exc)
        return jsonify({"error": "AI Chat is temporarily unavailable. Please try again."}), 502

    model_msg = ChatMessage(session_id=session.id, role="model", text=reply_text)
    db.session.add(model_msg)
    db.session.commit()

    return jsonify({"reply": model_msg.to_dict()}), 201
