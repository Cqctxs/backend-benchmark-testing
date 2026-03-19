import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import modal
import time
from supabase import create_client, Client

# 1. Define the environment
image = modal.Image.debian_slim().pip_install("supabase", "FastAPI", "uvicorn")

app = modal.App("ai-matching-backend")

# Package the local .env variables into a Modal Secret so the container can access them
supabase_secrets = modal.Secret.from_dict(
    {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_KEY": os.environ.get("SUPABASE_KEY", ""),
    }
)


# 2. Supabase Credentials
# NOTE: Using a Modal App Class allows caching the Supabase client per container
@app.cls(image=image, secrets=[supabase_secrets])
class MatchApp:
    @modal.enter()
    def setup(self):
        # 3. Initialize Supabase Client ONCE per container lifecycle
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    @modal.web_endpoint(method="GET")
    def match(self):
        # Start high-precision timer
        start_time = time.perf_counter_ns()

        try:
            # 4. Execute the matching logic in Supabase using the cached client
            result = self.supabase.rpc(
                "match_users_by_id",
                {"p_user_id": 1, "match_threshold": 0.5, "match_count": 50},
            ).execute()

            # Calculate duration in microseconds
            duration_micros = (time.perf_counter_ns() - start_time) // 1000

            return {
                "status": "Success",
                "matches_made": len(result.data) if result.data else 0,
                "processing_time_micros": duration_micros,
            }

        except Exception as e:
            return {"status": "Error", "message": str(e)}
