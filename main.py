import subprocess
import time
import schedule

# Step 0: Authenticate with Gmail API
def authenticate():
    print("🔐 Authenticating Gmail API...")
    subprocess.run(["python", "auth.py"])

# Step 0.1: Initialize Database (if not already initialized)
def initialize_database():
    print("📊 Initializing database...")
    subprocess.run(["python", "database.py"])

# Step 1: Fetch emails from Gmail
def fetch_emails():
    print("📩 Fetching emails...")
    subprocess.run(["python", "email_read.py"])

# Step 2: Categorize emails
def categorize_emails():
    print("📂 Categorizing emails...")
    subprocess.run(["python", "categorizer.py"])

# Step 3: Summarize emails
def summarize_emails():
    print("📝 Summarizing emails...")
    subprocess.run(["python", "summarizer.py"])

# Step 4: Determine priority
def prioritize_emails():
    print("🚦 Assigning priority...")
    subprocess.run(["python", "priority.py"])

# Step 5: Generate automatic replies
def generate_replies():
    print("✍️ Generating replies...")
    subprocess.run(["python", "auto_reply.py"])

# Step 6: Schedule important emails in Calendar
def schedule_events():
    print("📅 Scheduling calendar events...")
    subprocess.run(["python", "calendar_scheduler.py"])

# Step 7: Notify on Slack
def send_notifications():
    print("🔔 Sending Slack notifications...")
    subprocess.run(["python", "slack_notify.py"])

# Step 8: Perform web search for context
def web_search():
    print("🔎 Searching the web for context...")
    subprocess.run(["python", "web_search.py"])

# Step 9: Full automation sequence
def run_full_automation():
    authenticate()  # Ensure authentication before anything else
    initialize_database()  # Ensure database is set up
    fetch_emails()
    categorize_emails()
    summarize_emails()
    prioritize_emails()
    generate_replies()
    schedule_events()
    send_notifications()
    web_search()
    print("AI Email Assistant Automation Complete!")

# Step 10: Automate execution every 30 minutes
def start_scheduler():
    schedule.every(30).minutes.do(run_full_automation)
    print("⏳ AI Email Assistant will run every 30 minutes...")
    while True:
        schedule.run_pending()
        time.sleep(60)

# CLI execution
if __name__ == "__main__":
    print("\n🔹 **AI Email Assistant Automation** 🔹")
    print("1️⃣ Run full automation now")
    print("2️⃣ Start scheduler for automation every 30 minutes")
    print("3️⃣ Exit")

    choice = input("👉 Enter your choice: ").strip()

    if choice == "1":
        run_full_automation()
    elif choice == "2":
        start_scheduler()
    elif choice == "3":
        print("👋 Exiting...")
    else:
        print("⚠️ Invalid choice! Try again.")