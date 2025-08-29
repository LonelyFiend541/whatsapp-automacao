from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import threading
import time
import requests

# ----------------- FLASK -----------------
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return "Servidor Flask rodando! Use POST em /webhook"

@app.route('/webhook', methods=['POST'])
def webhook_receiver():
    data = request.json
    print("📩 Webhook recebido:", data)
    return jsonify({"status": "sucesso", "mensagem": "Webhook recebido com sucesso!"}), 200


# ----------------- MONITORAMENTO -----------------
load_dotenv()

BASE_URL = "https://api.z-api.io"
client_token = os.getenv("CLIENT_TOKEN")

# URL do webhook para onde enviar os alertas
WEBHOOK_ALERT_URL = os.getenv("WEBHOOK_ALERT_URL", "http://localhost:4040/webhook")

# Carrega todas as instâncias do .env
instances = []
for i in range(40, 49):
    instance_id = os.getenv(f"ZAPI_LENTO_{i}_ID")
    instance_token = os.getenv(f"ZAPI_LENTO_{i}_TOKEN")
    instance_name = f'ZAPI_LENTO_{i}'
    if instance_id and instance_token:
        instances.append({"id": instance_id, "token": instance_token, "name": instance_name})
    else:
        print(f"Instância {i} não configurada no .env")

# Função para enviar alertas
#funcao de enviar alerta desligada
def send_alert(inst_name, status):
    """Envia alerta via webhook"""
    payload = {
        "instance": inst_name,
        "status": "conectada" if status else "desconectada"
    }
    try:
        r = requests.post(WEBHOOK_ALERT_URL, json=payload, timeout=5)
        r.raise_for_status()
        print(f"📤 Alerta enviado para {WEBHOOK_ALERT_URL}: {payload}")
    except Exception as e:
        pass
        #print(f"❌ Erro ao enviar alerta da {inst_name}: {e}")

# Classe para monitorar cada instância em thread separada
class MonitorThread(threading.Thread):
    def __init__(self, inst, interval=5):
        super().__init__(daemon=True)
        self.inst = inst
        self.interval = interval
        self._stop_event = threading.Event()
        self.prev_status = None

    def run(self):
        print(f"Iniciando monitoramento da instância {self.inst['name']}")
        while not self._stop_event.is_set():
            status = self.check_status()
            if self.prev_status is not None:
                if self.prev_status and not status:
                    print(f"⚠️ Instância {self.inst['name']} desconectou!")
                    send_alert(self.inst['name'], status)
                elif not self.prev_status and status:
                    print(f"✅ Instância {self.inst['name']} reconectou!")
                    send_alert(self.inst['name'], status)
            else:
                print(f"Status inicial da instância {self.inst['name']}: {'Conectada' if status else 'Desconectada'}")
                send_alert(self.inst['name'], status)

            self.prev_status = status
            time.sleep(self.interval)

    def check_status(self):
        url = f"{BASE_URL}/instances/{self.inst['id']}/token/{self.inst['token']}/status"
        headers = {"Client-Token": client_token}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data.get("connected", False)
        except Exception as e:
            print(f"Erro ao consultar {self.inst['name']}: {e}")
            return False

    def stop(self):
        self._stop_event.set()

def start_monitoring():
    threads = []
    for inst in instances:
        t = MonitorThread(inst)
        t.start()
        threads.append(t)
    return threads


# ----------------- MAIN -----------------
if __name__ == "__main__":
    # inicia monitoramento
    threads = start_monitoring()

    # inicia flask em outra thread
    flask_thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=4040),
        daemon=True
    )
    flask_thread.start()

    print("Monitoramento e servidor Flask rodando. Digite 'sair' para encerrar.")
    while True:
        cmd = input()
        if cmd.strip().lower() == "sair":
            print("Encerrando...")
            for t in threads:
                t.stop()
            break

    for t in threads:
        t.join()
