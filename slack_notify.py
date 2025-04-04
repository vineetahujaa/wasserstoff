import sqlite3
import requests
import ollama
import os
from dotenv import load_dotenv
load_dotenv()
from google.auth.transport.requests import Request

# 🔹 Slack Bot Token (Replace with your own)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = "all-new-workspace"  # Change to your target channel or @username for DM

def extract_priority_email(subject, body):
    
    prompt = f"""
    Identify if this email is important for urgent attention.
    Reply only 'YES' or 'NO'.

    Subject: {subject}
    Body: {body[:500]}
    """
    try:
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}], options={"temperature": 0.1})
        return response["message"]["content"].strip().upper() == "YES"
    except Exception as e:
        print(f"⚠️ LLM Error: {str(e)}")
        return False

def extract_priority_email(subject, body):
    
    # ✅ Ignore certain types of emails
    IGNORED_KEYWORDS = ["confirmation", "verify", "newsletter", "promotion", "receipt", "no-reply", "click this link"]
    subject_lower = subject.lower()

    if any(keyword in subject_lower for keyword in IGNORED_KEYWORDS):
        print(f"🚫 Ignored Email: {subject}")
        return False  # Not important

    # ✅ Improved LLM prompt
    prompt = f"""
    You are an AI assistant classifying emails.
    
    Mark an email as *important* ONLY IF:
    - It is related to meetings, deadlines, urgent work tasks.
    - It contains action items requiring user response.
    - It is sent by a known colleague or organization.

    DO NOT mark newsletters, promotions, verification emails, or general updates as important.

    Respond ONLY with 'YES' or 'NO'.

    **Subject:** {subject}
    **Body:** {body[:500]}
    """

    try:
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}], options={"temperature": 0.1})
        decision = response["message"]["content"].strip().upper()

        return decision == "YES"
    except Exception as e:
        print(f"⚠️ LLM Error: {str(e)}")
        return False

def send_slack_notification(subject, body):
   
    message = f"📩 *New Important Email*\n\n*Subject:* {subject}\n*Body:* {body[:300]}...\n🔗 Check your email."
    
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {SLACK_BOT_TOKEN}", "Content-Type": "application/json"}
    payload = {"channel": SLACK_CHANNEL, "text": message}

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200 and response.json().get("ok"):
        print(f"✅ Slack Notification Sent: {subject}")
    else:
        print(f"❌ Slack Error: {response.json()}")

def check_and_notify_emails():
    
    conn = sqlite3.connect("data/emails.db")
    cursor = conn.cursor()

    cursor.execute("SELECT subject, body FROM emails")
    emails = cursor.fetchall()

    for subject, body in emails:
        if extract_priority_email(subject, body):  
            send_slack_notification(subject, body)

    conn.close()

if __name__ == "__main__":
    check_and_notify_emails()