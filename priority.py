import sqlite3
import ollama

# Priority Assignment Function
def assign_priority():
    """Priority classification using LLM"""
    DB_PATH = "data/emails.db"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #  Ensure Priority column exists
    cursor.execute("PRAGMA table_info(emails)")
    columns = [col[1] for col in cursor.fetchall()]
    if "priority" not in columns:
        cursor.execute("ALTER TABLE emails ADD COLUMN priority TEXT DEFAULT 'Routine'")
        conn.commit()

    # Fetch uncategorized priority emails
    cursor.execute("SELECT id, sender, subject, body FROM emails")
    emails = cursor.fetchall()

    priority_levels = {"Critical", "Urgent", "Important", "Routine"}  # ✅ Valid categories

    for email_id, sender, subject, body in emails:
        try:
            prompt = f"""
            You are an AI email assistant. Assign the priority of this email based on urgency:
            
            - **Critical**: Requires immediate attention (e.g., security breach, emergency response).
            - **Urgent**: Needs to be addressed soon (e.g., time-sensitive tasks, deadline-related).
            - **Important**: Relevant but not immediate (e.g., meeting invites, project updates).
            - **Routine**: General emails, newsletters, low-priority messages.

            **Email Details:**
            - **From**: {sender}
            - **Subject**: {subject}
            - **Body**: {body[:500]}

            Always return ONLY ONE of these four options: Critical, Urgent, Important, Routine.
            """

            response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
            priority = response["message"]["content"].strip()

            #  Validate response
            if priority not in priority_levels:
                print(f" Invalid response '{priority}', defaulting to 'Routine'")
                priority = "Routine"

            # Update priority in database
            cursor.execute("UPDATE emails SET priority = ? WHERE id = ?", (priority, email_id))
            conn.commit()

            print(f"Email {email_id} classified as {priority}")

        except Exception as e:
            print(f" Error processing email {email_id}: {e}")
            cursor.execute("UPDATE emails SET priority = ? WHERE id = ?", ("Routine", email_id))
            conn.commit()

    conn.close()
    print(" All emails have been assigned priorities successfully!")

#  Run priority assignment
assign_priority()