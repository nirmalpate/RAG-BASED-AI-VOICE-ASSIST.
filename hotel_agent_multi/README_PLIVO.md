# Plivo setup

1. `pip install -r requirements.txt`
2. `export GROQ_API_KEY=... PUBLIC_BASE_URL=https://<your-ngrok>.ngrok-free.app`
3. `uvicorn server:app --port 8000` and `ngrok http 8000`
4. Plivo Console > Voice > XML Applications > Create:
   - Answer URL: `https://<ngrok>/voice`, method POST
   - Hangup URL: `https://<ngrok>/hangup`, method POST
5. Attach the application to your Plivo number (Phone Numbers > your number > Application Type XML).
6. Call the number.
Trial accounts can only call/receive from verified numbers.

# Vonage (works from Germany)
Endpoints: /vonage/answer (GET), /vonage/input, /vonage/event
1. Vonage dashboard > Applications > Create. Enable "Voice".
   - Answer URL: <PUBLIC_BASE_URL>/vonage/answer (GET)
   - Event URL:  <PUBLIC_BASE_URL>/vonage/event (POST)
   Click "Generate public and private key" - save private.key into this folder. Copy the Application ID.
2. pip install pyjwt cryptography requests
3. export VONAGE_APPLICATION_ID=... PUBLIC_BASE_URL=...
4. python call_me.py 491774499545   (your own number, digits only, with country code)
   Your phone rings; answer it and speak German to the bot.
Trial accounts can only call numbers you verified in the dashboard.
