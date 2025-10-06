import os
import json
import random
import requests
import pytz
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# 🔧 Carregar variáveis de ambiente
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# 🤖 Inicializar bot e agendador
bot = Bot(token=TELEGRAM_TOKEN)
scheduler = BlockingScheduler()
noticias_enviadas = set()
fuso_brasil = pytz.timezone("America/Sao_Paulo")

# 🎯 Temas disponíveis
temas_disponiveis = {
    "politica": "política OR governo OR eleições",
    "esporte": "esporte OR futebol OR campeonato",
    "cultura": "cultura OR cinema OR música",
    "mundo": "internacional OR ONU OR global",
    "ciência": "ciência OR tecnologia OR descobertas",
    "celebridades": "celebridades OR famosos OR artistas"
}

# 📁 Carregar títulos já enviados
def carregar_titulos():
    global noticias_enviadas
    try:
        with open("titulos_enviados.json", "r") as f:
            noticias_enviadas = set(json.load(f))
    except:
        noticias_enviadas = set()

# 💾 Salvar títulos enviados
def salvar_titulos():
    with open("titulos_enviados.json", "w") as f:
        json.dump(list(noticias_enviadas), f)

# 🔍 Buscar notícia segura
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

# 📤 Enviar edição formatada
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

# ⏰ Carregar horários do arquivo externo
def carregar_horarios():
    try:
        with open("horarios.json", "r") as f:
            return json.load(f)
    except:
        return []

# 🔁 Agendar edições
def agendar_edicoes():
    horarios = carregar_horarios()
    for h in horarios:
        hora, minuto = map(int, h["hora"].split(":"))
        label = h["label"]
        scheduler.add_job(lambda l=label: enviar_edicao(l), 'cron', hour=hora, minute=minuto, timezone=fuso_brasil)

# 🚀 Início
if __name__ == "__main__":
    print("Jornal Amizades iniciado.")
    agendar_edicoes()
    scheduler.start()
