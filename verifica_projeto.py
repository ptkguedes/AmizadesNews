import os
import re

# Arquivos obrigatórios
arquivos_essenciais = ["bot.py", "requirements.txt", "discloud.config"]

# Regras de segurança
requisitos_validos = [
    "python-telegram-bot[job-queue]==20.6",
    "requests==2.31.0",
    "python-dotenv==1.0.1"
]

# Pastas que devem ser removidas
pastas_indesejadas = ["__pycache__", ".venv", ".idea", ".mypy_cache"]

def verificar_arquivos():
    print("🔍 Verificando arquivos essenciais...")
    for arquivo in arquivos_essenciais:
        if not os.path.isfile(arquivo):
            print(f"❌ Faltando: {arquivo}")
        else:
            print(f"✅ Encontrado: {arquivo}")

def verificar_updater():
    print("\n🔍 Verificando uso indevido de 'Updater'...")
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                caminho = os.path.join(root, file)
                with open(caminho, "r", encoding="utf-8") as f:
                    conteudo = f.read()
                    if "Updater" in conteudo:
                        print(f"❌ 'Updater' encontrado em: {caminho}")

def verificar_requirements():
    print("\n🔍 Verificando requirements.txt...")
    if not os.path.isfile("requirements.txt"):
        print("❌ Arquivo requirements.txt não encontrado.")
        return

    with open("requirements.txt", "r", encoding="utf-8") as f:
        linhas = [linha.strip() for linha in f.readlines() if linha.strip()]
        for req in requisitos_validos:
            if req not in linhas:
                print(f"❌ Requisito ausente ou incorreto: {req}")
            else:
                print(f"✅ Requisito OK: {req}")

def verificar_pastas_indesejadas():
    print("\n🔍 Verificando pastas indesejadas...")
    for pasta in pastas_indesejadas:
        if os.path.isdir(pasta):
            print(f"⚠️ Remova a pasta: {pasta}")

def resumo():
    print("\n✅ Verificação concluída. Corrija os itens marcados com ❌ ou ⚠️ antes de subir no Discloud.")

if __name__ == "__main__":
    print("🛠️ Iniciando verificação do projeto...")
    verificar_arquivos()
    verificar_updater()
    verificar_requirements()
    verificar_pastas_indesejadas()
    resumo()
