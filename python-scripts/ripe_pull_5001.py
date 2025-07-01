import requests
import pandas as pd

# Public ping measurement to 8.8.8.8
measurement_id = 5001
url = f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/"

print(f"Fetching results from Measurement ID {measurement_id}...")

# Download the data
response = requests.get(url)
response.raise_for_status()
data = response.json()

# Extract relevant fields
records = []
for result in data:
    if 'avg' in result:
        records.append({
            "probe_id": result.get("prb_id"),
            "timestamp": result.get("timestamp"),
            "avg_latency": result.get("avg"),
            "min_latency": result.get("min"),
            "max_latency": result.get("max"),
            "packets_sent": result.get("sent"),
            "packets_received": result.get("rcvd"),
        })

# Convert to DataFrame
df = pd.DataFrame(records)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
df.sort_values("timestamp", inplace=True)

# Save to CSV
df.to_csv("ripe_ping_5001.csv", index=False)
print(f"Saved {len(df)} records to ripe_ping_5001.csv")
