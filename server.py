from flask import Flask
from telegram import Bot
import os
from bot import enviar_edicao, carregar_titulos

app = Flask(__name__)
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
CHAT_ID = int(os.getenv("CHAT_ID"))

@app.route("/")
def home():
    return "Servidor do Jornal Amizades está ativo!", 200

@app.route("/executar")
def executar_edicao():
    carregar_titulos()
    context = {
        "bot": bot,
        "job": {"context": {
            "frase": "🗞️ Edição acionada via webhook",
            "temas": ["politica", "mundo"]
        }}
    }
    enviar_edicao(context)
    return "Edição enviada!", 200

if __name__ == "__main__":
    app.run()
