import ollama
import sqlite3

# Database connection
DB = "data/emails.db"
conn = sqlite3.connect(DB)
cursor = conn.cursor()

#  Fetch emails that don't have a summary yet
cursor.execute("SELECT id, subject, body FROM emails WHERE summary IS NULL")
emails = cursor.fetchall()

# Function to summarize the email
def summarize_email(email_text):
    prompt = f"""
    You are an email summarizer. Given the following email, provide a summary.

    Email: {email_text}
    Summary:
    """
    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

#  Summarize emails and update database
updated_records = []
for email_id, subject, body in emails:
    email_text = f"{subject}\n{body[:500]}"  # First 500 characters of the body for summary
    summary = summarize_email(email_text)  # Generate summary
    updated_records.append((summary, email_id))

#  Batch update summaries
if updated_records:
    cursor.executemany("UPDATE emails SET summary = ? WHERE id = ?", updated_records)
    conn.commit()
    print(f" {len(updated_records)} emails summarized successfully!")
else:
    print(" No new emails required summarization.")

# Close the connection
conn.close()