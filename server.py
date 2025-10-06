import os
import json
import random
import requests
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

bot = Bot(token=TELEGRAM_TOKEN)
scheduler = BlockingScheduler()
noticias_enviadas = set()

# Palavras-chave por tema
temas_disponiveis = {
    "politica": "política OR governo OR eleições",
    "esporte": "esporte OR futebol OR campeonato",
    "cultura": "cultura OR cinema OR música",
    "mundo": "internacional OR ONU OR global",
    "ciência": "ciência OR tecnologia OR descobertas",
    "celebridades": "celebridades OR famosos OR artistas"
}

def carregar_titulos():
    global noticias_enviadas
    try:
        with open("titulos_enviados.json", "r") as f:
            noticias_enviadas = set(json.load(f))
    except:
        noticias_enviadas = set()

def salvar_titulos():
    with open("titulos_enviados.json", "w") as f:
        json.dump(list(noticias_enviadas), f)

def buscar_noticia(tema):
    query = temas_disponiveis.get(tema, tema)
    url = f"https://newsapi.org/v2/everything?q={query}&language=pt&sortBy=publishedAt&pageSize=10&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    if resposta.status_code != 200:
        return None
    artigos = resposta.json().get("articles", [])
    for artigo in artigos:
        titulo = artigo.get("title", "")
        descricao = artigo.get("description", "")
        url = artigo.get("url", "")
        if not titulo or titulo in noticias_enviadas:
            continue
        if any(p in titulo.lower() for p in ["sexo", "suicídio", "violência"]):
            continue
        resumo = descricao if descricao else "Resumo indisponível."
        if len(resumo) > 200:
            resumo = resumo[:200].rsplit(" ", 1)[0] + "..."
        noticias_enviadas.add(titulo)
        salvar_titulos()
        return f"📰 *{titulo}*\n_{resumo}_\n[Leia mais]({url})"
    return None

def enviar_edicao(horario):
    carregar_titulos()
    temas = random.sample(list(temas_disponiveis.keys()), 2)
    mensagens = [f"🗞️ Jornal Amizades — Edição das {horario}"]
    for tema in temas:
        noticia = buscar_noticia(tema)
        if noticia:
            mensagens.append(noticia)
        else:
            mensagens.append(f"⚠️ Nenhuma notícia segura encontrada sobre *{tema}*.")
    texto_final = "\n\n".join(mensagens)
    bot.send_message(chat_id=GROUP_ID, text=texto_final, parse_mode="Markdown")

# Agendamentos
scheduler.add_job(lambda: enviar_edicao("07h50"), 'cron', hour=7, minute=50)
scheduler.add_job(lambda: enviar_edicao("14h10"), 'cron', hour=14, minute=10)
scheduler.add_job(lambda: enviar_edicao("21h20"), 'cron', hour=21, minute=20)

# Início
if __name__ == "__main__":
    print("Jornal Amizades iniciado.")
    scheduler.start()
