import time
import os
import json
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from integration.IA import get_ia_response
from integration.api import agentes

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

HISTORICO_DIR = "historicos"
os.makedirs(HISTORICO_DIR, exist_ok=True)


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


def processar_mensagem(data: dict):
    chat_id = str(data.get("numero") or data.get("phone") or "desconhecido")
    mensagem = ""
    if "mensagem" in data:
        mensagem = str(data["mensagem"])
    elif "text" in data and isinstance(data["text"], dict):
        mensagem = str(data["text"].get("message", ""))

    if not mensagem:
        print(f"⚠️ Nenhuma mensagem encontrada para {chat_id}")
        return

    historico = carregar_historico(chat_id)

    if not data.get("fromMe", False):
        # Adiciona mensagem do usuário
        historico.append({
            "role": "user",
            "content": mensagem,
            "timestamp": data.get("momment") or int(time.time() * 1000)
        })
        salvar_historico(chat_id, historico)

        # Gera resposta da IA
        resposta = get_ia_response(mensagem, historico)

        # Envia a resposta para o agente correto
        try:
            # Aqui você pode mapear qual agente responde para qual chat
            agentes[8].enviar_mensagem(chat_id, resposta)
            print(f"[Responder] Mensagem enviada para {chat_id}: {resposta}")
        except Exception as e:
            print(f"⚠️ Erro ao enviar mensagem para {chat_id}: {e}")
    else:
        print(f"Mensagem do agente ({chat_id}): {mensagem}")


@app.route('/', methods=['GET'])
def index():
    return "Servidor Flask rodando! Use POST em /webhook"


@app.route('/webhook', methods=['POST'])
@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    try:
        data = request.get_json(force=True)
    except Exception as e:
        print(f"⚠️ Erro ao ler JSON do webhook: {e}")
        return jsonify({"status": "erro", "mensagem": "JSON inválido"}), 400

    if not isinstance(data, dict):
        return jsonify({"status": "erro", "mensagem": "Formato de JSON inválido"}), 400

    chat_id = str(data.get("chatName") or data.get("phone") or "desconhecido")
    historico = carregar_historico(chat_id)

    # Somente responde se não for mensagem enviada pelo próprio agente
    if not data.get("fromMe", False):
        phone = str(data.get("phone") or "")
        mensagem_texto = ""
        if "text" in data and isinstance(data["text"], dict):
            mensagem_texto = data["text"].get("message", "")

        if phone == agentes[8].numero:
            resposta = get_ia_response(
                mensagem_texto,
                historico,
                prompt_extra="Responda com menos de 60 caracteres"
            )

            try:
                agentes[8].enviar_mensagem(phone, resposta)
                print(f"[Responder] Mensagem enviada para {phone}: {resposta}")
            except Exception as e:
                print(f"⚠️ Erro ao enviar mensagem para {phone}: {e}")

    return jsonify({"status": "sucesso", "mensagem": "Webhook processado"}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
