import os
import time
import hmac
import hashlib
import requests
import gradio as gr
from openai import OpenAI

# ===== Config =====
JOINGONKA_KEY = os.environ.get("JOINGONKA_API_KEY")
BYBIT_KEY = os.environ.get("BYBIT_API_KEY", "")
BYBIT_SECRET = os.environ.get("BYBIT_API_SECRET", "")
BYBIT_BASE = "https://api-demo.bybit.com"   # Demo Account

if not JOINGONKA_KEY:
    raise ValueError("JOINGONKA_API_KEY belum di-set di Variables Railway")

client = OpenAI(
    base_url="https://gate.joingonka.ai/v1",
    api_key=JOINGONKA_KEY
)

# ===== Bybit V5 Helper =====
def bybit_request(method, endpoint, params=None):
    if not BYBIT_KEY or not BYBIT_SECRET:
        return {"error": "Bybit API Key/Secret belum di-set di Variables"}

    params = params or {}
    timestamp = str(int(time.time() * 1000))
    recv_window = "5000"
    
    if method == "GET":
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())]) if params else ""
        param_str = timestamp + BYBIT_KEY + recv_window + query_string
        url_payload = f"{BYBIT_BASE}{endpoint}?{query_string}" if query_string else f"{BYBIT_BASE}{endpoint}"
        body_payload = None
    else:
        # POST Request (Perlu JSON String untuk Body Signature)
        import json
        body_payload = json.dumps(params)
        param_str = timestamp + BYBIT_KEY + recv_window + body_payload
        url_payload = f"{BYBIT_BASE}{endpoint}"

    signature = hmac.new(
        BYBIT_SECRET.encode("utf-8"),
        param_str.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "X-BAPI-API-KEY": BYBIT_KEY,
        "X-BAPI-TIMESTAMP": timestamp,
        "X-BAPI-SIGN": signature,
        "X-BAPI-RECV-WINDOW": recv_window,
        "Content-Type": "application/json"
    }

    try:
        if method == "GET":
            res = requests.get(url_payload, headers=headers, timeout=10)
        else:
            res = requests.post(url_payload, headers=headers, data=body_payload, timeout=10)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_balance():
    return bybit_request("GET", "/v5/account/wallet-balance", {"accountType": "UNIFIED"})

def get_positions():
    return bybit_request("GET", "/v5/position/list", {"category": "linear", "settleCoin": "USDT"})

# Fungsi Buka Posisi (Trading)
def place_order(symbol, side, qty):
    """
    side: 'Buy' atau 'Sell'
    qty: jumlah (misal '0.01' untuk BTCUSDT)
    """
    params = {
        "category": "linear",
        "symbol": symbol.upper(),
        "side": side,
        "orderType": "Market",
        "qty": str(qty),
        "timeInForce": "GTC"
    }
    return bybit_request("POST", "/v5/order/create", params)

# ===== Chat Function dengan Streaming =====
def chat(message, history, model_name):
    if not message or not str(message).strip():
        yield "Pesan kosong."
        return

    lower_msg = message.lower().strip()

    # 1. Command Cek Saldo
    if "saldo" in lower_msg or "balance" in lower_msg:
        bal = get_balance()
        yield f"📊 Hasil cek saldo Demo:\n\n```json\n{bal}\n```"
        return

    # 2. Command Cek Posisi
    if "posisi" in lower_msg or "position" in lower_msg:
        pos = get_positions()
        yield f"📈 Posisi saat ini:\n\n```json\n{pos}\n```"
        return

    # 3. Command Trading (Contoh: "buy btcusdt 0.001" atau "sell ethusdt 0.01")
    parts = lower_msg.split()
    if len(parts) == 3 and parts[0] in ["buy", "sell"]:
        side = "Buy" if parts[0] == "buy" else "Sell"
        symbol = parts[1].upper()
        qty = parts[2]
        
        yield f"⏳ Sedang mengirim order {side} {symbol} sejumlah {qty}..."
        order_res = place_order(symbol, side, qty)
        yield f"🚀 Response Order Demo Bybit:\n\n```json\n{order_res}\n```"
        return

    # 4. Chat ke LLM Joingonka
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
            max_tokens=2048,
            stream=True
        )
        
        partial_text = ""
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                partial_text += chunk.choices[0].delta.content
                yield partial_text
                
    except Exception as e:
        yield f"❌ Error LLM:\n\n{type(e).__name__}: {str(e)}"

# ===== UI =====
with gr.Blocks(title="Gonka + Bybit Demo") as demo:
    gr.Markdown("# 🤖 Gonka AI + Bybit Demo Trader")
    gr.Markdown("Bisa ngobrol, cek saldo, cek posisi, dan **buka order trading**!")

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
            ["buy btcusdt 0.001", "MiniMaxAI/MiniMax-M2.7"],
            ["sell btcusdt 0.001", "MiniMaxAI/MiniMax-M2.7"],
            ["Cek saldo saya", "MiniMaxAI/MiniMax-M2.7"],
            ["Lihat posisi saya", "MiniMaxAI/MiniMax-M2.7"]
        ]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
