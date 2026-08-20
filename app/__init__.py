import os
from flask import Flask

from config import Config
from app.extensions import db, login_manager, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    from app import errors
    errors.register(app)

    # Dev convenience: if the configured database has no tables yet (most
    # commonly because `flask db init/migrate/upgrade` was never run after
    # a fresh clone), create them automatically instead of 500ing on the
    # first register/login/scan/chat request. This is safe to run every
    # startup — SQLAlchemy's create_all() only creates tables that don't
    # already exist and never touches ones that do. Once you're managing
    # schema changes with Flask-Migrate in production, this is a no-op.
    with app.app_context():
        try:
            db.create_all()
        except Exception:
            app.logger.exception(
                "Could not verify/create database tables on startup. "
                "Check DATABASE_URL in your .env and that the DB server is reachable."
            )

    return app
