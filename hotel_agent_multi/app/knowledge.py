import os

KNOWLEDGE_PATH = os.path.join("knowledge", "hotel_bayerischer_hof.md")

def load_hotel_knowledge() -> str:
    if not os.path.exists(KNOWLEDGE_PATH):
        return "Keine Hotelinformationen verfügbar."
    with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
        return f.read()
