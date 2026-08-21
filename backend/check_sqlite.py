import sqlite3

def check():
    conn = sqlite3.connect("backend/bursa_faaliyet.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, report_id, creator_id, status, source_item_id FROM report_item")
    rows = cursor.fetchall()
    print("id | report_id | creator_id | status | source_item_id")
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
    conn.close()

if __name__ == "__main__":
    check()
