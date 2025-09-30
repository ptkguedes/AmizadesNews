import os
import requests
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from dotenv import load_dotenv
import sys

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")

TURNO = "manha"
if len(sys.argv) > 1 and sys.argv[1].startswith("--turno="):
    TURNO = sys.argv[1].split("=")[1]

async def enviar_noticias(context: ContextTypes.DEFAULT_TYPE):
    saudacao = "Bom dia" if TURNO == "manha" else "Boa tarde"
    url = f"https://newsapi.org/v2/everything?q=brasil&language=pt&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()

    artigos = dados.get("articles", [])[:5]
    if not artigos:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"{saudacao}, sem notícias disponíveis no momento.")
        return

    await context.bot.send_message(chat_id=CHAT_ID, text=f"{saudacao}, aqui está sua edição do Jornal Amizades 🗞️:")

    for artigo in artigos:
        titulo = artigo.get("title", "Sem título")
        descricao = artigo.get("description", "")
        url_noticia = artigo.get("url", "")
        imagem = artigo.get("urlToImage", None)

        texto = f"📰 *{titulo}*\n\n_{descricao}_\n\n[Leia mais]({url_noticia})"
        if imagem:
            await context.bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.job_queue.run_once(enviar_noticias, when=0)
    app.run_polling()
