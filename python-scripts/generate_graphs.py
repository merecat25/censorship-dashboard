import json
import matplotlib.pyplot as plt
import os

input_file = "results.json"
output_dir = "static/images"

os.makedirs(output_dir, exist_ok=True)

with open(input_file) as f:
    raw = [json.loads(line) for line in f if line.strip()]
    # Flatten if outer structure is a list of lists
    data = [item for sublist in raw for item in (sublist if isinstance(sublist, list) else [sublist])]

probe_ids = []
avg_rtts = []
loss_rates = []

for entry in data:
    probe_id = entry.get("prb_id")
    results = entry.get("result", [])
    
    successes = [r["rtt"] for r in results if "rtt" in r]
    losses = len([r for r in results if "x" in r])
    
    if results:
        loss_rate = losses / len(results)
        avg_rtt = sum(successes) / len(successes) if successes else None

        probe_ids.append(str(probe_id))
        avg_rtts.append(avg_rtt if avg_rtt is not None else 0)
        loss_rates.append(loss_rate * 100)
    else:
        probe_ids.append(str(probe_id))
        avg_rtts.append(0)
        loss_rates.append(100)

# Plot RTT
plt.figure(figsize=(12, 5))
plt.bar(probe_ids, avg_rtts)
plt.ylabel("Average RTT (ms)")
plt.xlabel("Probe ID")
plt.title("Ping Latency from Iran to 1.1.1.1")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(f"{output_dir}/iran_ping_rtt.png")
plt.close()

# Plot Loss
plt.figure(figsize=(12, 5))
plt.bar(probe_ids, loss_rates, color="red")
plt.ylabel("Packet Loss (%)")
plt.xlabel("Probe ID")
plt.title("Packet Loss from Iran to 1.1.1.1")
plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(f"{output_dir}/iran_ping_loss.png")
plt.close()

