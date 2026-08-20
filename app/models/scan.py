from datetime import datetime, timezone
from app.extensions import db


class DiagnosisScan(db.Model):
    """Mirrors the frontend's DiagnosisResult shape (see types.ts) so the
    API can serialize a row straight into what the UI already expects."""

    __tablename__ = "diagnosis_scans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    image_path = db.Column(db.String(500), nullable=False)

    disease_name = db.Column(db.String(200), nullable=False)
    severity = db.Column(db.String(10), nullable=False)  # Low | Medium | High
    confidence = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)

    # Stored as JSON so we can keep the list-of-strings shape the UI wants
    treatments = db.Column(db.JSON, nullable=False, default=list)

    fertilizer_name = db.Column(db.String(200), nullable=True)
    fertilizer_dosage = db.Column(db.String(200), nullable=True)
    fertilizer_schedule = db.Column(db.String(200), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "diseaseName": self.disease_name,
            "severity": self.severity,
            "confidence": self.confidence,
            "description": self.description,
            "treatments": self.treatments or [],
            "fertilizer": {
                "name": self.fertilizer_name,
                "dosage": self.fertilizer_dosage,
                "schedule": self.fertilizer_schedule,
            },
            "imagePath": self.image_path,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
