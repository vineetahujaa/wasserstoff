import sqlite3
import datetime
import pickle
from googleapiclient.discovery import build
import ollama
from google.auth.transport.requests import Request
from dateutil import parser, relativedelta
import pytz  # ✅ Timezone Handling

# Token file path
TOKEN_FILE = "token.pickle"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# ✅ IST Timezone
IST = pytz.timezone("Asia/Kolkata")

# Initialize Google Calendar API
def get_calendar_service():
    creds = None
    if TOKEN_FILE:
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("⚠️ Authentication Error: Please re-authenticate using OAuth.")

    return build("calendar", "v3", credentials=creds)

service = get_calendar_service()

def extract_meeting_details(subject, body):
    """Use LLM to extract a meeting's date and time from an email."""
    today = datetime.datetime.today()

    prompt = f"""
    Your task is to extract the exact **meeting date and time** from an email.

    🔹 If the email says "tomorrow", assume the date is **"{(today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}"**.
    🔹 If it says "next Monday" or "Monday at 3 PM", convert it to an exact date and time.
    🔹 If it only says "at 10 AM", assume it's **today's date** at 10 AM.
    🔹 Ensure the output is in **YYYY-MM-DD HH:MM** format.
    
    **Email Details:**  
    📨 Subject: {subject}  
    📝 Body: {body[:500]}  

    **Response Format:**  
    - If a meeting is found, respond:  
      **YES | YYYY-MM-DD HH:MM**  
    - If no date or time is found, respond:  
      **NO**
    """

    try:
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}], options={"temperature": 0.1})
        result = response["message"]["content"].strip()

        print(f"🔎 LLM Response: {result}")  # ✅ DEBUGGING: Print raw response

        if result.startswith("YES |"):
            date_str = result.split(" | ")[1].strip()

            try:
                # ✅ Parse extracted date
                meeting_date = parser.parse(date_str)

                # ✅ Convert to IST
                meeting_date = IST.localize(meeting_date)

                # ✅ Convert to UTC before saving to Google Calendar
                meeting_date_utc = meeting_date.astimezone(pytz.UTC)

                return meeting_date_utc
            except ValueError:
                print(f"❌ Error parsing date: {date_str}")
                return None
        return None
    except Exception as e:
        print(f"⚠️ LLM Error: {str(e)}")
        return None

def create_event(subject, description, event_time):
    """Create an event in Google Calendar at the extracted time."""
    event = {
        "summary": subject,
        "description": description,
        "start": {
            "dateTime": event_time.isoformat(),  # ✅ Now UTC
            "timeZone": "UTC",  # ✅ Store in UTC
        },
        "end": {
            "dateTime": (event_time + datetime.timedelta(hours=1)).isoformat(),  # 1-hour slot
            "timeZone": "UTC",  # ✅ Store in UTC
        },
    }

    event = service.events().insert(calendarId="primary", body=event).execute()
    print(f"✅ Meeting Scheduled at {event_time.astimezone(IST)} IST: {event.get('htmlLink')}")

def auto_schedule_meeting():
    """Fetch important emails from the database and schedule meetings if needed."""
    conn = sqlite3.connect("data/emails.db")
    cursor = conn.cursor()

    # ✅ Check if the "emails" table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emails'")
    if not cursor.fetchone():
        print("❌ Error: 'emails' table does not exist.")
        return

    # ✅ Now Fetch Emails Safely
    cursor.execute("SELECT subject, body, category, priority FROM emails")
    emails = cursor.fetchall()

    for subject, body, category, priority in emails:
        print(f"\n📩 Checking Email: {subject}")  # ✅ Debugging Email Subject
        print(f"📝 Email Body: {body[:200]}...")  # ✅ Debugging Email Body (First 200 chars)

        event_time = extract_meeting_details(subject, body)  # Extract meeting date-time using LLM

        if event_time:
            print(f"📅 Scheduling meeting for: {subject} at {event_time.astimezone(IST)} IST")
            create_event(subject, body, event_time)

    conn.close()

if __name__ == "__main__":
    auto_schedule_meeting()