import hashlib
import secrets
from flask import jsonify
from flask_cors import CORS
from datetime import datetime
from config import SessionLocal
from flask import Flask, request
from encryption import Encryptor
from contextlib import contextmanager
from sqlalchemy.orm import scoped_session
from twilio.twiml.messaging_response import MessagingResponse
from email_validator import validate_email, EmailNotValidError
from models import ServiceStatus, EmailSubscription, SMSSubscription

# Create a Flask application instance
app = Flask(__name__)
encryptor = Encryptor()

# Allow requests from any origin during development
CORS(app, resources={r"/api/*": {"origins": "*"}})


# Context manager for handling database sessions
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


# Route to get the current service status
@app.route("/api/status", methods=["GET"])
def get_status():
    with get_session() as session:
        service_status = session.query(ServiceStatus).first()

        # Default response if no status is found
        if service_status is None:
            response_data = {
                "message": "No status information available",
                "status_code": 500,
            }
        else:
            # Construct response message based on service status
            formatted_timestamp = service_status.updated_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            message_text = (
                f"✅ Allo is online! Last updated at {formatted_timestamp}"
                if service_status.status == "online"
                else f"⚠️ Allo is down! Last updated at {formatted_timestamp}"
            )
            response_data = {"message": message_text}

        return jsonify(response_data)


# Route to handle email subscription
@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    with get_session() as session:
        email = request.form["email"]

        try:
            # Validate the email address
            valid = validate_email(email)
            email = valid.email
            encrypted_email = encryptor.encrypt(email)

            # Create a unique hash of the email for identification
            email_hash = hashlib.sha256(email.encode()).hexdigest()
        except EmailNotValidError as e:
            return jsonify({"message": str(e)}), 400

        # Check for existing subscription
        existing_subscription = (
            session.query(EmailSubscription).filter_by(email_hash=email_hash).first()
        )
        if existing_subscription:
            return jsonify({"message": "You're already subscribed to notifications"}), 409

        # Create new subscription if not already subscribed
        token = secrets.token_urlsafe(16)
        subscription = EmailSubscription(
            token=token, encrypted_email=encrypted_email, email_hash=email_hash
        )
        session.add(subscription)
        session.commit()


        return jsonify({"message": "Successfully subscribed to notifications"}), 200


# Route to handle email unsubscription
@app.route("/api/unsubscribe", methods=["GET"])
def unsubscribe():
    token = request.args.get("token")
    if not token:
        return "Invalid unsubscribe request. Please check your link.", 400

    with get_session() as session:
        # Find the subscription by its token
        subscription = session.query(EmailSubscription).filter_by(token=token).first()
        if not subscription:
            return (
                "Invalid unsubscribe link. Please try again with the correct link.",
                400,
            )

        # Remove the subscription and update the database
        session.delete(subscription)
        session.commit()

        return jsonify({"message": "Successfully unsubscribed from notifications"}), 200


# Route to handle SMS replies and subscriptions
@app.route("/api/sms", methods=["POST"])
def sms_reply():
    """Respond to incoming messages with a friendly SMS."""
    body = request.values.get("Body", "").strip()
    from_number = request.values.get("From", "")

    resp = MessagingResponse()

    with get_session() as session:
        # Handle subscription via SMS
        if "SUBSCRIBE" in body.upper():
            phone_hash = hashlib.sha256(from_number.encode()).hexdigest()

            # Check for existing subscription
            existing_subscription = (
                session.query(SMSSubscription).filter_by(phone_hash=phone_hash).first()
            )
            if existing_subscription:
                resp.message("You're already subscribed to SMS alerts!")
            else:
                encrypted_phone = encryptor.encrypt(from_number)
                token = secrets.token_urlsafe(16)
                subscription = SMSSubscription(
                    token=token, encrypted_phone=encrypted_phone, phone_hash=phone_hash
                )
                session.add(subscription)
                session.commit()

                resp.message("Thank you for subscribing to SMS alerts!")

        # Handle unsubscription via SMS
        elif "UNSUBSCRIBE" in body.upper():
            phone_hash = hashlib.sha256(from_number.encode()).hexdigest()
            subscription = (
                session.query(SMSSubscription).filter_by(phone_hash=phone_hash).first()
            )

            if subscription:
                session.delete(subscription)
                session.commit()
                resp.message("You have been unsubscribed from SMS alerts.")
            else:
                resp.message("You were not subscribed.")

        else:
            # Default response for unrecognized commands
            resp.message(
                "Welcome to our service! Reply SUBSCRIBE to receive updates or UNSUBSCRIBE to stop."
            )

    return str(resp)


# Function to initialize the Flask application
def start_flask_app():
    # Create a scoped session
    session = scoped_session(SessionLocal)

    try:
        # Check and set initial service status
        service_status = session.query(ServiceStatus).first()

        if not service_status:
            new_status = ServiceStatus(status="online", updated_at=datetime.now())
            session.add(new_status)
            session.commit()
            print("Service status set to online")
        else:
            print("Service status already exists")

        # Additional Flask app startup code goes here...

    except Exception as e:
        print(f"Error setting service status: {e}")
        session.rollback()
    finally:
        session.remove()


# Start the Flask application
start_flask_app()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
