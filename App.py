from flask import Flask, request
import requests, os
from openai import OpenAI

app = Flask(__name__)

TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_ID = "1366798936510631"
VERIFY_TOKEN = "taquero123"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT = """Eres vendedor de Tacos El Taquero, Santa Tecla. Formal buena onda, corto tipo WhatsApp.
Menu: Tacos al pastor $3.99 orden de 3, Tortas $2.99, Hamburguesas $2.99.
Info: Lunes a Domingo sin cerrar, efectivo y tarjeta, delivery 5min $1.00, Viernes 2x1, pedidos grandes 2h anticipacion. Vende y cierra pedido."""

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Error", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    try:
        msg = body["entry"][0]["changes"][0]["value"]["messages"][0]
        from_num = msg["from"]
        user_text = msg["text"]["body"]
        comp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role":"system","content":PROMPT},{"role":"user","content":user_text}])
        send_whatsapp(from_num, comp.choices[0].message.content)
    except: pass
    return "OK", 200
