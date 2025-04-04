import sqlite3
import os
import datetime
import json
import smtplib
import ollama
import pickle
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from serpapi import GoogleSearch
from bs4 import BeautifulSoup


# Constants
DB_FILE = "data/emails.db"
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def load_credentials():
    try:
        with open(TOKEN_FILE, "rb") as token:
            return pickle.load(token)
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None

# Function to create a meeting event
def create_event(subject, description):
    creds = load_credentials()
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": subject,
        "description": description,
        "start": {"dateTime": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": (datetime.datetime.utcnow() + datetime.timedelta(days=1, hours=1)).isoformat(), "timeZone": "Asia/Kolkata"},
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Meeting Scheduled: {event.get('htmlLink')}")
    return event.get('htmlLink')

# Function to check if an email needs a web search
def needs_web_search(body):
    prompt = f"""
    Determine if this email requires web research.
    Reply only 'YES' or 'NO'.
    Email Body: {body[:500]}
    """
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}], options={"temperature": 0.1})
    return response["message"]["content"].strip().upper() == "YES"

def serpapi_search(query):
    if not SERPAPI_KEY:
        print("❌ SerpAPI Key is missing!")
        return []
    
    print(f"🔍 Searching SerpAPI for: {query}")

    try:
        search = GoogleSearch({"q": query, "api_key": SERPAPI_KEY})
        raw_results = search.get_results()

        if not raw_results:  # Agar response empty hai
            print("⚠️ No results found from SerpAPI!")
            return []

        results = json.loads(raw_results).get("organic_results", [])
        return [(result['title'], result['link']) for result in results[:3]]

    except json.decoder.JSONDecodeError:
        print("❌ JSON decoding error! Invalid SerpAPI response.")
        return []
    except Exception as e:
        print(f"❌ SerpAPI Error: {e}")
        return []
def extract_plain_text(html_body):
    try:
        soup = BeautifulSoup(html_body, "html.parser")
        return soup.get_text(separator=" ", strip=True)
    except Exception as e:
        print(f"⚠️ Failed to extract plain text: {e}")
        return html_body  # fallback
# Function to generate email replies
def generate_reply(subject, body, meeting_link=None):
    clean_body = extract_plain_text(body)

    if meeting_link:
        return f"Your meeting has been scheduled. Here is the link: {meeting_link}"
    elif needs_web_search(clean_body):
        search_results = serpapi_search(clean_body)
        return "Here are some relevant search results:\n" + "\n".join([f"- {title}: {link}" for title, link in search_results])
    else:
        return "I have reviewed your email and will get back to you shortly."
# Function to send emails
def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
    print("📩 Email sent successfully!")

# Main function to process emails
def auto_process_emails():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sender, subject, body FROM emails")
    emails = cursor.fetchall()

    for sender, subject, body in emails:
        if "meeting" in subject.lower() or "schedule" in body.lower():
            print(f"📅 Scheduling meeting for: {subject}")
            meeting_link = create_event(subject, body)
            email_reply = generate_reply(subject, body, meeting_link)
        else:
            email_reply = generate_reply(subject, body)
        
        send_email(sender, f"Re: {subject}", email_reply)
    
    conn.close()

if __name__ == "__main__":
    auto_process_emails()