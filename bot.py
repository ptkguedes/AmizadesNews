import os
import requests
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, CallbackContext
from dotenv import load_dotenv

# Carrega variáveis do .env (usado localmente, ignorado no Discloud)
load_dotenv()

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "sua_chave_newsapi_aqui")
CHAT_ID = os.getenv("CHAT_ID", "1234567890")

# Verificação de variáveis obrigatórias
if not TELEGRAM_TOKEN or not NEWSAPI_KEY or not CHAT_ID:
    print("❌ Erro: Variáveis de ambiente ausentes ou inválidas.")
    exit(1)

# Ordem temática fixa
temas = ["fofoca", "esporte", "politica", "entretenimento", "mundo", "celebridades"]

def buscar_noticia_por_tema(tema):
    url = f"https://newsapi.org/v2/everything?q={tema}&language=pt&sortBy=publishedAt&pageSize=1&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()
    return dados.get("articles", [])[0] if dados.get("articles") else None

async def enviar_noticia(context: CallbackContext):
    tema = context.job.data
    noticia = buscar_noticia_por_tema(tema)

    if not noticia:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"🕒 Nenhuma notícia encontrada sobre *{tema}* agora.", parse_mode="Markdown")
        return

    titulo = noticia.get("title", "Sem título")
    descricao = noticia.get("description", "")
    url_noticia = noticia.get("url", "")
    imagem = noticia.get("urlToImage", None)

    texto = f"🕒 *{tema.upper()}*\n\n📰 *{titulo}*\n\n_{descricao}_\n\n[Leia mais]({url_noticia})"

    if imagem:
        await context.bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

async def main():
    print("🟢 Iniciando Jornal Amizades por hora...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    hora_inicial = datetime.strptime("07:00", "%H:%M")  # horário de início
    agora = datetime.now()
    inicio = agora.replace(hour=hora_inicial.hour, minute=hora_inicial.minute, second=0, microsecond=0)
    if inicio < agora:
        inicio += timedelta(days=1)

    for i in range(24):
        tema = temas[i % len(temas)]
        horario = inicio + timedelta(hours=i)
        delay = (horario - agora).total_seconds()
        app.job_queue.run_once(enviar_noticia, when=delay, data=tema)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print("❌ Erro ao iniciar o bot:")
        print(e)
