import os
from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# Ambil token dan port dari pengaturan internal Railway
HF_TOKEN = os.environ.get("HF_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# MENGGUNAKAN MODEL LLAMA-3 YANG LEBIH STABIL
API_URL = "https://huggingface.co"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Chatbot Bakri</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); border-radius: 8px; }
        .chat-box { height: 300px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin-bottom: 20px; background: #f9f9f9; border-radius: 4px; }
        input[type="text"] { width: 75%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 20%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .user { color: blue; margin-bottom: 5px; }
        .ai { color: green; margin-bottom: 15px; }
    </style>
</head>
<body>
    <h2>🤖 AI Chatbot Bakri</h2>
    <div class="chat-box">
        {% if user_msg %}
            <div class="user"><b>Kamu:</b> {{ user_msg }}</div>
            <div class="ai"><b>AI:</b> {{ ai_reply }}</div>
        {% else %}
            <div class="ai"><b>AI:</b> Halo! Ada yang bisa saya bantu hari ini?</div>
        {% endif %}
    </div>
    <form method="POST">
        <input type="text" name="message" placeholder="Ketik pesan di sini..." required autocomplete="off">
        <button type="submit">Kirim</button>
    </form>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_msg = request.form["message"]
        
        payload = {
            "inputs": user_msg,
            "parameters": {"max_new_tokens": 150}
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            result = response.json()
            
            # Sistem pengecekan respon otomatis (agar terhindar dari error 'Expecting value')
            if isinstance(result, list) and len(result) > 0:
                ai_reply = result[0].get('generated_text', 'Format teks kosong').strip()
            elif isinstance(result, dict):
                if "estimated_time" in result:
                    ai_reply = "Server Hugging Face sedang memuat model. Silakan kirim ulang pesan ini dalam 20 detik."
                elif "error" in result:
                    ai_reply = f"Pesan dari Hugging Face: {result['error']}"
                else:
                    ai_reply = str(result)
            else:
                ai_reply = f"Menerima respon tidak dikenal: {str(result)}"
                
        except Exception as e:
            ai_reply = f"Terjadi kendala koneksi ke AI: {str(e)}"

        return render_template_string(HTML_TEMPLATE, user_msg=user_msg, ai_reply=ai_reply)
        
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
