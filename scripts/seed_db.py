import sqlite3

# 1. Connect to SQLite (this creates the file if it doesn't exist)
conn = sqlite3.connect("database.sqlite")
cursor = conn.cursor()

# 2. Create the Users table
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT NOT NULL
    )
"""
)

# 3. Clear the table if you are re-running the script
cursor.execute("DELETE FROM users")

# 4. Insert 100 Test Users (50 Proposers, 50 Receivers for Gale-Shapley)
users = []
for i in range(1, 51):
    users.append((f"Proposer_{i}", "Proposer"))
    users.append((f"Receiver_{i}", "Receiver"))

cursor.executemany("INSERT INTO users (name, role) VALUES (?, ?)", users)

# 5. Save and Close
conn.commit()
conn.close()

print("Success: database.sqlite created with 100 test users.")
