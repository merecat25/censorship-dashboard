import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("ripe_ping_5001.csv")
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Plot average latency
plt.figure(figsize=(10, 5))
plt.plot(df["timestamp"], df["avg_latency"], label="Avg Latency (ms)")
plt.fill_between(df["timestamp"], df["min_latency"], df["max_latency"], color='lightgray', alpha=0.5, label="Min/Max Range")

plt.title("RIPE Atlas Measurement 5001 - Latency to 8.8.8.8")
plt.xlabel("Timestamp")
plt.ylabel("Latency (ms)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("ripe_5001_latency.png")
plt.show()
