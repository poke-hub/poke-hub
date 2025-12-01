import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, session
from app.extensions import mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from core.configuration.configuration import get_app_version
from core.managers.config_manager import ConfigManager
from core.managers.error_handler_manager import ErrorHandlerManager
from core.managers.logging_manager import LoggingManager
from core.managers.module_manager import ModuleManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="development"):
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)
    app.config.from_object("core.configuration.configuration.Config")  


    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register modules
    module_manager = ModuleManager(app)
    module_manager.register_modules()

    try:
        from app.modules.fakenodo.routes import fakenodo_bp

        app.register_blueprint(fakenodo_bp, url_prefix="/api")
        app.logger.info("Fakenodo blueprint registered successfully at /api.")
    except ImportError:
        app.logger.warning("Fakenodo blueprint (app/fakenodo/routes.py) not found. Skipping registration.")

    # Register login manager
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.modules.auth.models import User, UserSession

        user = User.query.get(int(user_id))

        # Si no existe el usuario, retornamos None
        if not user:
            return None

        # Si estamos en medio del proceso de 2FA (antes de verificar código),
        # no validamos la sesión de base de datos todavía.
        if "2fa_user_id" in session:
            return None

        # Validamos la sesión específica del dispositivo
        current_session_token = session.get("app_session_token")
        if not current_session_token:
            return None  # No hay token de sesión, desconectar

        user_session = UserSession.query.filter_by(token=current_session_token).first()
        if not user_session:
            return None  # La sesión fue revocada remotamente, desconectar

        # Actualizamos la última vez visto (opcional: hacerlo con menos frecuencia para optimizar)
        user_session.last_seen = datetime.now(timezone.utc)
        db.session.commit()

        return user

    # Set up logging
    logging_manager = LoggingManager(app)
    logging_manager.setup_logging()

    # Initialize error handler manager
    error_handler_manager = ErrorHandlerManager(app)
    error_handler_manager.register_error_handlers()

    # Injecting environment variables into jinja context
    @app.context_processor
    def inject_vars_into_jinja():
        return {
            "FLASK_APP_NAME": os.getenv("FLASK_APP_NAME"),
            "FLASK_ENV": os.getenv("FLASK_ENV"),
            "DOMAIN": os.getenv("DOMAIN", "localhost"),
            "APP_VERSION": get_app_version(),
        }

    return app


app = create_app()
