from app.extensions import db
from app.models import User, DiagnosisScan


def test_password_hashing(app):
    with app.app_context():
        user = User(name="Test", email="hash@example.com", role="farmer")
        user.set_password("supersecret")
        assert user.password_hash != "supersecret"
        assert user.check_password("supersecret") is True
        assert user.check_password("wrong") is False


def test_diagnosis_scan_to_dict(app):
    with app.app_context():
        user = User(name="Test", email="scan@example.com", role="farmer")
        user.set_password("supersecret")
        db.session.add(user)
        db.session.commit()

        scan = DiagnosisScan(
            user_id=user.id,
            image_path="uploads/test.jpg",
            disease_name="Leaf Blight",
            severity="Medium",
            confidence=0.87,
            description="Some description",
            treatments=["Remove affected leaves", "Apply fungicide"],
            fertilizer_name="NPK 20-20-20",
            fertilizer_dosage="50g per plant",
            fertilizer_schedule="Every 2 weeks",
        )
        db.session.add(scan)
        db.session.commit()

        data = scan.to_dict()
        assert data["diseaseName"] == "Leaf Blight"
        assert data["severity"] == "Medium"
        assert data["fertilizer"]["name"] == "NPK 20-20-20"
        assert len(data["treatments"]) == 2


def test_user_scans_relationship_cascades(app):
    with app.app_context():
        user = User(name="Test", email="cascade@example.com", role="farmer")
        user.set_password("supersecret")
        db.session.add(user)
        db.session.commit()

        scan = DiagnosisScan(
            user_id=user.id, image_path="x.jpg", disease_name="X",
            severity="Low", confidence=0.5, description="d", treatments=[],
        )
        db.session.add(scan)
        db.session.commit()

        db.session.delete(user)
        db.session.commit()

        assert DiagnosisScan.query.count() == 0
