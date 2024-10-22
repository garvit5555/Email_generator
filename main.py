import os
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_community.document_loaders import WebBaseLoader
from chains import Chain
from portfolio import Portfolio
from utils import clean_text

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
    gmail_password = st.text_input("Your Gmail password", type="password")

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

    if submit_button and gmail_user and gmail_password:
        try:
            # Load job data
            loader = WebBaseLoader([url_input])
            data = clean_text(loader.load().pop().page_content)
            portfolio.load_portfolio()
            jobs = llm.extract_jobs(data)

            # Generate emails for each job
            st.session_state["generated_emails"] = []  # Clear previous emails
            for index, job in enumerate(jobs):
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
    if st.session_state["generated_emails"] and gmail_user and gmail_password:
        recipient_email = st.text_input("Recipient's Email Address", "")
        selected_email_index = st.selectbox(
            "Select the generated email to send",
            options=range(len(st.session_state["generated_emails"])),
            format_func=lambda x: f"Generated Email {x + 1}"
        )

        # Send Email button
        send_button = st.button("Send Email ✉️")

        if send_button and recipient_email:
            try:
                # Select the email content to send
                selected_email = st.session_state["generated_emails"][selected_email_index]

                # Create email content
                msg = MIMEMultipart()
                msg['From'] = gmail_user
                msg['To'] = recipient_email
                msg['Subject'] = "Job Application"

                # Attach email content
                msg.attach(MIMEText(selected_email, 'plain'))

                # Send email using SMTP
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(gmail_user, gmail_password)
                    server.sendmail(gmail_user, recipient_email, msg.as_string())

                st.success(f"Email successfully sent to {recipient_email}!")

            except Exception as e:
                st.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    api_key = os.getenv("GROQ_API_KEY")  # Provide your API key here
    chain = Chain(api_key)
    portfolio = Portfolio()
    create_streamlit_app(chain, portfolio, clean_text)
