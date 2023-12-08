import os
import time
import boto3
import asyncio
from ping3 import ping

from datetime import datetime
from dotenv import load_dotenv
from config import SessionLocal
from encryption import Encryptor
from models import ServiceStatus, Subscription
from sqlalchemy.orm import scoped_session

load_dotenv()
encryptor = Encryptor()

# AWS SNS configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

# SES client
ses_client = boto3.client(
    "ses",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Global variable
previous_state = None

# isp_endpoints = ["216.75.112.220", "216.75.120.220"]
isp_endpoints = ["127.0.0.1:9999", "216.75.120.220"]


def generate_unsubscribe_link(token):
    base_url = "http://localhost:5000/unsubscribe"
    unsubscribe_link = f"{base_url}?token={token}"
    return unsubscribe_link


def send_email_notification(subject, message, recipients):
    """
    Sends email notifications using SES.
    """
    CHARSET = "UTF-8"
    session = scoped_session(SessionLocal)  # Create a scoped session

    try:
        # Fetch subscriber encrypted emails and tokens from the database
        subscribers = session.query(Subscription).all()

        for subscriber in subscribers:
            # Decrypt the email address
            decrypted_email = encryptor.decrypt(subscriber.encrypted_email)
            unsubscribe_token = subscriber.token
            unsubscribe_link = generate_unsubscribe_link(unsubscribe_token)

            full_message = (
                f"{message}\n\nTo unsubscribe, please click here: {unsubscribe_link}"
            )

            # Sending email via Amazon SES
            try:
                response = ses_client.send_email(
                    Destination={"ToAddresses": [decrypted_email]},
                    Message={
                        "Body": {"Text": {"Charset": CHARSET, "Data": full_message}},
                        "Subject": {"Charset": CHARSET, "Data": subject},
                    },
                    Source="alerts@allo.guru",  # Replace with your verified SES email
                )
            except Exception as e:
                print(f"Error sending email to {decrypted_email}: {e}")

    except Exception as e:
        print(f"Error fetching subscribers: {e}")
    finally:
        session.remove()  # Remove the session after operation


async def check_isp_and_publish():
    global previous_state
    current_state = True
    session = scoped_session(SessionLocal)  # Create a scoped session

    try:
        for endpoint in isp_endpoints:
            response = ping(endpoint)
            if response == False:
                current_state = False
                break

        if current_state != previous_state:
            formatted_timestamp = datetime.fromtimestamp(time.time()).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            subject = "ISP Status Update"
            message_text = (
                f"✅ Allo is online! {formatted_timestamp}"
                if current_state
                else f"⚠️ Allo is down! {formatted_timestamp}"
            )

            print(f"ISP state changed: {message_text}")

            # Update or create a new ServiceStatus entry
            service_status = session.query(ServiceStatus).first()
            if service_status:
                service_status.status = "online" if current_state else "offline"
                service_status.updated_at = datetime.now()
            else:
                new_status = ServiceStatus(
                    status="online" if current_state else "offline"
                )
                session.add(new_status)

            session.commit()

            # Fetch email addresses of subscribers from PostgreSQL
            recipients = session.query(Subscription).all()

            for recipient in recipients:
                decrypted_email = encryptor.decrypt(recipient.encrypted_email)
                recipient.email = decrypted_email

                if recipient.email:
                    send_email_notification(subject, message_text, [recipient.email])

            previous_state = current_state

    except Exception as e:
        print(f"Error checking ISP status: {e}")
        session.rollback()
    finally:
        session.remove()


async def main():
    while True:
        await asyncio.sleep(10)
        await check_isp_and_publish()


if __name__ == "__main__":
    asyncio.run(main())
