"""
LLM service abstraction.

Routes and other app code should only ever call the functions in this
module (analyze_crop_image, chat_reply) — never talk to a provider's SDK
directly. That keeps the provider swappable via the LLM_PROVIDER env var
without touching any route code.

Currently wired:
  - "gemini": Google Gemini via google-generativeai. Free tier covers both
    multimodal image analysis (crop photos) and text chat. This is the
    provider the original app (@google/genai) was already built around.

To add another provider (e.g. Groq, OpenRouter), implement the same two
function signatures in a sibling module and branch on LLM_PROVIDER below.
Note: not all free-tier chat models support vision, so a non-Gemini
provider may only be able to power the Chat feature, not Crop Doctor,
unless the model you pick is explicitly multimodal.
"""
import json
import re
from flask import current_app

_SEVERITIES = {"Low", "Medium", "High"}

DIAGNOSIS_PROMPT = """You are an expert agricultural plant pathologist. Analyze the attached
leaf/crop photo and respond with ONLY a single JSON object (no markdown fences, no prose)
matching exactly this shape:

{
  "diseaseName": string,
  "severity": "Low" | "Medium" | "High",
  "confidence": number between 0 and 1,
  "description": string (2-3 sentences explaining what you see and why),
  "treatments": [string, string, ...] (3-5 concrete actionable treatment steps),
  "fertilizer": {
    "name": string (a specific fertilizer or nutrient product/type),
    "dosage": string (e.g. "50g per plant" or "10ml/L water"),
    "schedule": string (e.g. "Every 2 weeks for 6 weeks")
  }
}

If the plant looks healthy, still return this shape with diseaseName like
"No Disease Detected", severity "Low", and preventative treatments/fertilizer advice."""

CHAT_SYSTEM_PROMPT = """You are Agri-Chat, AgroVision's AI farming assistant. You help farmers
with crop health, fertilizer planning, irrigation, pest management, and general agricultural
advice. Keep answers practical, concise, and farmer-friendly. If a question is unrelated to
farming, gently steer the conversation back."""


class LLMError(RuntimeError):
    """Raised when the configured provider fails or is misconfigured."""


def _get_provider():
    provider = (current_app.config.get("LLM_PROVIDER") or "gemini").lower()
    if provider != "gemini":
        raise LLMError(
            f"LLM_PROVIDER='{provider}' is not implemented yet. "
            "Only 'gemini' is fully wired in this build. See app/services/llm_service.py."
        )
    return provider


def _gemini_client():
    import google.generativeai as genai

    api_key = current_app.config.get("LLM_API_KEY")
    if not api_key:
        raise LLMError("LLM_API_KEY is not set. Add it to your .env file.")
    genai.configure(api_key=api_key)
    model_name = current_app.config.get("LLM_MODEL", "gemini-1.5-flash")
    return genai, genai.GenerativeModel(model_name)


def _extract_json(raw_text: str) -> dict:
    """Gemini sometimes wraps JSON in markdown fences despite instructions —
    strip those before parsing."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return json.loads(cleaned)


def analyze_crop_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """Send a crop photo to the LLM and return a dict matching the
    frontend's DiagnosisResult shape (diseaseName, severity, confidence,
    description, treatments, fertilizer)."""
    _get_provider()
    genai, model = _gemini_client()

    try:
        response = model.generate_content(
            [
                DIAGNOSIS_PROMPT,
                {"mime_type": mime_type, "data": image_bytes},
            ]
        )
        result = _extract_json(response.text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Model returned non-JSON output: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surface any SDK/network error uniformly
        raise LLMError(f"Gemini request failed: {exc}") from exc

    # Defensive normalization so a slightly-off model response never 500s the route.
    result.setdefault("diseaseName", "Unknown")
    if result.get("severity") not in _SEVERITIES:
        result["severity"] = "Medium"
    try:
        result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
    except (TypeError, ValueError):
        result["confidence"] = 0.5
    result.setdefault("description", "")
    result.setdefault("treatments", [])
    fert = result.get("fertilizer") or {}
    result["fertilizer"] = {
        "name": fert.get("name", ""),
        "dosage": fert.get("dosage", ""),
        "schedule": fert.get("schedule", ""),
    }
    return result


def chat_reply(history: list[dict], message: str) -> str:
    """history: list of {"role": "user"|"model", "text": str}, oldest first.
    Returns the assistant's reply text."""
    _get_provider()
    genai, model = _gemini_client()

    gemini_history = [
        {"role": turn["role"], "parts": [turn["text"]]} for turn in history
    ]

    try:
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(f"{CHAT_SYSTEM_PROMPT}\n\nFarmer: {message}")
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"Gemini chat request failed: {exc}") from exc
