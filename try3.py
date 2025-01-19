import imaplib
import email
import os
import re
from PyPDF2 import PdfReader
import mysql.connector

# Email credentials
EMAIL = "harishasivakumar001@gmail.com"
PASSWORD = "xrwh sspv miud grpj"
IMAP_SERVER = "imap.gmail.com"
ALLOWED_EXTENSIONS = [".pdf", ".docx", ".doc"]

# Database credentials
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "Harisha#8"
DB_NAME = "haridb 1"

# Function to check if the file is a resume
def is_resume(filename):
    nameFile, ext = os.path.splitext(filename)
    return (ext.lower() in ALLOWED_EXTENSIONS) and ("resume" in nameFile.lower())

# Extract phone numbers and emails from text
def extract_phone_and_email(text):
    phone_pattern = r"\b\d{10}\b"
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    phone_numbers = re.findall(phone_pattern, text)
    emails = re.findall(email_pattern, text)
    return phone_numbers, emails

# Download resumes from email
def download_resumes(mail):
    mail.select("inbox")
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()[-10:]  # Fetch the last 10 emails
    email_ids.reverse()  # Process the newest emails first

    downloaded_files = []
    for email_id in email_ids:
        try:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_disposition() == "attachment":
                                filename = part.get_filename()
                                if filename and is_resume(filename):
                                    if not os.path.exists("downloads"):
                                        os.makedirs("downloads")
                                    filepath = os.path.join("downloads", filename)
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    downloaded_files.append(filepath)
        except Exception as e:
            print(f"Error processing email ID {email_id.decode()}: {e}")
    return downloaded_files

# Process resumes and insert data into the database
def process_resumes_and_insert_to_db(file_paths):
    try:
        db = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
        )
        cursor = db.cursor()

        for file_path in file_paths:
            try:
                print(f"Processing file: {file_path}")
                # Read PDF content
                reader = PdfReader(file_path)
                resume_content = ""
                for page in reader.pages:
                    resume_content += page.extract_text()
                
                # Extract phone numbers and emails
                phone_numbers, emails = extract_phone_and_email(resume_content)

                # Insert data into database
                for phone in phone_numbers:
                    for email in emails:
                        sql = "INSERT INTO resumetest (phonenumber, email) VALUES (%s, %s)"
                        values = (phone, email)
                        cursor.execute(sql, values)
                db.commit()
                print(f"Inserted data from {file_path} into database.")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

        cursor.close()
        db.close()
        print("Database connection closed.")
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")

if __name__ == "__main__":
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, timeout=10)
        mail.login(EMAIL, PASSWORD)
        print("Logged in to email successfully.\n")

        # Step 1: Download resumes
        downloaded_files = download_resumes(mail)
        if not downloaded_files:
            print("No resumes found.")
        else:
            print(f"Downloaded {len(downloaded_files)} resumes.")

            # Step 2: Process and insert into the database
            process_resumes_and_insert_to_db(downloaded_files)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        mail.logout()
        print("Logged out from email.")   