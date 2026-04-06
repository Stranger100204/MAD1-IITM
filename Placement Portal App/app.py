from flask import Flask
from application.database import db
from application.models import User


def create_app():
    app = Flask(__name__)

    # CONFIG
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///placement.sqlite3'
    app.secret_key = "mysecretkey123"

    # INIT DB
    db.init_app(app)

    # REGISTER BLUEPRINT
    from application.controllers import app as app_blueprint
    app.register_blueprint(app_blueprint)

    return app


# ✅ CREATE APP HERE (IMPORTANT)
app = create_app()


# RUN
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Create default admin
        admin = User.query.filter_by(role="admin").first()
        if admin is None:
            admin = User(
                username="admin",
                email="admin@portal.com",
                password="admin123",
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True)