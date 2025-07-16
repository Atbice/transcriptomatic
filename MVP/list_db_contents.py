import sqlite3

db_path = 'MVP/data/trans_agents.db'
target_title = 'kodsnack 643'

def list_kodsnack_contents(db_path, title):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get the meeting_id for the target title
        cursor.execute("SELECT id FROM meetings WHERE title = ?;", (title,))
        meeting_id_result = cursor.fetchone()

        if not meeting_id_result:
            print(f"No meeting found with title: '{title}'")
            return

        meeting_id = meeting_id_result[0]
        print(f"\n--- Details for Meeting: '{title}' (ID: {meeting_id}) ---")

        # Get meeting details
        cursor.execute("SELECT * FROM meetings WHERE id = ?;", (meeting_id,))
        meeting_details = cursor.fetchone()
        if meeting_details:
            columns = [description[0] for description in cursor.description]
            print(f"Meeting Details: {dict(zip(columns, meeting_details))}")
        else:
            print("Meeting details not found.")

        # Get associated transcripts
        print(f"\n--- Transcripts for Meeting ID: {meeting_id} ---")
        cursor.execute("SELECT * FROM transcripts WHERE meeting_id = ? ORDER BY timestamp;", (meeting_id,))
        transcripts = cursor.fetchall()

        if not transcripts:
            print("No transcripts found for this meeting.")
        else:
            for transcript_row in transcripts:
                print(transcript_row)

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    list_kodsnack_contents(db_path, target_title)