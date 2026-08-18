import os
import requests
import gradio as gr

MODAL_API_URL = os.environ.get("MODAL_API_URL", "")

def chat(message, history):
    if not message or not str(message).strip():
        return "Pesan tidak boleh kosong."

    if not MODAL_API_URL:
        return "❌ MODAL_API_URL belum di-set di Environment Variables Railway."

    try:
        response = requests.post(
            MODAL_API_URL, 
            json={"prompt": message}, 
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("result", "Tidak ada respon dari model.")
        return f"❌ Error API ({response.status_code}): {response.text}"
    except Exception as e:
        return f"❌ Failure: {str(e)}"

# UI Gradio
with gr.Blocks(title="AI Bot Console") as demo:
    gr.Markdown("# 🤖 AI Bot (Railway UI + Modal GPU)")
    gr.Markdown("UI berjalan di Railway (CPU) dan pemrosesan AI di Modal.com (GPU T4)")
    
    chatbot = gr.ChatInterface(fn=chat)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
