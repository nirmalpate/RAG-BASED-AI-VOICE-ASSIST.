import os
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI
from app.knowledge import load_hotel_knowledge
from app.call_log import CallLogger

class HotelAgent:
    def __init__(self, call_id: str, caller_number: str = "Unbekannt"):
        self.call_id = call_id
        self.caller_number = caller_number
        self.logger = CallLogger(call_id)
        
        self.client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY")
        )
        self.model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        
        self.transfer_requested = False
        current_hour = datetime.now(ZoneInfo("Europe/Berlin")).hour
        self.is_night_shift = current_hour >= 21 or current_hour < 6
        self.night_mode_engaged = self.is_night_shift
        
        knowledge_text = load_hotel_knowledge()
        self.system_prompt = f"""Du bist der exklusive, charmante digitale Telefon-Assistent des 5-Sterne-Hotels Bayerischer Hof in München.
Nutze folgendes Wissen, um Fragen präzise zu beantworten:
{knowledge_text}

Regeln:
- Antworte extrem kurz, höflich und in exzellentem Deutsch (maximal 1-2 kurze Sätze für das Telefongespräch).
- Nenne nur Fakten aus dem Wissen.
"""
        self.history = [{"role": "system", "content": self.system_prompt}]

    def reply(self, user_text: str) -> str:
        self.logger.log_turn("user", user_text)
        
        if self.is_night_shift and self.night_mode_engaged:
            lower_text = user_text.lower()
            emergency_keywords = ["notfall", "schlüssel", "brand", "krank", "arzt", "aufsperren", "hilfe", "not", "problem"]
            is_emergency = any(kw in lower_text for kw in emergency_keywords)
            
            if is_emergency:
                answer = "Das verstehe ich. Ich verbinde Sie in unserem Nachtservice sofort mit dem diensthabenden Portier des Hotel Bayerischer Hof. Bitte bleiben Sie dran."
                self.transfer_requested = True
                self.logger.log_turn("assistant", answer)
                self.history.append({"role": "user", "content": user_text})
                self.history.append({"role": "assistant", "content": answer})
                return answer
            else:
                self.night_mode_engaged = False

        self.history.append({"role": "user", "content": user_text})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            max_tokens=400,
            temperature=0.3
        )
        
        answer = (response.choices[0].message.content or "").strip()
        if not answer:
            answer = "Entschuldigung, könnten Sie das bitte noch einmal sagen?"
        
        self.history.append({"role": "assistant", "content": answer})
        self.logger.log_turn("assistant", answer)
        
        return answer
