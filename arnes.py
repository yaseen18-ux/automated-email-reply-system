import os
import time
import ssl
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Auto-reply message
AUTO_REPLY_SUBJECT = "AR:"
AUTO_REPLY_BODY = "Thank you for reaching out. I will get back to you soon."

# List of emails to ignore
IGNORED_SENDERS = ["no-reply", "donotreply"]

def check_emails():
    """Check new emails and send auto-replies."""
    try:
        context = ssl.create_default_context()
        with imaplib.IMAP4_SSL(IMAP_SERVER, ssl_context=context) as imap:
            imap.login(EMAIL, PASSWORD)
            imap.select("inbox")

            # Search for unseen emails
            status, messages = imap.search(None, '(UNSEEN)')
            email_ids = messages[0].split()

            for mail_id in email_ids:
                status, msg_data = imap.fetch(mail_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        sender = email.utils.parseaddr(msg["From"])[1]

                        # Avoid replying to ignored senders
                        if any(ignore in sender.lower() for ignore in IGNORED_SENDERS):
                            print(f"Skipping auto-reply to {sender}")
                            continue

                        # Avoid replying to yourself
                        if sender.lower() != EMAIL.lower():
                            send_auto_reply(sender, msg["Subject"])

                # Mark email as seen
                imap.store(mail_id, '+FLAGS', '\\Seen')

    except Exception as e:
        print(f"Error checking emails: {e}")

def send_auto_reply(to_address, original_subject):
    """Send an auto-reply to the sender."""
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)

            reply = MIMEText(AUTO_REPLY_BODY)
            reply["Subject"] = AUTO_REPLY_SUBJECT + " " + original_subject
            reply["From"] = EMAIL
            reply["To"] = to_address

            server.sendmail(EMAIL, to_address, reply.as_string())
            print(f"Auto-reply sent to {to_address}")

    except Exception as e:
        print(f"Error sending auto-reply to {to_address}: {e}")

# Run the script in an infinite loop with error handling
while True:
    try:
        check_emails()
        time.sleep(60)  # Wait 1 minute before checking again
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
        break
    except Exception as e:
        print(f"Unexpected error: {e}")
