import os, logging, threading
from flask import Flask, request
import requests
from openai import OpenAI

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "taquero123")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED = os.getenv("ALLOWED_NUMBERS", "50360280872")

client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

def send_whatsapp(to, text):
    try:
        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
        data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text[:4000]}}
        r = requests.post(url, headers=headers, json=data, timeout=15)
        logging.info(f"Meta: {r.status_code} - {r.text[:200]}")
    except Exception as e:
        logging.error(f"Error enviando: {e}")

def process_message(from_number, text):
    logging.info(f"Procesando de {from_number}: {text}")
    if ALLOWED and from_number not in ALLOWED:
        send_whatsapp(from_number, "⛔ No estás autorizado.")
        return
    try:
        prompt = f"Eres el Taquero-bot, amable y corto. Cliente dice: {text}. Responde en español ofreciendo tacos."
        if client:
            resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], max_tokens=300)
            reply = resp.choices[0].message.content
        else:
            reply = f"¡Hola! Recibí: {text}. 🌮 ¿Cuántos tacos quieres?"
        send_whatsapp(from_number, reply)
    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        send_whatsapp(from_number, f"Recibí tu mensaje: {text} 🌮 ¿Qué tacos quieres?")

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Error token", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    logging.info(f"Webhook POST: {data}")
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            from_number = msg["from"]
            text = msg.get("text", {}).get("body", "")
            # Procesar en segundo plano y responder 200 YA
            threading.Thread(target=process_message, args=(from_number, text)).start()
    except Exception as e:
        logging.error(f"Webhook parse error: {e}")
    return "OK", 200

@app.route("/")
def home():
    return "Taquero-bot Live 🌮", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
