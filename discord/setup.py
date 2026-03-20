import discord
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

# Throwaway setup bot token — run once, then delete this bot
SETUP_TOKEN = os.environ["SETUP_BOT_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])  # Right-click server → Copy Server ID

intents = discord.Intents.default()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if guild is None:
        print("ERROR: Guild not found. Check GUILD_ID and that bot is in the server.")
        await client.close()
        return

    # Create a category to keep things organized
    category = await guild.create_category("mos-test-channels")
    print(f"Created category: {category.name} ({category.id})")

    channel_ids = []
    for i in range(50):
        channel = await guild.create_text_channel(
            name=f"test-{i:02d}", category=category  # test-00, test-01, ..., test-49
        )
        channel_ids.append(channel.id)
        print(f"  Created #{channel.name} → {channel.id}")

    # Print the final comma-separated string ready to paste into Railway env var
    ids_string = ",".join(str(cid) for cid in channel_ids)
    print(f"\n--- COPY THIS INTO CHANNEL_IDS ENV VAR ---")
    print(ids_string)

    await client.close()


client.run(SETUP_TOKEN)
