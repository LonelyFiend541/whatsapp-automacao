import random

import redis
import time
import os
import json
import itertools
from random import choice, randrange
import re
from flask import Flask, request, jsonify, render_template
from concurrent.futures import ThreadPoolExecutor
from banco.dbo import carregar_agentes_do_banco, DB
from integration.IA import get_ia_response_ollama
from integration.api_GTI import atualizar_status_parallel

# -------------------- CONFIGURAÇÃO --------------------
app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

HISTORICO_DIR = "historicos"
os.makedirs(HISTORICO_DIR, exist_ok=True)

# -------------------- VARIÁVEIS GLOBAIS --------------------
agentes_gti = []
agentes_conectados = []

# -------------------- FUNÇÕES RESPONDER GRUPO --------------------

def responde_aleatorio(numero, resposta):
    global agentes_conectados
    if not agentes_conectados:
        return None
    ag = randrange(len(agentes_conectados))
    agentes_conectados[ag].enviar_mensagem(numero, resposta)
    return agentes_conectados[ag]

# -------------------- INICIALIZAÇÃO DE AGENTES --------------------

async def inicializar_agentes():
    global agentes_gti, agentes_conectados
    agentes_gti = carregar_agentes_do_banco(DB)
    await atualizar_status_parallel(agentes_gti)
    agentes_conectados = [ag for ag in agentes_gti if ag.conectado]
    return agentes_conectados


# -------------------- HISTÓRICO --------------------

def carregar_historico(chat_id: str):
    caminho = os.path.join(HISTORICO_DIR, f"{chat_id}.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico de {chat_id}: {e}")
    return []

def salvar_historico(chat_id: str, historico: list):
    caminho = os.path.join(HISTORICO_DIR, f"{chat_id}.json")
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(historico, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Erro ao salvar histórico de {chat_id}: {e}")

# -------------------- PROCESSAR MENSAGEM --------------------
def tratar_mensagem(data):
    chat_id = data.get("message", {}).get("chatid", "desconhecido")
    mensagem = data.get("message", {}).get("text", "")
    is_group = data.get("message", {}).get("isGroup", False)
    is_from_me = data.get("message", {}).get("fromMe", False)

    if chat_id == "desconhecido" or not mensagem or is_from_me:
        return None

    historico = carregar_historico(chat_id)

    # Obter resposta da IA
    resposta = get_ia_response_ollama(
        mensagem,
        historico,
        "mantenha uma cnonversa sobre progragamaçao "
    )

    agente = None
    if is_group and not is_from_me:
        # envia mensagem para grupo com um agente aleatório
        agente = random.choice(agentes_conectados)
        agente.enviar_mensagem(chat_id, resposta)
        print(f"✏️{agente.numero} respondeu no grupo {chat_id}: {resposta}")

    else:
        # mensagem privada
        owner = data.get("message", {}).get("owner", "")
        sender = data.get("message", {}).get("sender", "")
        match = re.search(r"(\d+)@", sender)
        numero = match.group(1) if match else None
        for ag in agentes_conectados:
            if ag.numero == owner:
                ag.enviar_mensagem(numero, resposta)
                agente = ag
                print(f"✏️ {agente.nome} respondeu para {numero}: {resposta}")

    # salvar histórico
    if agente:
        historico.append({
            "role": "assistant",
            "content": resposta,
            "group": is_group,
            "timestamp": int(time.time() * 1000),
            "data": time.strftime("%d/%m/%Y %H:%M:%S", time.localtime())
        })
        salvar_historico(chat_id, historico)
        return resposta

    return None

def processar_mensagem(chat_id, mensagem, from_me=False):
    if not mensagem:
        return

    historico = carregar_historico(chat_id)

    if not from_me:
        # Salva mensagem do usuário
        historico.append({
            "role": "user",
            "content": mensagem,
            "timestamp": int(time.time() * 1000)
        })
        salvar_historico(chat_id, historico)

        def responder():
            resposta = get_ia_response_ollama(mensagem, historico, "responda de forma educada e curta")
            if resposta:
                if not agentes_conectados:
                    inicializar_agentes()
                agente = responde_aleatorio(chat_id, resposta)
                if agente:
                    historico.append({
                        "role": "assistant",
                        "content": resposta,
                        "timestamp": int(time.time() * 1000)
                    })
                    salvar_historico(chat_id, historico)
                    print(f"[Responder] {agente.nome} enviou mensagem para {chat_id}: {resposta}")
                else:
                    print(f"⚠️ Nenhum agente disponível para enviar mensagem para {chat_id}")

        executor.submit(responder)
    else:
        print(f"Mensagem do agente ({chat_id}): {mensagem}")

# -------------------- FUNÇÕES AUXILIARES --------------------

def extrair_chat_id(data):
    return str(
        data.get("message", {}).get("chatid")
        or data.get("message", {}).get("chatName")
        or data.get("chatid")
        or data.get("chatName")
        or data.get("phone")
        or "desconhecido"
    )

def extrair_mensagem(data):
    if "message" in data and isinstance(data["message"], dict) and "text" in data["message"]:
        return str(data["message"]["text"])
    if "text" in data:
        if isinstance(data["text"], dict):
            return data["text"].get("message", "")
        return str(data["text"])
    if "mensagem" in data:
        return str(data["mensagem"])
    return ""

def worker_fila():
    print("[Worker] Iniciando processamento da fila...")
    while True:
        item = r.lpop("mensagens_fila")
        if item:
            try:
                data = json.loads(item)
                msg = data.get("message", {})
                msg_id = msg.get("messageid")
                chat_id = msg.get("chatid")

                # Lock Redis atômico
                lock_key = f"msg_lock:{chat_id}:{msg_id}"
                if not r.set(lock_key, 1, ex=3600, nx=True):
                    print(f"[Ignorada] Mensagem já processada: {msg_id}")
                    continue

                # Processa a mensagem
                resposta = tratar_mensagem(data)
                if resposta:
                    print(f"[Worker] Mensagem processada: {msg_id}")

            except Exception as e:
                print(f"⚠️ Erro ao processar item da fila: {e}")
        else:
            time.sleep(0.05)  # evita 100% CPU quando fila vazia


# -------------------- ROTAS --------------------
@app.route('/', methods=['GET'])
@app.route("/index.html")
def index():
    return render_template('index.html')

'''# Inicializa agentes ao iniciar o app
@app.before_request
def start_agentes():
    import threading, asyncio
    threading.Thread(target=lambda: asyncio.run(inicializar_agentes()), daemon=True).start()'''


@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    try:
        data = request.get_json(force=True)
        print("[Webhook] Recebido:", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"⚠️ Erro ao ler JSON do webhook: {e}")
        return jsonify({"status": "erro", "mensagem": "JSON inválido"}), 400


    return jsonify({"status": "sucesso"}), 200

# -------------------- WEBHOOK REFACTORADO --------------------
@app.route('/webhook/messages/text', methods=['POST'])
def webhook_messages_text():
    try:
        data = request.get_json(force=True)
        msg = data.get("message", {})
        msg_id = msg.get("messageid")
        chat_id = msg.get("chatid")

        if not msg_id or not chat_id:
            return "", 200

        # Adiciona à fila Redis
        r.rpush("mensagens_fila", json.dumps(data))
        print(f"[Fila] Mensagem enfileirada: {msg_id}")

    except Exception as e:
        print(f"⚠️ Erro ao enfileirar mensagem: {e}")
        return jsonify({"status": "erro"}), 400

    return jsonify({"status": "enfileirada"}), 200

@app.route('/webhook/presence', methods=['POST'])
def webhook_presence():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar presence: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200

@app.route('/webhook/groups', methods=['POST'])
def webhook_groups():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar presence: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200

@app.route('/webhook/chats', methods=['POST'])
def webhook_chats():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar chats: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200

@app.route('/webhook/messages_update', methods=['POST'])
def webhook_messages_update():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar messages_update: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200

@app.route('/webhook/history', methods=['POST'])
def webhook_history():
    data = request.get_json(force=True)
    return jsonify({"status": "ok", "mensagem": "Histórico processado com sucesso!"}), 200

@app.route('/webhook/connection', methods=['POST'])
def webhook_connection():
    data = request.json
    print("🔌 Evento de conexão recebido:", data)
    # Exemplo: tratar status
    status = data.get("status")
    if status == "CONNECTED":
        print("✅ Instância conectada com sucesso")
    elif status == "DISCONNECTED":
        print("⚠️ Instância desconectada")

    return jsonify({"status": "sucesso", "mensagem": "Webhook de conexão recebido"}), 200

@app.route('/webhook/contacts', methods=['POST'])
def webhook_contacts():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar messages_update: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200

@app.route('/webhook/messages/error', methods=['POST'])
def webhook_messages_error():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao processar messages_update: {e}")
        return jsonify({"status": "erro"}), 400
    return jsonify({"status": "sucesso"}), 200



# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    import threading
    import asyncio

    # Inicializa agentes
    asyncio.run(inicializar_agentes())

    # Start worker da fila em thread separada
    threading.Thread(target=worker_fila, daemon=True).start()

    # Roda Flask
    app.run(host="0.0.0.0", port=5000, debug=False)

