import os
from supabase import create_client, Client
import random

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Generate 100 fake users with random 1536-dimensional vectors
for i in range(1, 101):
    fake_embedding =[random.uniform(-1, 1) for _ in range(1536)]
    supabase.table("ai_users").insert({
        "name": f"AI_User_{i}",
        "embedding": fake_embedding
    }).execute()

print("Supabase seeded with 100 AI users!")