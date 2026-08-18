import gradio as gr
from openai import OpenAI
import os
import spaces
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# ===== Config =====
JOINGONKA_KEY = os.environ.get("JOINGONKA_API_KEY")
BYBIT_KEY = os.environ.get("BYBIT_API_KEY")
BYBIT_SECRET = os.environ.get("BYBIT_API_SECRET")
BYBIT_BASE = "https://api-demo.bybit.com"   # Demo

if not JOINGONKA_KEY:
    raise ValueError("JOINGONKA_API_KEY belum di-set")

client = OpenAI(
    base_url="https://gate.joingonka.ai/v1",
    api_key=JOINGONKA_KEY
)

# ===== Bybit Helper =====
def bybit_request(method, endpoint, params=None):
    if not BYBIT_KEY or not BYBIT_SECRET:
        return {"error": "Bybit API Key/Secret belum di-set di Secrets"}

    params = params or {}
    timestamp = str(int(time.time() * 1000))
    params["api_key"] = BYBIT_KEY
    params["timestamp"] = timestamp
    params["recv_window"] = 5000

    query = urlencode(sorted(params.items()))
    signature = hmac.new(
        BYBIT_SECRET.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    params["sign"] = signature

    url = f"{BYBIT_BASE}{endpoint}"
    try:
        if method == "GET":
            res = requests.get(url, params=params, timeout=10)
        else:
            res = requests.post(url, data=params, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_balance():
    data = bybit_request("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})
    return data

def get_positions():
    data = bybit_request("GET", "/v5/position/list", {"category": "linear", "settleCoin": "USDT"})
    return data

# ===== Chat Function =====
@spaces.GPU
def chat(message, history, model_name):
    if not message or not str(message).strip():
        return "Pesan kosong."

    lower_msg = message.lower()

    # Command khusus
    if "saldo" in lower_msg or "balance" in lower_msg:
        bal = get_balance()
        return f"📊 Hasil cek saldo Demo:\n\n```json\n{bal}\n```"

    if "posisi" in lower_msg or "position" in lower_msg:
        pos = get_positions()
        return f"📈 Posisi saat ini:\n\n```json\n{pos}\n```"

    # Normal chat ke joingonka
    messages = []
    if history:
        for item in history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                human, assistant = item
                messages.append({"role": "user", "content": str(human)})
                messages.append({"role": "assistant", "content": str(assistant)})
            elif isinstance(item, dict):
                messages.append(item)

    messages.append({"role": "user", "content": str(message)})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error LLM:\n\n{type(e).__name__}: {str(e)}"

# ===== UI =====
with gr.Blocks(title="Gonka + Bybit Demo") as demo:
    gr.Markdown("# 🤖 Gonka AI + Bybit Demo")
    gr.Markdown("Bisa ngobrol, cek saldo, dan cek posisi (Demo Account)")

    model_dropdown = gr.Dropdown(
        choices=[
            "MiniMaxAI/MiniMax-M2.7",
            "moonshotai/Kimi-K2.6",
            "deepseek-ai/DeepSeek-V4-Flash-0731"
        ],
        value="MiniMaxAI/MiniMax-M2.7",
        label="Pilih Model"
    )

    chatbot = gr.ChatInterface(
        fn=chat,
        additional_inputs=[model_dropdown],
        examples=[
            ["Halo", "MiniMaxAI/MiniMax-M2.7"],
            ["Cek saldo saya", "MiniMaxAI/MiniMax-M2.7"],
            ["Lihat posisi saya", "MiniMaxAI/MiniMax-M2.7"],
            ["Analisis BTC sekarang", "MiniMaxAI/MiniMax-M2.7"]
        ]
    )

demo.launch()
