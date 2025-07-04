import requests
import json

api_key = "7a071b2d-04b0-4657-9d13-e4a237d4cfc3"  # Replace with your real key
url = "https://atlas.ripe.net/api/v2/measurements/"

headers = {
    "Authorization": f"Key {api_key}",
    "Content-Type": "application/json"
}

body = {
    "definitions": [
        {
            "type": "ping",
            "af": 4,
            "resolve_on_probe": True,
            "description": "Ping measurement to 1.1.1.1",
            "packets": 3,
            "size": 48,
            "target": "1.1.1.1"
        }
    ],
    "probes": [
        {
            "type": "country",
            "value": "IR",
            "requested": 81
        }
    ],
    "is_oneoff": True,
    "bill_to": "merecat25@protonmail.com"
}

response = requests.post(url, headers=headers, data=json.dumps(body))

if response.status_code == 201:
    print("Measurement created! ID:", response.json()["measurements"][0])
else:
    print("Error:", response.status_code, response.text)
