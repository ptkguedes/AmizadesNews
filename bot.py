import os
import requests
from telegram import Bot
from telegram.ext import ApplicationBuilder, ContextTypes
from dotenv import load_dotenv
import sys

# Carrega variáveis do .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")

# Define o turno (manha, almoco, tarde)
TURNO = "manha"
if len(sys.argv) > 1 and sys.argv[1].startswith("--turno="):
    TURNO = sys.argv[1].split("=")[1]

# Saudação personalizada por turno
saudacoes = {
    "manha": "Bom dia ☀️",
    "almoco": "Boa tarde, aproveite sua pausa 🍽️",
    "tarde": "Boa tarde 🌇"
}
saudacao = saudacoes.get(TURNO, "Olá")

# Nome da edição por turno
edicoes = {
    "manha": "Edição da Manhã",
    "almoco": "Edição do Almoço",
    "tarde": "Edição da Tarde"
}
nome_edicao = edicoes.get(TURNO, "Edição Especial")

# Função principal que envia as notícias
async def enviar_noticias(context: ContextTypes.DEFAULT_TYPE):
    url = f"https://newsapi.org/v2/everything?q=brasil&language=pt&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()

    artigos = dados.get("articles", [])[:5]
    if not artigos:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"{saudacao}, sem notícias disponíveis no momento.")
        return

    # Mensagem de abertura
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"{saudacao}, aqui está sua *{nome_edicao}* do Jornal Amizades 🗞️:",
        parse_mode="Markdown"
    )

    # Envia cada notícia
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

# Inicializa o bot
if __name__ == "__main__":
    try:
        print("Iniciando o Jornal Amizades...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.job_queue.run_once(enviar_noticias, when=0)
        app.run_polling()
    except Exception as e:
        print("❌ Erro ao iniciar o bot:")
        print(e)
