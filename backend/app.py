import os
import hashlib
import secrets
from flask import jsonify
from flask_cors import CORS
from datetime import datetime
from datetime import timedelta
from dotenv import load_dotenv
from config import SessionLocal
from flask import Flask, request
from encryption import Encryptor
from flask import render_template
from contextlib import contextmanager
from sqlalchemy.orm import scoped_session
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required, get_jwt_identity
from twilio.twiml.messaging_response import MessagingResponse
from email_validator import validate_email, EmailNotValidError
from models import (
    ServiceStatus,
    EmailSubscription,
    SMSSubscription,
    ISPEndpoint,
    Superuser,
)

# Create a Flask application instance
app = Flask(__name__)
encryptor = Encryptor()
jwt = JWTManager(app)

load_dotenv()
SUPERUSER_NAME = os.getenv("SUPERUSER_NAME")
SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
DEFAULT_ISP_ENDPOINTS = ["216.75.112.220", "216.75.120.220"]

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


# Route to handle user login
@app.route("/api/login", methods=["POST"])
def login():
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    # Authenticate user
    with get_session() as session:
        user = session.query(Superuser).filter_by(username=username).first()
        if user and user.check_password(password):
            # Create JWT token
            expires = timedelta(days=1)  # Token expires in one day
            access_token = create_access_token(identity=username, expires_delta=expires)
            return jsonify(access_token=access_token), 200
        else:
            return jsonify({"msg": "Bad username or password"}), 401


# Route to get all ISP endpoints
@app.route("/api/isp_endpoints", methods=["GET"])
def get_isp_endpoints():
    with get_session() as session:
        # Fetch all ISP endpoints from the database
        endpoints = session.query(ISPEndpoint).all()
        # Extract the address from each endpoint
        isp_endpoints = [endpoint.address for endpoint in endpoints]
        return jsonify({"endpoints": isp_endpoints})


# Route to update ISP endpoints
@app.route("/api/isp_endpoints", methods=["POST"])
@jwt_required()
def update_isp_endpoints():
    # Get the identity of the current user from the JWT
    current_user_username = get_jwt_identity()

    # Optional: You can add additional checks here to confirm that the current user is a superuser
    with get_session() as session:
        user = (
            session.query(Superuser).filter_by(username=current_user_username).first()
        )
        if not user:
            return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    new_endpoints = data.get("endpoints")
    if not new_endpoints or not isinstance(new_endpoints, list):
        return jsonify({"message": "Bad Request. 'endpoints' must be a list."}), 400

    with get_session() as session:
        # Remove all current endpoints
        session.query(ISPEndpoint).delete()

        # Add new ISP endpoints
        for address in new_endpoints:
            new_endpoint = ISPEndpoint(address=address)
            session.add(new_endpoint)

        session.commit()

        return jsonify({"message": "ISP endpoints updated successfully"}), 200


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
            return (
                jsonify({"message": "You're already subscribed to notifications"}),
                409,
            )

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
        return (
            render_template(
                "message.html",
                message="Invalid unsubscribe request. Please check your link.",
            ),
            400,
        )

    with get_session() as session:
        # Find the subscription by its token
        subscription = session.query(EmailSubscription).filter_by(token=token).first()
        if not subscription:
            return (
                render_template(
                    "message.html",
                    message="Invalid unsubscribe link. Please try again with the correct link.",
                ),
                400,
            )

        # Remove the subscription and update the database
        session.delete(subscription)
        session.commit()

        return (
            render_template(
                "message.html", message="Successfully unsubscribed from notifications"
            ),
            200,
        )


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


def populate_default_isp_endpoints():
    with get_session() as session:
        # Check if any ISP endpoints already exist
        if session.query(ISPEndpoint).first() is None:
            # Add default endpoints
            for endpoint in DEFAULT_ISP_ENDPOINTS:
                new_endpoint = ISPEndpoint(address=endpoint)
                session.add(new_endpoint)
            session.commit()
            print("Default ISP endpoints added to the database.")
        else:
            print("ISP endpoints already exist in the database.")


def create_default_superuser():
    with get_session() as session:
        superuser_exists = (
            session.query(Superuser).filter_by(username=SUPERUSER_NAME).first()
            is not None
        )
        if not superuser_exists:
            superuser = Superuser(username=SUPERUSER_NAME)
            superuser.set_password(SUPERUSER_PASSWORD)
            session.add(superuser)
            session.commit()


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
create_default_superuser()
populate_default_isp_endpoints()

if __name__ == "__main__":
    app.run(debug=False, use_reloader=False)
