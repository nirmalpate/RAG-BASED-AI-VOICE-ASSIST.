import os

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

from app.agent import HotelAgent

app = FastAPI(title="Hotel Bayerischer Hof Voice Agent (Vonage)")
SESSIONS = {}

# Optional: real number of the night porter (E.164, e.g. +4989...). If set, emergency calls are really transferred.
NIGHT_PORTIER_NUMBER = os.environ.get("NIGHT_PORTIER_NUMBER", "").strip()

NO_INPUT_TEXT = "Ich habe leider nichts gehört. Vielen Dank für Ihren Anruf. Auf Wiederhören."
UNCLEAR_TEXT = "Das habe ich leider nicht verstanden. Könnten Sie das bitte wiederholen?"
ERROR_TEXT = "Entschuldigung, es gab ein technisches Problem. Bitte versuchen Sie es noch einmal."


def public_base_url(request: Request) -> str:
    """Vonage needs absolute callback URLs. Set PUBLIC_BASE_URL (e.g. your ngrok URL) or it is derived from headers."""
    env_url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return f"{proto}://{host}"


@app.get("/health")
def health_check():
    return {"status": "healthy", "hotel": "Bayerischer Hof München", "telephony": "Vonage"}


# ======================= VONAGE (Voice API / NCCO) =======================
# Answer URL:  {PUBLIC_BASE_URL}/vonage/answer  (GET or POST)
# Event URL:   {PUBLIC_BASE_URL}/vonage/event   (POST)

def vonage_ncco(request: Request, text: str, final: bool = False) -> list:
    ncco = [{"action": "talk", "text": text, "language": "de-DE", "style": 0, "bargeIn": not final}]
    if not final:
        ncco.append({
            "action": "input",
            "type": ["speech"],
            "eventUrl": [f"{public_base_url(request)}/vonage/input"],
            "eventMethod": "POST",
            "speech": {"language": "de-DE", "endOnSilence": 1.5, "startTimeout": 10, "maxDuration": 25},
        })
    return ncco


async def _params(request: Request) -> dict:
    if request.method == "GET":
        return dict(request.query_params)
    try:
        return await request.json()
    except Exception:
        return {}


@app.api_route("/vonage/answer", methods=["GET", "POST"])
async def vonage_answer(request: Request):
    p = await _params(request)
    uuid = p.get("uuid") or p.get("conversation_uuid") or "unknown"
    agent = HotelAgent(call_id=uuid, caller_number=str(p.get("from", "Unbekannt")))
    SESSIONS[uuid] = agent

    if agent.is_night_shift:
        greeting = "Guten Abend beim Nachtservice des Hotel Bayerischer Hof in München. Haben Sie ein dringendes Anliegen oder einen Notfall?"
    else:
        greeting = "Grüß Gott und herzlich willkommen im Hotel Bayerischer Hof in München. Wie kann ich Ihnen heute behilflich sein?"
    return vonage_ncco(request, greeting)


@app.post("/vonage/input")
async def vonage_input(request: Request):
    p = await _params(request)
    uuid = p.get("uuid") or p.get("conversation_uuid") or "unknown"
    agent = SESSIONS.get(uuid)
    if not agent:
        agent = HotelAgent(call_id=uuid)
        SESSIONS[uuid] = agent

    results = (p.get("speech") or {}).get("results") or []
    speech = (results[0].get("text", "") if results else "").strip()

    if not speech:
        agent.silence_count = getattr(agent, "silence_count", 0) + 1
        if agent.silence_count >= 2:
            return vonage_ncco(request, NO_INPUT_TEXT, final=True)
        return vonage_ncco(request, UNCLEAR_TEXT)
    agent.silence_count = 0

    try:
        reply_text = await run_in_threadpool(agent.reply, speech)
    except Exception as e:
        print(f"[agent error] {uuid}: {e}")
        return vonage_ncco(request, ERROR_TEXT)

    if agent.transfer_requested and NIGHT_PORTIER_NUMBER:
        agent.transfer_requested = False
        return [
            {"action": "talk", "text": reply_text, "language": "de-DE", "style": 0},
            {"action": "connect", "endpoint": [{"type": "phone", "number": NIGHT_PORTIER_NUMBER.lstrip("+")}]},
        ]
    return vonage_ncco(request, reply_text)


@app.post("/vonage/event")
async def vonage_event(request: Request):
    p = await _params(request)
    if p.get("status") in ("completed", "failed", "rejected", "busy", "cancelled", "timeout", "unanswered"):
        SESSIONS.pop(p.get("uuid", ""), None)
    return {"status": "ok"}
