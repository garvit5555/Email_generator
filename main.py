import os
import streamlit as st
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

# Define the Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Function to authenticate Gmail
def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file('api_file.json', SCOPES)
        # Specify your redirect URI here
        flow.redirect_uri = 'http://localhost:8501/'  # Change 'your_port' to your desired port
        
        # Get the authorization URL and print it
        auth_url, _ = flow.authorization_url(access_type='offline')
        print(f"Please go to this URL and authorize the application: {auth_url}")

        creds = flow.run_local_server(port=8501)
        try:
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("Token saved to token.json")
        except Exception as e:
            print(f"Failed to save token: {e}")
    
    return build('gmail', 'v1', credentials=creds)

# Function to send email using Gmail API
def send_email(service, sender_email, receiver_email, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = receiver_email
    message['from'] = sender_email
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent_message = service.users().messages().send(userId="me", body={'raw': raw_message}).execute()
        print(f"Message ID: {sent_message['id']}")  # Print the message ID to verify
        return f"Message sent successfully, message ID: {sent_message['id']}"
    except HttpError as error:
        print(f"An error occurred: {error}")  # Detailed error information
        return f"An error occurred: {error}"


def create_streamlit_app(llm, portfolio, clean_text):
    # Set the page configuration
    st.set_page_config(
        layout="wide", 
        page_title="Job Application Magic", 
        page_icon="✨"
    )

    # Add a title and introductory text
    st.title("✨ Job Application Magic: AI-Powered Email Creator")
    st.markdown(
        """
        ### Welcome to Job Application Magic!
        Turn job descriptions into personalized application emails with ease.
        """
    )

    # Sidebar instructions
    with st.sidebar:
        st.header("Instructions")
        st.write(
            """
            1. Enter the job URL.
            2. Enter a custom prompt for the email instruction.
            3. Click "Submit" to generate the emails.
            4. Provide the recipient's Gmail address.
            5. Select the email to send and click "Send Email."
            """
        )

    # Input section for the URL
    url_input = st.text_input(
        "🔗 Enter a Job URL:",
        value="",
        help="Provide the URL of the job you are interested in."
    )

    # Gmail credentials
    gmail_user = st.text_input("Your Gmail address", "")
    st.write("You will authenticate with Google to send emails.")

    # Input for custom email prompt
    custom_email_prompt_instruction = st.text_area(
        "✍️ Custom Email Instruction Prompt:",
        value="Your job is to write a cold email to the company regarding the job mentioned above, describing your capability in fulfilling their needs.",
        help="Provide the instruction for writing the email."
    )

    # Submit button to trigger the email generation
    submit_button = st.button("Generate Emails 📝")

    # Use a session state to store the generated emails
    if "generated_emails" not in st.session_state:
        st.session_state["generated_emails"] = []

    if submit_button:
        try:
            # Load job data
            loader = WebBaseLoader([url_input])
            data = clean_text(loader.load().pop().page_content)
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)

            # Generate emails for each job
            max_emails = 10  # Limit the number of emails to generate
            st.session_state["generated_emails"] = []  # Clear previous emails
            for index, job in enumerate(jobs):
                if index >= max_emails:  # Stop if we've generated 10 emails
                    break
                
                skills = job.get('skills', [])
                links = portfolio.query_links(skills)
                email_content = llm.write_mail(job, links, custom_email_prompt_instruction)

                # Store the generated email
                st.session_state["generated_emails"].append(email_content)

                # Display generated emails
                st.subheader(f"Generated Email {index + 1}")
                st.code(email_content, language='markdown')

        except Exception as e:
            st.error(f"An Error Occurred: {e}")

    # Email sending section
    if st.session_state["generated_emails"]:
        recipient_email = st.text_input("Recipient's Email Address", "")
        selected_email_index = st.selectbox(
            "Select the generated email to send",
            options=range(len(st.session_state["generated_emails"])),
            format_func=lambda x: f"Generated Email {x + 1}"
        )

        # Authenticate and send Email button
        send_button = st.button("Send Email ✉️")

        if send_button and recipient_email:
            try:
                # Authenticate Gmail service
                service = authenticate_gmail()

                # Select the email content to send
                selected_email = st.session_state["generated_emails"][selected_email_index]
                print(f"this is the selected email: {selected_email}")
                # Send the email using the Gmail API
                response = send_email(service, gmail_user, recipient_email, "Job Application", selected_email)
                
                st.success(response)
                print("done", response)

            except Exception as e:
                st.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    api_key = "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"
    chain = Chain(api_key)
    portfolio = Portfolio()
    create_streamlit_app(chain, portfolio, clean_text)
