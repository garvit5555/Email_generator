import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

# Define the scope for sending email
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def authenticate_gmail():
    """Authenticate the user and obtain Gmail API service."""
    creds = None
    # Check for existing credentials file
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials, authenticate the user
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('api_file.json', SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_email(service, sender_email, receiver_email, subject, message_text):
    """Send an email using the Gmail API."""
    message = MIMEText(message_text)
    message['to'] = receiver_email
    message['from'] = sender_email
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f"Message sent successfully, message ID: {message['id']}")
    except HttpError as error:
        print(f"An error occurred: {error}")

# Authenticate and send an email
service = authenticate_gmail()
send_email(service, "user_email@gmail.com", "hr_email@example.com", "Subject Here", "Email body content")
