import secrets
from config import SessionLocal
from flask import Flask, request
from encryption import Encryptor
from contextlib import contextmanager
from models import ServiceStatus, Subscription
from email_validator import validate_email, EmailNotValidError

app = Flask(__name__)
encryptor = Encryptor()


@contextmanager
def get_session():
    """Context manager for SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


@app.route("/status", methods=["GET"])
def get_status():
    with get_session() as session:
        service_status = session.query(ServiceStatus).first()

        if service_status is None:
            return "No status information available", 500

        # Format the 'updated_at' timestamp from the database
        formatted_timestamp = service_status.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        message_text = (
            f"✅ Allo is online! Last updated at {formatted_timestamp}"
            if service_status.status == 'online'
            else f"⚠️ Allo is down! Last updated at {formatted_timestamp}"
        )

        return message_text, 200


@app.route("/subscribe", methods=["POST"])
def subscribe():
    with get_session() as session:
        email = request.form["email"]

        try:
            valid = validate_email(email)
            email = valid.email
            encrypted_email = encryptor.encrypt(email)  # Encrypt the email
        except EmailNotValidError as e:
            return str(e), 400

        token = secrets.token_urlsafe(16)
        subscription = Subscription(token=token, encrypted_email=encrypted_email)
        session.add(subscription)
        session.commit()

        return "Successfully subscribed to notifications.", 200


@app.route("/unsubscribe", methods=["GET"])
def unsubscribe():
    token = request.args.get("token")
    if not token:
        return "Invalid unsubscribe request. Please check your link.", 400

    with get_session() as session:
        subscription = session.query(Subscription).filter_by(token=token).first()
        if not subscription:
            return (
                "Invalid unsubscribe link. Please try again with the correct link.",
                400,
            )

        session.delete(subscription)
        session.commit()

        return "You have been successfully unsubscribed.", 200


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
