import os
import requests
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import ApplicationBuilder, CallbackContext
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CHAT_ID = os.getenv("CHAT_ID")

# Lista de temas que se repete a cada 7 horas
temas = ["fofoca", "mundo", "esporte", "politica", "entretenimento", "fofoca", "esporte"]

# Função para buscar notícia por tema
def buscar_noticia_por_tema(tema):
    url = f"https://newsapi.org/v2/everything?q={tema}&language=pt&sortBy=publishedAt&pageSize=1&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()
    return dados.get("articles", [])[0] if dados.get("articles") else None

# Função para enviar notícia no horário agendado
def enviar_noticia_tematica(context: CallbackContext):
    tema = context.job.data
    noticia = buscar_noticia_por_tema(tema)
    if not noticia:
        context.bot.send_message(chat_id=CHAT_ID, text=f"🕒 Nenhuma notícia encontrada sobre *{tema}* agora.", parse_mode="Markdown")
        return

    titulo = noticia.get("title", "Sem título")
    descricao = noticia.get("description", "")
    url_noticia = noticia.get("url", "")
    imagem = noticia.get("urlToImage", None)

    texto = f"🕒 *{tema.upper()}*\n\n📰 *{titulo}*\n\n_{descricao}_\n\n[Leia mais]({url_noticia})"

    if imagem:
        context.bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, parse_mode="Markdown")
    else:
        context.bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

# Início do bot e agendamento das 24 horas
if __name__ == "__main__":
    try:
        print("🟢 Iniciando Jornal Amizades por hora...")
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).arbitrary_callback_data(True).build()

        # Defina o horário inicial aqui (formato HH:MM)
        hora_inicial = datetime.strptime("14:30", "%H:%M")
        agora = datetime.now()
        inicio = agora.replace(hour=hora_inicial.hour, minute=hora_inicial.minute, second=0, microsecond=0)
        if inicio < agora:
            inicio += timedelta(days=1)

        # Agenda 24 postagens com temas cíclicos
        for i in range(24):
            tema = temas[i % len(temas)]
            horario = inicio + timedelta(hours=i)
            delay = (horario - agora).total_seconds()
            app.job_queue.run_once(enviar_noticia_tematica, when=delay, data=tema)

        app.run_polling()
    except Exception as e:
        print("❌ Erro ao iniciar o bot:")
        print(e)
