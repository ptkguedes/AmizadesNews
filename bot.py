import os
import json
import requests
import random
import time
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
ENDPOINT_EXECUTAR = os.getenv("ENDPOINT_EXECUTAR")

noticias_enviadas = set()
ultimo_teste = 0
INTERVALO_TESTE = 600  # 10 minutos

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

def salvar_titulos():
    try:
        with open("titulos_enviados.json", "w") as f:
            json.dump(list(noticias_enviadas), f)
    except:
        pass

def carregar_titulos():
    global noticias_enviadas
    try:
        with open("titulos_enviados.json", "r") as f:
            noticias_enviadas = set(json.load(f))
    except:
        noticias_enviadas = set()

def conteudo_inadequado(texto):
    texto = texto.lower()
    palavras_18 = ["porn", "sexo", "sexual", "erótico", "nude", "nudes", "suicídio", "decapitação", "bestialismo", "incesto"]
    return any(p in texto for p in palavras_18)

def resumir_texto(texto):
    if not texto:
        return "Resumo indisponível."
    texto = texto.strip().replace("\n", " ")
    if len(texto) > 200:
        texto = texto[:200].rsplit(" ", 1)[0] + "..."
    return texto

def buscar_noticia(tema):
    query = palavras_chave.get(tema, tema)
    url = f"https://newsapi.org/v2/everything?q={query}&language=pt&sortBy=publishedAt&pageSize=10&apiKey={NEWSAPI_KEY}"
    resposta = requests.get(url)
    if resposta.status_code != 200:
        return None
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
        noticias_enviadas.add(titulo)
        salvar_titulos()
        artigo["resumo"] = resumir_texto(descricao)
        return artigo
    return None

def buscar_noticia_manual(tema):
    fontes = {
        "politica": {
            "titulo": "Ministro do Planalto nega saída do cargo",
            "resumo": "Márcio Macêdo minimiza rumores e diz que nunca tratou saída com o presidente.",
            "url": "https://www.metropoles.com/brasil/ministro-do-planalto-nega-saida-do-cargo"
        }
    }
    if tema in fontes:
        noticia = fontes[tema]
        noticia["resumo"] = resumir_texto(noticia["resumo"])
        noticia["title"] = noticia["titulo"]
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
    frase = context["job"]["context"]["frase"]
    temas_edicao = context["job"]["context"]["temas"]
    bot = context["bot"]
    bot.send_message(chat_id=CHAT_ID, text=frase)
    for tema in temas_edicao:
        noticia = obter_noticia_segura(tema)
        if not noticia:
            enviar_link_util(bot, tema)
            continue
        enviar_noticia_formatada(bot, noticia, tema)

def comando_teste(update: Update, context):
    global ultimo_teste
    chat = update.effective_chat
    if chat.type != "private" or chat.id != CHAT_ID:
        update.message.reply_text("Este comando só pode ser usado pelo administrador em chat privado.")
        return
    agora = time.time()
    if agora - ultimo_teste < INTERVALO_TESTE:
        update.message.reply_text("Aguarde um pouco antes de usar o comando novamente.")
        return
    ultimo_teste = agora
    update.message.reply_text("conteúdo teste sendo enviado ao grupo")
    try:
        resposta = requests.get(ENDPOINT_EXECUTAR)
        if resposta.status_code == 200:
            update.message.reply_text("✅ Edição acionada com sucesso.")
        else:
            update.message.reply_text(f"⚠️ Erro ao acionar edição: {resposta.status_code}")
    except Exception as e:
        update.message.reply_text(f"❌ Falha na conexão: {e}")

def main():
    carregar_titulos()
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    updater.dispatcher.add_handler(CommandHandler("teste", comando_teste))
    updater.start_polling()
    updater.idle()
