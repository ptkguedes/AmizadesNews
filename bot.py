import os
import json
import requests
from telegram import Bot
from telegram.ext import Updater, JobQueue
from datetime import time, datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
CHAT_ID = int(os.getenv("CHAT_ID"))

frases_abertura = [
    "Bom dia leitores, começamos com a primeira edição do jornal da manhã.",
    "Hora do café! Vamos às manchetes da manhã.",
    "Boa tarde! Aqui está o jornal do almoço.",
    "Fim de tarde chegando, confira as últimas.",
    "Boa noite! Veja o que está acontecendo agora.",
    "Última edição da noite chegando quente.",
    "Fim do dia, boa noite a todos e até amanhã."
]

horarios = [
    time(9, 12),  # 06:12 BRT
    time(12, 12), # 09:12 BRT
    time(15, 12), # 12:12 BRT
    time(18, 12), # 15:12 BRT
    time(21, 12), # 18:12 BRT
    time(0, 12),  # 21:12 BRT
    time(2, 12)   # 23:12 BRT
]

temas_por_horario = [
    ["fofoca", "celebridades"],
    ["esporte", "mundo"],
    ["politica", "entretenimento"],
    ["fofoca", "esporte"],
    ["politica", "celebridades"],
    ["entretenimento", "mundo"],
    ["fofoca", "politica"]
]

noticias_enviadas = set()

def salvar_titulos():
    try:
        with open("titulos_enviados.json", "w") as f:
            json.dump(list(noticias_enviadas), f)
    except Exception as e:
        print(f"[ERRO] ao salvar títulos: {e}")

def carregar_titulos():
    global noticias_enviadas
    try:
        with open("titulos_enviados.json", "r") as f:
            noticias_enviadas = set(json.load(f))
    except:
        noticias_enviadas = set()

def conteudo_inadequado(texto):
    texto = texto.lower()
    palavras_18 = [
        "porn", "sexo", "sexual", "erótico", "nude", "nudes",
        "suicídio", "decapitação", "bestialismo", "incesto"
    ]
    return any(p in texto for p in palavras_18)

def resumir_texto(texto):
    if not texto:
        return "Resumo indisponível."
    texto = texto.strip().replace("\n", " ")
    if len(texto) > 200:
        texto = texto[:200].rsplit(" ", 1)[0] + "..."
    return texto

palavras_chave = {
    "fofoca": "fofoca OR escândalo OR celebridades",
    "esporte": "esporte OR futebol OR campeonato OR olimpíadas",
    "politica": "política OR governo OR eleições OR congresso OR presidente",
    "entretenimento": "entretenimento OR cinema OR séries OR música",
    "mundo": "mundo OR internacional OR global OR ONU",
    "celebridades": "celebridades OR famosos OR artistas OR influenciadores"
}

emojis_por_tema = {
    "fofoca": "🕵️",
    "esporte": "⚽",
    "politica": "🗳️",
    "entretenimento": "🎬",
    "mundo": "🌍",
    "celebridades": "🧑‍🎤"
}

def buscar_noticia(tema):
    query = palavras_chave.get(tema, tema)
    url = f"https://newsapi.org/v2/everything?q={query}&language=pt&sortBy=publishedAt&pageSize=10&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)

    if resposta.status_code != 200:
        print(f"[ERRO] NewsAPI falhou para tema '{tema}'")
        return None

    dados = resposta.json()
    artigos = dados.get("articles", [])
    print(f"[INFO] {len(artigos)} artigos recebidos para tema '{tema}'")

    for artigo in artigos:
        titulo = artigo.get("title", "")
        descricao = artigo.get("description", "")
        imagem = artigo.get("urlToImage", "")
        publicado = artigo.get("publishedAt", "")

        if titulo in noticias_enviadas:
            continue
        if conteudo_inadequado(titulo) or conteudo_inadequado(descricao):
            continue

        try:
            publicado_dt = datetime.fromisoformat(publicado.replace("Z", "+00:00"))
            if datetime.utcnow() - publicado_dt > timedelta(hours=24):
                continue
        except:
            continue

        noticias_enviadas.add(titulo)
        salvar_titulos()
        artigo["resumo"] = resumir_texto(descricao)
        return artigo

    return None

def buscar_noticia_manual(tema):
    fontes = {
        "politica": {
            "titulo": "Ministro do Planalto nega saída do cargo: “Fofoca e cerco político”",
            "resumo": "Márcio Macêdo minimiza rumores e diz que nunca tratou saída com o presidente.",
            "url": "https://www.metropoles.com/brasil/ministro-do-planalto-nega-saida-do-cargo-fofoca-e-cerco-politico"
        },
        "fofoca": {
            "titulo": "Márcio Macêdo ironiza rumores: “Já posso pedir música no Fantástico”",
            "resumo": "Ministro brinca com especulações sobre sua saída do governo e chama de fofoca política.",
            "url": "https://www.otempo.com.br/politica/governo/2025/9/26/cerco-politico-e-fofoca-marcio-macedo-minimiza-rumores-de-saida-do-governo-lula"
        }
    }

    if tema in fontes:
        noticia = fontes[tema]
        noticia["resumo"] = resumir_texto(noticia["resumo"])
        noticia["title"] = noticia["titulo"]
        noticia["url"] = noticia["url"]
        noticia["urlToImage"] = None
        return noticia

    return None

def enviar_link_util(bot, tema):
    url = f"https://news.google.com/search?q={tema}"
    texto = f"⚠️ Nenhuma notícia segura encontrada sobre *{tema}*. Veja mais em [Google News]({url})"
    bot.send_message(chat_id=CHAT_ID, text=texto, parse_mode="Markdown")

def enviar_noticia_formatada(bot, noticia, tema):
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

def obter_noticia_segura(tema):
    noticia = buscar_noticia(tema)
    if noticia:
        return noticia
    noticia = buscar_noticia_manual(tema)
    if noticia:
        return noticia
    return None

def enviar_edicao(context):
    frase = context.job.context["frase"]
    temas_edicao = context.job.context["temas"]
    bot = context.bot

    bot.send_message(chat_id=CHAT_ID, text=f"🗞️ {frase}")
    print(f"[ENVIO] Iniciando edição: {frase}")

    for tema in temas_edicao:
        noticia = obter_noticia_segura(tema)
        if not noticia:
            enviar_link_util(bot, tema)
            continue
        enviar_noticia_formatada(bot, noticia, tema)

def main():
    print("🟢 Iniciando Jornal Amizades com persistência e filtro inteligente…")
    carregar_titulos()
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
