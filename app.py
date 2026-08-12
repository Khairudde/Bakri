import os
from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

# Mengambil token Hugging Face & Port dari environment variable Railway
HF_TOKEN = os.environ.get("HF_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

# Kita gunakan model open-source gratis yang andal untuk chat
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://huggingface.co{MODEL_ID}"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Desain tampilan chat web sederhana (HTML & CSS)
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
    <div class="chat-box" id="chatBox">
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
        
        # Format prompt agar model mengerti ini adalah percakapan instruksi
        payload = {
            "inputs": f"<s>[INST] {user_msg} [/INST]",
            "parameters": {"max_new_tokens": 250, "temperature": 0.7}
        }
        
        # Menembak API Hugging Face
        response = requests.post(API_URL, headers=headers, json=payload)
        
        try:
            # Mengambil teks jawaban dari respon JSON Hugging Face
            result = response.json()
            ai_reply = result[0]['generated_text'].split("[/INST]")[-1].strip()
        except Exception:
            ai_reply = "Maaf, server AI sedang sibuk atau token belum diatur dengan benar."

        return render_template_string(HTML_TEMPLATE, user_msg=user_msg, ai_reply=ai_reply)
        
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
