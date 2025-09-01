import time
import os
import json
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from integration.IA import get_ia_response
from integration.api_GTI import agentes_conectados

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

HISTORICO_DIR = "historicos"
os.makedirs(HISTORICO_DIR, exist_ok=True)


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
def processar_mensagem(chat_id, mensagem, from_me=False):
    if not mensagem:
        return

    historico = carregar_historico(chat_id)

    if not from_me:
        # Adiciona mensagem do usuário ao histórico
        historico.append({
            "role": "user",
            "content": mensagem,
            "timestamp": int(time.time() * 1000)
        })
        salvar_historico(chat_id, historico)

        # Resposta da IA
        resposta = get_ia_response(mensagem, historico, "responda de forma educada e curta")

        try:
            agente = agentes_conectados[0]
            if agente.conectado:
                agente.enviar_mensagem(chat_id, resposta)
                print(f"[Responder] Mensagem enviada para {chat_id}: {resposta}")
            else:
                print(f"⚠️ Agente {agente.numero} desconectado. Não foi possível enviar.")
        except Exception as e:
            print(f"⚠️ Erro ao enviar mensagem para {chat_id}: {e}")
    else:
        print(f"Mensagem do agente ({chat_id}): {mensagem}")


# -------------------- FUNÇÕES AUXILIARES --------------------
def extrair_chat_id(data):
    # Primeiro tenta pegar dentro de "message"
    if "message" in data and isinstance(data["message"], dict):
        return str(data["message"].get("chatid") or data["message"].get("chatName") or "desconhecido")
    # Caso não tenha "message", verifica no nível principal
    return str(data.get("chatid") or data.get("chatName") or data.get("phone") or "desconhecido")


def extrair_mensagem(data):
    # Primeiro verifica se está dentro de "message"
    if "message" in data and isinstance(data["message"], dict):
        if "text" in data["message"]:
            return str(data["message"]["text"])
    # Verifica no nível principal
    if "text" in data and isinstance(data["text"], dict):
        return data["text"].get("message", "")
    elif "text" in data and isinstance(data["text"], str):
        return data["text"]
    elif "mensagem" in data:
        return str(data["mensagem"])
    return ""


# -------------------- ROTAS --------------------
@app.route('/', methods=['GET'])
def index():
    return "Servidor Flask rodando! Use POST em /webhook"


@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    try:
        data = request.get_json(force=True)
        print(data)
        print("[Webhook] Recebido:", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"⚠️ Erro ao ler JSON do webhook: {e}")
        return jsonify({"status": "erro", "mensagem": "JSON inválido"}), 400

    chat_id = extrair_chat_id(data)
    mensagem = extrair_mensagem(data)

    if chat_id == "desconhecido":
        print("⚠️ Chat ID não encontrado, mensagem ignorada")
        return jsonify({"status": "erro", "mensagem": "Chat ID inválido"}), 400

    processar_mensagem(chat_id, mensagem, from_me=data.get("fromMe", False))
    return jsonify({"status": "sucesso"}), 200


@app.route('/webhook/presence', methods=['POST'])
def webhook_presence():
    try:
        data = request.get_json(force=True)
        print(data)
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


@app.route('/webhook/messages/text', methods=['POST'])
def webhook_messages_text():
    try:
        data = request.get_json(force=True)
        msg = data["message"]["text"]
        usuario = data["message"]["senderName"]
        print(f"Mensagem de usuario: {usuario}\nMensagem: {msg}")
        chat_id = extrair_chat_id(data)
        mensagem = extrair_mensagem(data)

        if chat_id == "desconhecido":
            print("⚠️ Chat ID não encontrado, mensagem ignorada")
            return jsonify({"status": "erro", "mensagem": "Chat ID inválido"}), 400

        # Carrega histórico (opcional)
        historico = carregar_historico(chat_id)

        # Gera resposta da IA
        resposta = get_ia_response(mensagem, historico=historico, prompt_extra="Converse de forma casual no WhatsApp")

        # Salva histórico atualizado
        salvar_historico(chat_id, historico)

        # Envia mensagem usando o agente conectado
        agente = agentes_conectados[0]
        if agente.conectado:
            agente.enviar_mensagem(chat_id, resposta)
            print(f"[Responder] Mensagem enviada para {chat_id}: {resposta}")
        else:
            print(f"⚠️ Agente {agente.numero} desconectado. Não foi possível enviar.")

    except Exception as e:
        print(f"⚠️ Erro ao processar messages/text: {e}")
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


# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
