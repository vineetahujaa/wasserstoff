import sqlite3
import ollama

# ✅ Database se connect karo
DB_PATH = "data/emails.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ✅ Ensure Category column exists
cursor.execute("PRAGMA table_info(emails)")
columns = [col[1] for col in cursor.fetchall()]
if "Category" not in columns:
    cursor.execute("ALTER TABLE emails ADD COLUMN Category TEXT DEFAULT 'Uncategorized'")
    conn.commit()

# ✅ Fetch all emails (overwrite existing category)
cursor.execute("SELECT id, subject, body FROM emails")
emails = cursor.fetchall()

# ✅ Email categorization function
def classify_email(email_text):
    prompt = f"""
    You are an AI email classifier. Categorize the email into one of the following categories:
    
    - **Spam**: Promotional emails, ads, or phishing attempts.
    - **Finance**: Bank statements, invoices, payment receipts.
    - **Career**: Job offers, interview calls, HR emails.
    - **Social**: Personal messages, social media notifications.
    - **Security**: Password resets, security alerts, authentication emails.
    - **Meeting**: Calendar invites, meeting reminders, scheduling emails.
    - **Other**: Anything that does not fit the above categories.

    Always return only one of these category names.

    **Email Content:**  
    {email_text}

    **Category:** 
    """

    response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

# ✅ Classify & overwrite category
for email_id, subject, body in emails:
    email_text = f"{subject}\n{body[:500]}"  # First 500 chars for classification
    predicted_category = classify_email(email_text)

    # Overwrite category
    cursor.execute("UPDATE emails SET Category = ? WHERE id = ?", (predicted_category, email_id))

# ✅ Save changes & close DB connection
conn.commit()
conn.close()

print("✅ All emails categorized successfully! (Overwritten)")  