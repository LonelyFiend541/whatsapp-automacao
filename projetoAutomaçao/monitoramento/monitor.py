import threading
import time
import requests
import os
from dotenv import load_dotenv

from monitoramento.utils import send_alert

load_dotenv()

BASE_URL = "https://api.z-api.io"
client_token = os.getenv("CLIENT_TOKEN")

# Carrega instâncias do .env
def load_instances():
    instances = []
    for i in range(40, 49):
        instance_id = os.getenv(f"ZAPI_LENTO_{i}_ID")
        instance_token = os.getenv(f"ZAPI_LENTO_{i}_TOKEN")
        instance_name = f'ZAPI_LENTO_{i}'
        if instance_id and instance_token:
            instances.append({"id": instance_id, "token": instance_token, "name": instance_name})
        else:
            print(f"Instância {i} não configurada no .env")
    return instances

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

    def pegar_qrCode(self):
        url = f"{BASE_URL}/instances/{self.inst['id']}/token/{self.inst['token']}/qr-code"
        headers = {"Client-Token": client_token}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data
        except Exception as e:
            print(f"Erro ao consultar {self.inst['name']}: {e}")
            return False


    def stop(self):
        self._stop_event.set()

def start_monitoring():
    threads = []
    instances = load_instances()
    for inst in instances:
        t = MonitorThread(inst)
        t.start()
        threads.append(t)
    return threads
