import pandas as pd
import numpy as np
import plotly.graph_objects as go
import sys
import os

if len(sys.argv) < 2:
    print("Usage: python plot_jtl.py <path_to_jtl_or_csv>")
    sys.exit(1)

file_path = sys.argv[1]
df = pd.read_csv(file_path)

# Filter out failed requests if you only want to plot successful ones
# (Optional, but usually a good idea)
# df = df[df['success'] == True].reset_index(drop=True)

# 'elapsed' in JMeter's JTL is the response time in milliseconds
rtt_ms = df["elapsed"]

mean_rtt = round(rtt_ms.mean(), 1)
p90 = round(np.percentile(rtt_ms, 90), 1)

fig = go.Figure()

# Plot the elapsed times
fig.add_trace(
    go.Scatter(
        x=df.index * 1.0,
        y=rtt_ms,
        mode="lines",
        name=f"Response Time (mean={mean_rtt}ms, P90={p90}ms)",
        line=dict(color="#1f77b4", width=2.5),
    )
)

# Mean horizontal line
fig.add_hline(
    y=mean_rtt,
    line_dash="dash",
    line_color="gray",
    annotation_text=f"Mean {mean_rtt}ms",
    annotation_position="top right",
)

# P90 horizontal line
fig.add_hline(
    y=p90,
    line_dash="dot",
    line_color="orange",
    annotation_text=f"P90 {p90}ms",
    annotation_position="top left",
)

# Formats and labels
fig.update_xaxes(title_text="Request #", tickfont=dict(size=13), showgrid=True)
fig.update_yaxes(title_text="Response Time (ms)", tickfont=dict(size=13), showgrid=True)

file_name = os.path.basename(file_path)
fig.update_layout(
    title={"text": f"JMeter Test Results — {file_name}"},
    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
)

out = file_path.replace(".csv", "_chart.png").replace(".jtl", "_chart.png")
fig.write_image(out)
print(f"Chart saved to {out}")
