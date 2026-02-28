import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///influencons.db')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    db.init_app(app)
    with app.app_context():
        # Migration automatique des colonnes manquantes
        from sqlalchemy import text
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE defis ADD COLUMN IF NOT EXISTS link VARCHAR(255)"))
                conn.execute(text("ALTER TABLE defis ADD COLUMN IF NOT EXISTS image_url VARCHAR(255)"))
                conn.execute(text("ALTER TABLE solidarite_action ADD COLUMN IF NOT EXISTS image_url VARCHAR(255)"))
                conn.commit()
        except Exception as e:
            print(f"Migration: {e}")
    
    return app
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.login_view = 'admin.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'

    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.main import main_bp
    from .routes.admin import admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()
        _create_admin()

    return app


def _create_admin():
    from .models import User
    from werkzeug.security import generate_password_hash
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@influencons.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
    if not User.query.filter_by(email=admin_email).first():
        admin = User(
            username='Evelyne',
            email=admin_email,
            password=generate_password_hash(admin_password),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
