import psycopg2
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Pull from env — run locally with:
# DATABASE_URL=your_railway_url python seed.py
DATABASE_URL = os.environ["DATABASE_URL"]

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True  # required for DDL (DROP/CREATE TABLE)
cursor = conn.cursor()

# 1. Drop old tables in reverse dependency order
for stmt in [
    "DROP TABLE IF EXISTS user_interests",
    "DROP TABLE IF EXISTS user_hardships",
    "DROP TABLE IF EXISTS interests",
    "DROP TABLE IF EXISTS hardships",
    "DROP TABLE IF EXISTS users",
]:
    cursor.execute(stmt)

# 2. Create schema — SERIAL replaces AUTOINCREMENT
cursor.execute(
    """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        full_name TEXT NOT NULL,
        birth_date TEXT NOT NULL,
        pronouns_id INTEGER NOT NULL
    )
"""
)
cursor.execute(
    """
    CREATE TABLE interests (
        id SERIAL PRIMARY KEY,
        label TEXT NOT NULL
    )
"""
)
cursor.execute(
    """
    CREATE TABLE hardships (
        id SERIAL PRIMARY KEY,
        label TEXT NOT NULL
    )
"""
)
cursor.execute(
    """
    CREATE TABLE user_interests (
        user_id INTEGER REFERENCES users(id),
        interest_id INTEGER REFERENCES interests(id)
    )
"""
)
cursor.execute(
    """
    CREATE TABLE user_hardships (
        user_id INTEGER REFERENCES users(id),
        hardship_id INTEGER REFERENCES hardships(id)
    )
"""
)

# 3. Switch off autocommit for data inserts (runs as one transaction)
conn.autocommit = False

# 4. Populate master lists
master_interests = [
    "Hiking",
    "Running",
    "Pilates",
    "Yoga",
    "Swimming",
    "Biking",
    "Gymnastics",
    "Tennis",
    "Dancing",
    "Walking",
]
master_hardships = [
    "Injury",
    "Financials",
    "Fear of Gym",
    "Illnesses",
    "Immunity",
    "Depression",
    "Cancer",
    "Drugs",
    "Smoking",
    "Identity Crisis",
]

cursor.executemany(
    "INSERT INTO interests (label) VALUES (%s)", [(i,) for i in master_interests]
)
cursor.executemany(
    "INSERT INTO hardships (label) VALUES (%s)", [(h,) for h in master_hardships]
)

# 5. Generate 100 test users
start_date = datetime.strptime("1990-01-01", "%Y-%m-%d")

for i in range(1, 101):
    name = f"User_{i}"
    birth_date = (start_date + timedelta(days=random.randint(0, 365 * 17))).strftime(
        "%Y-%m-%d"
    )
    pronouns_id = random.randint(1, 3)

    cursor.execute(
        "INSERT INTO users (full_name, birth_date, pronouns_id) VALUES (%s, %s, %s) RETURNING id",
        (name, birth_date, pronouns_id),
    )
    user_id = cursor.fetchone()[0]

    for interest_id in random.sample(range(1, 11), 5):
        cursor.execute(
            "INSERT INTO user_interests (user_id, interest_id) VALUES (%s, %s)",
            (user_id, interest_id),
        )
    for hardship_id in random.sample(range(1, 11), 3):
        cursor.execute(
            "INSERT INTO user_hardships (user_id, hardship_id) VALUES (%s, %s)",
            (user_id, hardship_id),
        )

conn.commit()
cursor.close()
conn.close()
print("Success: PostgreSQL seeded with 100 users, interests, and hardships.")
