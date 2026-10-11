# Hotel Bayerischer Hof – German Voice Agent (Vonage)

Phone voice assistant (German) for hotel guests. Vonage Voice API + Groq LLM + hotel knowledge injected into the prompt.

## Setup
1. `pip install fastapi "uvicorn[standard]" openai pydantic python-multipart tzdata pyjwt cryptography requests`
2. Vonage dashboard > Applications > Create, enable **Voice**:
   - Answer URL: `<PUBLIC_BASE_URL>/vonage/answer` (GET)
   - Event URL: `<PUBLIC_BASE_URL>/vonage/event` (POST)
   - Generate keys, save `private.key` in this folder (never commit it).
3. Environment variables (see `.env.example`):
   `GROQ_API_KEY`, `PUBLIC_BASE_URL`, `VONAGE_APPLICATION_ID`, optional `NIGHT_PORTIER_NUMBER`.
4. Run: `uvicorn server:app --host 0.0.0.0 --port 8000`
5. Test call to your own phone: `python call_me.py 49XXXXXXXXXX`

Trial Vonage accounts can only call verified numbers.
