from flask import Flask, request, jsonify
from integration.api import *
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Servidor Flask rodando! Use POST em /webhook"

@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    data = request.json
    agentes[8].enviar_mensagem(data.get("phone"), "ola")
    print("📩 Webhook recebido:", data)
    return jsonify({"status": "sucesso", "mensagem": "Webhook recebido com sucesso!"}), 200

def run_server():
    app.run(host="0.0.0.0", port=4040)
