import sqlite3
import random
from datetime import datetime, timedelta

# 1. Connect to SQLite
conn = sqlite3.connect('database.sqlite')
cursor = conn.cursor()

# 2. Clean up old tables
cursor.executescript('''
    DROP TABLE IF EXISTS user_interests;
    DROP TABLE IF EXISTS user_hardships;
    DROP TABLE IF EXISTS interests;
    DROP TABLE IF EXISTS hardships;
    DROP TABLE IF EXISTS users;
''')

# 3. Create the Relational Schema
# Note: We use two separate 'Join Tables' for interests and hardships.
cursor.executescript('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        birth_date TEXT NOT NULL,
        pronouns_id INTEGER NOT NULL
    );

    CREATE TABLE interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL
    );
                     
    CREATE TABLE hardships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT NOT NULL
    );

    CREATE TABLE user_interests (
        user_id INTEGER,
        interest_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(interest_id) REFERENCES interests(id)
    );

    CREATE TABLE user_hardships (
        user_id INTEGER,
        hardship_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(hardship_id) REFERENCES hardships(id)
    );
''')

# 4. Populate Master Lists
master_interests = ["Hiking", "Running", "Pilates", "Yoga", "Swimming", "Biking", "Gymnastics", "Tennis", "Dancing", "Walking"]
master_hardships = ["Injury", "Financials", "Fear of Gym", "Illnesses", "Immunity", "Depression", "Cancer", "Drugs", "Smoking", "Identity Crisis"]

cursor.executemany('INSERT INTO interests (label) VALUES (?)', [(i,) for i in master_interests])
cursor.executemany('INSERT INTO hardships (label) VALUES (?)', [(h,) for h in master_hardships])

# 5. Generate 100 Test Users
start_date = datetime.strptime("1990-01-01", "%Y-%m-%d")

for i in range(1, 101):
    name = f"User_{i}"
    random_days = random.randint(0, 365 * 17) 
    birth_date = (start_date + timedelta(days=random_days)).strftime("%Y-%m-%d")
    pronouns_id = random.randint(1, 3)
    
    cursor.execute('INSERT INTO users (full_name, birth_date, pronouns_id) VALUES (?, ?, ?)', (name, birth_date, pronouns_id))
    user_id = cursor.lastrowid
    
    # Insert into the specific Join Table for interests
    selected_interests = random.sample(range(1, 11), 5)
    for interest_id in selected_interests:
        cursor.execute('INSERT INTO user_interests (user_id, interest_id) VALUES (?, ?)', (user_id, interest_id))

    # Insert into the specific Join Table for hardships
    selected_hardships = random.sample(range(1, 11), 3)
    for hardship_id in selected_hardships:
        cursor.execute('INSERT INTO user_hardships (user_id, hardship_id) VALUES (?, ?)', (user_id, hardship_id))

conn.commit()
conn.close()
print("Success: database.sqlite created with normalized tables.")