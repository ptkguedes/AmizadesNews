import os
import requests
from telegram import Bot
from telegram.ext import Updater, JobQueue
from datetime import time
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "sua_chave_newsapi_aqui")
CHAT_ID = int(os.getenv("CHAT_ID", "1234567890"))

temas = [
    "fofoca", "esporte",
    "politica", "entretenimento",
    "mundo", "celebridades",
    "fofoca", "esporte",
    "politica", "entretenimento",
    "mundo", "celebridades",
    "fofoca", "esporte"
]

frases_abertura = [
    "Bom dia leitores, começamos com a primeira edição do jornal da manhã.",
    "Hora do café! Vamos às manchetes da manhã.",
    "Boa tarde! Aqui está o jornal do almoço.",
    "Fim de tarde chegando, confira as últimas.",
    "Boa noite! Veja o que está acontecendo agora.",
    "Última edição da noite chegando quente.",
    "Fim do dia, boa noite a todos e até amanhã."
]

horarios = 
[
    time(9, 12),  # 06:12 BRT
    time(12, 12), # 09:12 BRT
    time(15, 12), # 12:12 BRT
    time(18, 12), # 15:12 BRT
    time(21, 12), # 18:12 BRT
    time(0, 12),  # 21:12 BRT
    time(2, 12)   # 23:12 BRT
]

# Palavras proibidas para filtrar conteúdo sensível
palavras_proibidas = [
    "porn", "sexo", "sexual", "gore", "sangue", "assassinato",
    "violência", "explícito", "erótico", "nude", "suicídio", "decapitação"
]

def conteudo_inadequado(texto):
    texto = texto.lower()
    return any(palavra in texto for palavra in palavras_proibidas)

def buscar_noticia(tema):
    url = f"https://newsapi.org/v2/everything?q={tema}&language=pt&sortBy=publishedAt&pageSize=5&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()
    artigos = dados.get("articles", [])

    for artigo in artigos:
        titulo = artigo.get("title", "").lower()
        descricao = artigo.get("description", "").lower()
        imagem = artigo.get("urlToImage", "")
        if conteudo_inadequado(titulo) or conteudo_inadequado(descricao):
            continue
        if imagem and any(p in imagem for p in palavras_proibidas):
            continue
        return artigo

    return None

def enviar_edicao(context):
    frase = context.job.context["frase"]
    temas_edicao = context.job.context["temas"]
    bot = context.bot

    bot.send_message(chat_id=CHAT_ID, text=f"🗞️ {frase}")

    for tema in temas_edicao:
        noticia = buscar_noticia(tema)
        if not noticia:
            bot.send_message(chat_id=CHAT_ID, text=f"Nenhuma notícia segura encontrada sobre *{tema}*.", parse_mode="Markdown")
            continue

        titulo = noticia.get("title", "Sem título")
        descricao = noticia.get("description", "")
        url = noticia.get("url", "")
        imagem = noticia.get("urlToImage", None)

        texto = f"*{tema.upper()}*\n\n📰 *{titulo}*\n_{descricao}_\n\n[Leia mais]({url})"

        if imagem:
            bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, parse_mode="Markdown")
        else:
            bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

def main():
    print("🟢 Iniciando Jornal Amizades com agendamento fixo e filtro seguro...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    job_queue: JobQueue = updater.job_queue

    for i in range(7):
        job_queue.run_daily(
            enviar_edicao,
            time=horarios[i],
            context={
                "frase": frases_abertura[i],
                "temas": [temas[i * 2], temas[i * 2 + 1]]
            }
        )

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
