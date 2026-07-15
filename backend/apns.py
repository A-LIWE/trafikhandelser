import httpx
import jwt
import time
import os
from models import TrafficIncident

APNS_URL = "https://api.push.apple.com"
APNS_SANDBOX_URL = "https://api.sandbox.push.apple.com"

def build_token() -> str:
    key = os.getenv("APNS_PRIVATE_KEY")
    key_id = os.getenv("APNS_KEY_ID")
    team_id = os.getenv("APNS_TEAM_ID")

    payload = {
        "iss": team_id,
        "iat": time.time()
    }

    token = jwt.encode(
        payload,
        key,
        algorithm="ES256",
        headers={"kid": key_id}
    )
    return token

async def send_push(device_token: str, incident: TrafficIncident, sandbox: bool = True):
    bundle_id = os.getenv("APNS_BUNDLE_ID")
    base_url = APNS_SANDBOX_URL if sandbox else APNS_URL
    url = f"{base_url}/3/device/{device_token}"

    auth_token = build_token()

    payload = {
        "aps": {
            "alert": {
                "title": "Trafikolycka",
                "body": incident.header
            },
            "sound": "default"
        },
        "latitude": incident.lat,
        "longitude": incident.lon,
        "incident_id": incident.id
    }

    async with httpx.AsyncClient(http2=True) as client:
        response = await client.post(
            url,
            json=payload,
            headers={
                "authorization": f"bearer {auth_token}",
                "apns-topic": bundle_id,
                "apns-push-type": "alert",
                "apns-priority": "10"
            }
        )

        if response.status_code != 200:
            print(f"APNs error {response.status_code}: {response.text}")
        else:
            print(f"Push sent to {device_token[:10]}...")

async def send_push_to_all(tokens: list[str], incident: TrafficIncident):
    for token in tokens:
        await send_push(token, incident)