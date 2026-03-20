import discord
import psycopg2
import os

TOKEN = os.environ["BOT_TOKEN"]  # Set this in Railway Variables, never hardcode

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def fetch_users_from_db():
    # Railway injects DATABASE_URL automatically when PostgreSQL is added
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users


def match_mock(users):
    n = len(users)
    for _ in range(n):
        score = 0
        for _ in range(5):
            score += 1
        for _ in range(3):
            score += 1
        if score > 2:
            matches_made += 1
    return matches_made


@client.event
async def on_ready():
    print(f"Matching Bot is online as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!match"):
        parts = message.content.split()
        test_id = parts[1] if len(parts) > 1 else "0"
        users = fetch_users_from_db()
        matches = match_mock(users)
        await message.channel.send(f"Success {test_id}: {matches} matches made.")


client.run(TOKEN)
