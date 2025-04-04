import pickle
import os
import sqlite3
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode
from datetime import datetime

#  Load Gmail API credentials
TOKEN_FILE = "token.pickle"
if not os.path.exists(TOKEN_FILE):
    print("⚠️ Authentication token not found! Please authenticate with Gmail first.")
    exit()

with open(TOKEN_FILE, "rb") as token:
    creds = pickle.load(token)

#  Connect to Gmail API
service = build("gmail", "v1", credentials=creds)

#  Fetch last 3 emails from Primary inbox
query = "category:primary"
results = service.users().messages().list(userId="me", q=query, maxResults=3).execute()
messages = results.get("messages", [])

# Connect to SQLite database
DB_PATH = "data/emails.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

for message in messages:
    msg_id = message["id"]
    msg_data = service.users().messages().get(userId="me", id=msg_id).execute()
    
    headers = msg_data["payload"]["headers"]
    sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")
    recipients = next((h["value"] for h in headers if h["name"] == "To"), "Unknown")
    subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
    timestamp = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown")

    # Ignore no-reply emails
    if "no-reply" in sender.lower():
        print(f"🚫 Ignoring no-reply email: {subject}")
        continue

    # Extract body (handles both text and HTML emails)
    body = ""
    if "parts" in msg_data["payload"]:
        for part in msg_data["payload"]["parts"]:
            if part["mimeType"] == "text/plain":
                body = urlsafe_b64decode(part["body"]["data"]).decode()
                break
    else:
        body = urlsafe_b64decode(msg_data["payload"]["body"]["data"]).decode()

    #  Convert timestamp to standard format
    try:
        parsed_time = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %z")
        formatted_time = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        formatted_time = "Unknown"

    #  Store email in database
    cursor.execute(
        "INSERT INTO emails (sender, recipient, subject, body, timestamp, priority) VALUES (?, ?, ?, ?, ?, ?)",
        (sender, recipients, subject, body, formatted_time, "Unclassified"),
    )
    conn.commit()
    print(f" Email from {sender} stored successfully!")

#  Cleanup
conn.close()
print(" Last 3 primary emails processed!")