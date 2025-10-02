import os
import requests
from telegram import Bot
from telegram.ext import Updater, JobQueue
from datetime import time, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "sua_chave_newsapi_aqui")
CHAT_ID = int(os.getenv("CHAT_ID", "1234567890"))

frases_abertura = [
    "Bom dia leitores, começamos com a primeira edição do jornal da manhã.",     # 06:12
    "Hora do café! Vamos às manchetes da manhã.",                                # 09:12
    "Boa tarde! Aqui está o jornal do almoço.",                                  # 12:12
    "Fim de tarde chegando, confira as últimas.",                                # 15:12
    "Boa noite! Veja o que está acontecendo agora.",                             # 18:12
    "Última edição da noite chegando quente.",                                   # 21:12
    "Fim do dia, boa noite a todos e até amanhã."                                # 23:12
]

# Horários em UTC para bater com Brasília (UTC-3)
horarios = [
    time(9, 12),  # 06:12 BRT
    time(12, 12), # 09:12 BRT
    time(15, 12), # 12:12 BRT
    time(18, 12), # 15:12 BRT
    time(21, 12), # 18:12 BRT
    time(0, 12),  # 21:12 BRT
    time(2, 12)   # 23:12 BRT
]

# Temas fixos por horário
temas_por_horario = [
    ["fofoca", "celebridades"],
    ["esporte", "mundo"],
    ["politica", "entretenimento"],
    ["fofoca", "esporte"],
    ["politica", "celebridades"],
    ["entretenimento", "mundo"],
    ["fofoca", "politica"]
]

# Palavras proibidas para filtrar conteúdo sensível
palavras_proibidas = [
    "porn", "sexo", "sexual", "gore", "sangue", "assassinato",
    "violência", "explícito", "erótico", "nude", "suicídio", "decapitação"
]

# Títulos já enviados para evitar repetição
noticias_enviadas = set()

# Palavras-chave por tema
palavras_chave = {
    "fofoca": "fofoca OR escândalo OR celebridades",
    "esporte": "esporte OR futebol OR campeonato OR olimpíadas",
    "politica": "política OR governo OR eleições OR congresso OR presidente",
    "entretenimento": "entretenimento OR cinema OR séries OR música",
    "mundo": "mundo OR internacional OR global OR ONU",
    "celebridades": "celebridades OR famosos OR artistas OR influenciadores"
}

# Emojis por tema
emojis_por_tema = {
    "fofoca": "🕵️",
    "esporte": "⚽",
    "politica": "🗳️",
    "entretenimento": "🎬",
    "mundo": "🌍",
    "celebridades": "🧑‍🎤"
}

def conteudo_inadequado(texto):
    texto = texto.lower()
    return any(palavra in texto for palavra in palavras_proibidas)

def resumir_texto(texto):
    if not texto:
        return "Resumo indisponível."
    texto = texto.strip().replace("\n", " ")
    if len(texto) > 200:
        texto = texto[:200].rsplit(" ", 1)[0] + "..."
    return texto

def buscar_noticia(tema):
    query = palavras_chave.get(tema, tema)
    url = f"https://newsapi.org/v2/everything?q={query}&language=pt&sortBy=publishedAt&pageSize=5&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    dados = resposta.json()
    artigos = dados.get("articles", [])

    for artigo in artigos:
        titulo = artigo.get("title", "")
        descricao = artigo.get("description", "")
        imagem = artigo.get("urlToImage", "")
        publicado = artigo.get("publishedAt", "")

        if titulo in noticias_enviadas:
            continue
        if conteudo_inadequado(titulo) or conteudo_inadequado(descricao):
            continue
        if imagem and any(p in imagem for p in palavras_proibidas):
            continue

        try:
            publicado_dt = datetime.fromisoformat(publicado.replace("Z", "+00:00"))
            if datetime.utcnow() - publicado_dt > timedelta(hours=24):
                continue
        except:
            continue

        noticias_enviadas.add(titulo)
        artigo["resumo"] = resumir_texto(descricao)
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
        resumo = noticia.get("resumo", "")
        url = noticia.get("url", "")
        imagem = noticia.get("urlToImage", None)
        emoji = emojis_por_tema.get(tema, "📰")

        texto = f"{emoji} *{tema.upper()}*\n\n📰 *{titulo}*\n_{resumo}_\n\n[Leia mais]({url})"

        if imagem:
            bot.send_photo(chat_id=CHAT_ID, photo=imagem, caption=texto, parse_mode="Markdown")
        else:
            bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

def main():
    print("🟢 Iniciando Jornal Amizades com agendamento fixo, temas por horário e filtro seguro...")
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    job_queue: JobQueue = updater.job_queue

    for i in range(7):
        job_queue.run_daily(
            enviar_edicao,
            time=horarios[i],
            context={
                "frase": frases_abertura[i],
                "temas": temas_por_horario[i]
            }
        )

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
