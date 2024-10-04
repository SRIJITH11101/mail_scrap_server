from flask import Flask
import imaplib
import email
import re
import firebase_admin
from firebase_admin import credentials, firestore


app = Flask(__name__)

def update_firestore_with_email_data():
# Email credentials and server details
    EMAIL = "cybersparkz95@gmail.com"
    PASSWORD = "vpkt knek xmza khxc"  # Replace with your App Password
    IMAP_SERVER = "imap.gmail.com"

    # Firebase credentials and initialization
    cred = credentials.Certificate("GOOGLE_APPLICATION_CREDENTIALS") #canaryipcollect-firebase-adminsdk-xdipe-74bce1e107.json
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    # Connect to the IMAP server and select the mailbox
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select('inbox')

    # Search for emails from a specific sender
    result, data = mail.search(None, 'FROM', '"noreply@canarytokens.org"')

    # Extract email ids
    email_ids = data[0].split()

    # Function to extract details from the email body
    def extract_details(email_body):
        # Adjusted regex patterns based on the email content format you shared
        date = re.search(r'time_ymd:\s+(\d{4}/\d{2}/\d{2})', email_body).group(1)
        time = re.search(r'time_hm:\s+(\d{2}:\d{2})', email_body).group(1)
        source_ip = re.search(r"'ip':\s*'(\d+\.\d+\.\d+\.\d+)'", email_body).group(1)
        user_agent = re.search(r'useragent:\s+([^\n]+)', email_body).group(1).strip()
        return date, time, source_ip, user_agent

    # Loop through each email, extract data, and print it
    for email_id in email_ids:
        result, msg_data = mail.fetch(email_id, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                date, time, source_ip, user_agent = extract_details(body)
                
                # Prepare data for Firestore
                data = {
                    'Date': date,
                    'Time': time,
                    'Source IP': source_ip,
                    'User Agent': user_agent
                }
                
                doc_ref = db.collection('email_data').document(email_id.decode('utf-8'))
                doc = doc_ref.get()

                if not doc.exists:
                    doc_ref.set(data)
                    print(f"Saved data to Firestore: {data}")
                    print("-" * 40)
                else:
                    print(f"Document already exists for {email_id}. Skipping...")

    # Logout from the email server
    mail.logout()


@app.route('/run-script', methods=['POST'])
def run_script():
    update_firestore_with_email_data()  # Run the email scraping and Firestore update function
    return "Data updated successfully", 200

if __name__ == '__main__':
    app.run()