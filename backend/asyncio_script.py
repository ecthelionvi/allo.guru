import os
import boto3
import aiohttp
import asyncio
from ping3 import ping
from datetime import datetime
from twilio.rest import Client
from dotenv import load_dotenv
from config import SessionLocal
from encryption import Encryptor
from sqlalchemy.orm import scoped_session
from models import ServiceStatus, EmailSubscription, SMSSubscription

# Load environment variables from a .env file
load_dotenv()
encryptor = Encryptor()

# AWS Simple Notification Service (SNS) configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN")

# Twilio configuration for sending SMS
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# AWS Simple Email Service (SES) client configuration
ses_client = boto3.client(
    "ses",
    region_name="us-east-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Variable to store the previous state of the ISP
previous_state = None

def send_sms_notification(message, recipients):
    """
    Sends SMS notifications using Twilio.
    """
    for recipient in recipients:
        decrypted_phone = None
        try:
            decrypted_phone = encryptor.decrypt(recipient.encrypted_phone)
            twilio_client.messages.create(
                body=message, from_=TWILIO_PHONE_NUMBER, to=decrypted_phone
            )
        except Exception as e:
            print(f"Error sending SMS: {e}, to {decrypted_phone}")


def generate_unsubscribe_link(token):
    """
    Generates an unsubscribe link for email notifications.
    """
    base_url = "http://www.allo.guru/api/unsubscribe"
    unsubscribe_link = f"{base_url}?token={token}"
    return unsubscribe_link


def send_email_notification(subject, message, recipients):
    """
    Sends email notifications using Amazon SES.
    """
    CHARSET = "UTF-8"
    session = scoped_session(SessionLocal)

    try:
        subscribers = session.query(EmailSubscription).all()

        for subscriber in subscribers:
            decrypted_email = encryptor.decrypt(subscriber.encrypted_email)
            unsubscribe_token = subscriber.token
            unsubscribe_link = generate_unsubscribe_link(unsubscribe_token)

            full_message = (
                f"{message}\n\nTo unsubscribe, please click here: {unsubscribe_link}"
            )

            try:
                ses_client.send_email(
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
        session.remove()


async def fetch_isp_endpoints(api_url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get(
                        "endpoints", []
                    )  # Assuming the API returns a JSON with an 'endpoints' key
                else:
                    print(
                        f"Failed to fetch ISP endpoints. Status code: {response.status}"
                    )
                    return None
        except Exception as e:
            print(f"Error fetching ISP endpoints: {e}")
            return None


async def check_isp_and_publish(api_url):
    """
    Checks the status of ISP endpoints and publishes updates.
    """
    global previous_state
    current_state = True

    session = scoped_session(SessionLocal)

    try:
        new_endpoints = await fetch_isp_endpoints(api_url)
        if new_endpoints:
            for endpoint in new_endpoints:
                if not ping(endpoint):
                    current_state = False
                    break

        if current_state != previous_state:
            formatted_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            subject = "ISP Status Update"
            message_text = (
                f"✅ Allo is online! {formatted_timestamp}"
                if current_state
                else f"⚠️ Allo is down! {formatted_timestamp}"
            )

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

            email_recipients = session.query(EmailSubscription).all()
            send_email_notification(subject, message_text, email_recipients)

            sms_recipients = session.query(SMSSubscription).all()
            for recipient in sms_recipients:
                send_sms_notification(message_text, [recipient])

            previous_state = current_state

    except Exception as e:
        print(f"Error checking ISP status: {e}")
        session.rollback()
    finally:
        session.remove()


async def main(api_url):
    """
    The main function to run the ISP check loop.
    """
    while True:
        await asyncio.sleep(30)  # Wait for 10 seconds before next check
        await check_isp_and_publish(api_url)
        print("Checked ISP status")


if __name__ == "__main__":
    api_url = "https://allo.guru/api/isp_endpoints"
    asyncio.run(main(api_url))
