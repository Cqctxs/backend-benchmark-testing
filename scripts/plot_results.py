import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys

csv_file = sys.argv[1]  # e.g. python plot_results.py baseline_results.csv
df = pd.read_csv(csv_file)
df["rtt_ms"] = df["rtt_seconds"] * 1000
df = df.sort_values("test_id").reset_index(drop=True)
df["bucket"] = (df.index // 1) * 500  # one point per request

mean_rtt = round(df["rtt_ms"].mean(), 1)
p90 = round(np.percentile(df["rtt_ms"], 90), 1)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df.index * 1.0,
        y=df["rtt_ms"],
        mode="lines",
        name=f"RTT (mean={mean_rtt}ms, P90={p90}ms)",
        line=dict(color="#e03131", width=2.5),
    )
)
fig.add_hline(
    y=mean_rtt,
    line_dash="dash",
    line_color="gray",
    annotation_text=f"Mean {mean_rtt}ms",
    annotation_position="top right",
)
fig.add_hline(
    y=p90,
    line_dash="dot",
    line_color="orange",
    annotation_text=f"P90 {p90}ms",
    annotation_position="top left",
)

fig.update_xaxes(title_text="Request #", tickfont=dict(size=13), showgrid=True)
fig.update_yaxes(title_text="RTT (ms)", tickfont=dict(size=13), showgrid=True)
fig.update_layout(
    title={"text": f"Discord Bot RTT — {csv_file}"},
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
)
out = csv_file.replace(".csv", "_chart.png")
fig.write_image(out)
print(f"Chart saved to {out}")
