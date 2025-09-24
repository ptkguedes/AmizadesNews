import requests
import time
import os
import argparse
from telegram import Bot
from dotenv import load_dotenv

# 🔐 Carrega variáveis do .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")  # ID do canal ou grupo

bot = Bot(token=TELEGRAM_TOKEN)

# 🎯 Detecta o turno (manha ou tarde)
parser = argparse.ArgumentParser()
parser.add_argument("--turno", choices=["manha", "tarde"], default="manha")
args = parser.parse_args()
turno = args.turno

# 📰 Busca notícias da NewsAPI
def obter_noticias():
    url = f"https://newsapi.org/v2/top-headlines?country=br&language=pt&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()
    return dados["articles"][:8]  # pega as 8 primeiras

# 🧵 Envia o jornal como fio
def enviar_jornal():
    noticias = obter_noticias()

    # ✨ Mensagem editorial personalizada
    saudacao = "Bom dia" if turno == "manha" else "Boa tarde"
    manchetes = [f"• {n['title']}" for n in noticias]
    editorial = (
        f"🗞️ {saudacao}, caros leitores do Jornal Amizades!\n\n"
        "Hoje você começa seu dia com as seguintes notícias:\n"
        + "\n".join(manchetes) +
        "\n\nTudo isso e muito mais. Vamos juntos?\n👇"
    )
    bot.send_message(chat_id=CHAT_ID, text=editorial, disable_notification=True)

    # 📤 Envia cada notícia como mensagem separada
    for noticia in noticias:
        titulo = noticia["title"]
        resumo = noticia["description"] or "Resumo não disponível."
        fonte = noticia["source"]["name"]
        imagem = noticia["urlToImage"]

        texto = f"📰 {titulo}\n\n{resumo}\n\n📍 Fonte: {fonte}\n\nPróxima notícia 👇"

        try:
            if imagem:
                bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, disable_notification=True)
            else:
                bot.send_message(chat_id=CHAT_ID, text=texto, disable_notification=True)
        except Exception as e:
            print(f"Erro ao enviar notícia: {e}")

        time.sleep(5)  # espaçamento entre mensagens

# 🚀 Executa o envio
if __name__ == "__main__":
    enviar_jornal()
