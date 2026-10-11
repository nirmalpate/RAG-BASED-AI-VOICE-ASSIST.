"""Vonage: make Vonage call YOUR phone and connect it to this server (no number purchase needed).
Usage: python call_me.py 491774499545
Needs env: VONAGE_APPLICATION_ID, VONAGE_PRIVATE_KEY_PATH (default private.key), PUBLIC_BASE_URL
pip install pyjwt cryptography requests
"""
import os, sys, time, uuid, json
import jwt, requests

to = sys.argv[1].lstrip("+")
app_id = os.environ["VONAGE_APPLICATION_ID"]
key = open(os.environ.get("VONAGE_PRIVATE_KEY_PATH", "private.key")).read()
base = os.environ["PUBLIC_BASE_URL"].rstrip("/")
from_number = os.environ.get("VONAGE_FROM", "12345678901")

now = int(time.time())
token = jwt.encode({"application_id": app_id, "iat": now, "exp": now + 300, "jti": str(uuid.uuid4())}, key, algorithm="RS256")
r = requests.post(
    "https://api.nexmo.com/v1/calls",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "to": [{"type": "phone", "number": to}],
        "from": {"type": "phone", "number": from_number},
        "answer_url": [f"{base}/vonage/answer"],
        "answer_method": "GET",
        "event_url": [f"{base}/vonage/event"],
        "event_method": "POST",
    },
)
print(r.status_code, r.text)
