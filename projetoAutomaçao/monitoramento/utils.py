import requests
import os

WEBHOOK_ALERT_URL = os.getenv("WEBHOOK_ALERT_URL", "http://localhost:4040/webhook")

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
        #print(f"❌ Erro ao enviar alerta da {inst_name}: {e}")
        pass