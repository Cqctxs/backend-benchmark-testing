import discord
import asyncio
import time
import csv
import os
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# ── Environment Variables (set in Railway or locally before running) ──────────
TESTER_TOKEN = os.environ["TEST_BOT_TOKEN"]
MATCHING_BOT_ID = int(os.environ["MATCH_BOT_ID"])
CHANNEL_IDS = [int(x) for x in os.environ["CHANNEL_IDS"].split(",")]
TEST_MODE = os.environ.get("TEST_MODE", "stress")  # 'baseline' or 'stress'

# ── Test Parameters ───────────────────────────────────────────────────────────
TARGET_RATE_PER_SECOND = int(
    os.environ.get("TARGET_RATE_PER_SECOND", "50")
)  # Stay slightly below 50 to avoid global rate limits
BASELINE_REQUESTS = 10
BASELINE_INTERVAL = 1.0  # 1 req/s → 10 reqs over 10s, single channel

STRESS_REQUESTS_PER_CHANNEL = 10
# Calculate interval dynamically based on number of channels and desired rate
# Rate (req/sec) = 1 / (interval / len(CHANNEL_IDS))
# interval = len(CHANNEL_IDS) / Rate
if len(CHANNEL_IDS) > 0:
    STRESS_INTERVAL = len(CHANNEL_IDS) / TARGET_RATE_PER_SECOND
else:
    STRESS_INTERVAL = 1.0

# ── Shared State ──────────────────────────────────────────────────────────────
pending = {}  # test_id (str) → send timestamp (perf_counter)
results = []  # list of dicts: {test_id, channel_id, rtt_seconds}
expected_count = 0
all_done = asyncio.Event()

# ── Discord Client ────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True  # must be set BEFORE constructing client
client = discord.Client(intents=intents)


# ── Helpers ───────────────────────────────────────────────────────────────────
async def send_requests(channel, request_ids, interval, start_delay=0.0):
    await asyncio.sleep(start_delay)  # ← stagger the initial burst
    for test_id in request_ids:
        pending[str(test_id)] = time.perf_counter()
        await channel.send(f"!match {test_id}")
        print(f"[{test_id}] → channel {channel.id}")
        await asyncio.sleep(interval)


def write_results(filename):
    # Raw per-request CSV
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["test_id", "channel_id", "rtt_seconds"])
        writer.writeheader()
        writer.writerows(results)

    rtts_ms = sorted([r["rtt_seconds"] * 1000 for r in results])
    n = len(rtts_ms)
    if n == 0:
        print("No results captured — check MATCHING_BOT_ID and CHANNEL_IDS.")
        return

    mean = round(sum(rtts_ms) / n)
    median = round(np.percentile(rtts_ms, 50))
    p90 = round(np.percentile(rtts_ms, 90))
    p95 = round(np.percentile(rtts_ms, 95))
    p99 = round(np.percentile(rtts_ms, 99))
    mn = round(min(rtts_ms))
    mx = round(max(rtts_ms))
    std = round(float(np.std(rtts_ms)), 2)

    agg_row = {
        "Label": "Discord Bot",
        "# Samples": n,
        "Average": mean,
        "Median": median,
        "90% Line": p90,
        "95% Line": p95,
        "99% Line": p99,
        "Min": mn,
        "Max": mx,
        "Error %": "0.00%",
        "Std. Dev.": std,
    }
    agg_file = filename.replace(".csv", "_aggregate.csv")
    with open(agg_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=agg_row.keys())
        writer.writeheader()
        writer.writerow(agg_row)
        writer.writerow({**agg_row, "Label": "TOTAL"})

    print(f"\n--- {filename} ({n} samples) ---")
    print(f"Mean:  {mean}ms  |  P90: {p90}ms")
    print(f"Min:   {mn}ms   |  Max: {mx}ms  |  Std: {std}ms")
    print(f"Raw CSV:       {filename}")
    print(f"Aggregate CSV: {agg_file}")


# ── Test Runners ──────────────────────────────────────────────────────────────
async def run_baseline():
    global expected_count
    expected_count = BASELINE_REQUESTS

    channel = client.get_channel(CHANNEL_IDS[0])
    if channel is None:
        print(f"ERROR: Could not find channel {CHANNEL_IDS[0]}. Check CHANNEL_IDS.")
        await client.close()
        return

    await send_requests(channel, list(range(BASELINE_REQUESTS)), BASELINE_INTERVAL)

    try:
        await asyncio.wait_for(all_done.wait(), timeout=15)
    except asyncio.TimeoutError:
        print(
            f"WARNING: Timed out waiting — only {len(results)}/{expected_count} responses received."
        )

    write_results("baseline_results.csv")
    await client.close()


async def run_stress():
    global expected_count
    expected_count = len(CHANNEL_IDS) * STRESS_REQUESTS_PER_CHANNEL

    channels = [client.get_channel(cid) for cid in CHANNEL_IDS]
    missing = [cid for cid, ch in zip(CHANNEL_IDS, channels) if ch is None]
    if missing:
        print(f"ERROR: Could not find channels: {missing}")
        await client.close()
        return

    # Channel i handles request IDs [i*10 ... i*10+9]
    tasks = [
        send_requests(
            ch,
            list(
                range(
                    i * STRESS_REQUESTS_PER_CHANNEL,
                    (i + 1) * STRESS_REQUESTS_PER_CHANNEL,
                )
            ),
            STRESS_INTERVAL,
            start_delay=i
            * (STRESS_INTERVAL / len(channels)),  # Evens out the rate perfectly
        )
        for i, ch in enumerate(channels)
    ]
    await asyncio.gather(*tasks)

    # Calculate required timeout: num requests / rate per second + 15s buffer
    total_time_s = (expected_count / TARGET_RATE_PER_SECOND) + 15
    try:
        await asyncio.wait_for(all_done.wait(), timeout=total_time_s)
    except asyncio.TimeoutError:
        print(
            f"WARNING: Timed out waiting — only {len(results)}/{expected_count} responses received."
        )

    write_results("stress_results.csv")
    await client.close()


# ── Discord Events ────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    print(f"Tester online as {client.user} | Mode: {TEST_MODE}")
    await asyncio.sleep(2)  # let gateway connection stabilize
    if TEST_MODE == "baseline":
        client.loop.create_task(run_baseline())
    else:
        client.loop.create_task(run_stress())


@client.event
async def on_message(message):
    if message.author.id != MATCHING_BOT_ID:
        return
    if not message.content.startswith("Success"):
        return

    parts = message.content.split()
    try:
        test_id = parts[1].rstrip(":")
        t_receive = time.perf_counter()
        t_send = pending.pop(test_id, None)
        if t_send is not None:
            rtt = round(t_receive - t_send, 4)
            results.append(
                {
                    "test_id": test_id,
                    "channel_id": message.channel.id,
                    "rtt_seconds": rtt,
                }
            )
            print(f"[{test_id}] RTT: {rtt:.4f}s  ({rtt*1000:.1f}ms)")
            if len(results) >= expected_count:
                all_done.set()  # signals runner to stop waiting immediately
    except IndexError:
        pass


# ── Entry Point ───────────────────────────────────────────────────────────────
client.run(TESTER_TOKEN)
