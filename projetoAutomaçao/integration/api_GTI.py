import os
import base64
import random
import time
from io import BytesIO
import re
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import pyodbc
from dotenv import load_dotenv
from requests import session
from websockets.asyncio.async_timeout import timeout

load_dotenv()
BASE_URL = "https://api.gtiapi.workers.dev"


class AgenteGTI:
    def __init__(self, token=None, nome=None, timeout=10, debug=False):
        self.token = token
        self.nome = nome or "Agente GTI"
        self.numero = None
        self.conectado = False
        self.qrcode = ""
        self.status_data = {}
        self.timeout = timeout
        self.debug = debug

        # Sessão persistente para reduzir latência
        self.session = requests.Session()
        self.session.headers.update({
            "token": self.token,
            "Content-Type": "application/json"
        })

        self.atualizar_status()

    def atualizar_status(self):
        """Atualiza status da instância usando sessão persistente"""
        try:
            resp = self.session.get(f"{BASE_URL}/instance/status", timeout=self.timeout)
            data = resp.json()
            self.numero = data.get("instance", {}).get("owner")
            self.conectado = data.get("status", {}).get("connected", False)
            self.qrcode = data.get("instance", {}).get("qrcode", "")
            self.status_data = data
        except Exception as e:
            print(f"[{self.nome}] Erro ao atualizar status: {e}")
            self.conectado = False

    def enviar_mensagem(self, numero, mensagem, mentions=""):
        """Envia mensagem via API GTI"""
        if not mensagem:
            print(f"[{self.nome}] Mensagem vazia. Abortando envio.")
            return None

        payload = {
            "number": str(numero),
            "text": str(mensagem),
            "linkPreview": False,
            "replyid": "",
            "mentions": str(mentions),
            "readchat": True,
            "delay": 0
        }

        try:
            resp = self.session.post(f"{BASE_URL}/send/text", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return False

    def gerar_qr(self):
        """Solicita geração de QR code"""
        try:
            resp = self.session.post(f"{BASE_URL}/instance/connect", timeout=self.timeout)

            if resp.status_code == 409:
                print(f"[{self.nome}] Já conectado, atualizando status.")
                self.atualizar_status()
            else:
                resp.raise_for_status()
                data = resp.json()
                qr_base64 = data.get("instance", {}).get("qrcode", "")
                if qr_base64.startswith("data:image/png;base64,"):
                    qr_base64 = qr_base64.split(",")[1]
                self.qrcode = qr_base64

            if self.qrcode:
                print(f"\n[{self.nome}] QR Code disponível")
                self.abrir_qr(qr_base64)

        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao gerar QR code: {e}")

    def abrir_qr(self, qr_base64):
        import base64
        import cv2
        import numpy as np

        # Base64 do QR Code
        # Decodifica Base64 em bytes
        image_data = base64.b64decode(qr_base64)
        image_np = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
        while True:
            cv2.imshow(f"QR Code {self.nome}", img)
            print("Pressione 'r' para recarregar ou qualquer outra tecla para fechar...")
            key = cv2.waitKey(0)

            if key == ord('r') or key == ord('R'):
                cv2.destroyAllWindows()
                print(f"[{self.nome}] Recarregando QR...")
                self.gerar_qr()   # chama de novo para pegar QR atualizado
                return None
            else:
                cv2.destroyAllWindows()
                return True

    def dados(self):
        """Mostra dados básicos"""
        print(f"{self.nome} | Número: {self.numero} | Conectado: {self.conectado}")

import httpx

class AgenteGTIAsync:
    def __init__(self, token=None, nome=None, timeout=10):
        self.token = token
        self.nome = nome or "Agente GTI"
        self.numero = None
        self.conectado = False
        self.qrcode = ""
        self.status_data = {}
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, headers={
            "token": self.token,
            "Content-Type": "application/json"
        })

    async def async_init(self):
        """Inicializador assíncrono para atualizar status ao criar"""
        await self.atualizar_status()
        return self

    async def atualizar_status(self):
        try:
            resp = await self.client.get(f"{BASE_URL}/instance/status")
            data = resp.json()
            self.numero = data.get("instance", {}).get("owner")
            self.conectado = data.get("status", {}).get("connected", False)
            self.qrcode = data.get("instance", {}).get("qrcode", "")
            self.status_data = data
        except Exception as e:
            print(f"[{self.nome}] Erro ao atualizar status: {e}")
            self.conectado = False

    async def enviar_mensagem(self, numero, mensagem, mentions=""):
        if not mensagem:
            print(f"[{self.nome}] Mensagem vazia. Abortando envio.")
            return None

        payload = {
            "number": str(numero),
            "text": str(mensagem),
            "linkPreview": False,
            "replyid": "",
            "mentions": str(mentions),
            "readchat": True,
            "delay": 0
        }

        try:
            resp = await self.client.post(f"{BASE_URL}/send/text", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return False


# ======================
# Funções auxiliares
# ======================

def atualizar_webhook(agente, url):
    headers = {
        "token": agente.token,
        "Content-Type": "application/json"
    }

    payload = {
        "enabled": True,
        "url": url,
        "events": [
            "connection",
            "history",
            "messages",
            "messages_update",
            "call",
            "contacts",
            "presence",
            "groups",
            "labels",
            "chats",
            "chat_labels",
            "blocks",
            "leads",
            "wasSentByApi",
            "wasNotSentByApi",
            "fromMeYes",
            "fromMeNo",
            "isGroupYes",
            "IsGroupNo"
        ],
        "excludeMessages": [],
        "addUrlEvents": True,
        "addUrlTypesMessages": True,
        "action": "add"
    }

    try:
        resp = requests.post(f"{BASE_URL}/webhook", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        print(f"Webhook atualizado com sucesso para {payload['url']}.")
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️ Erro ao atualizar Webhook: {e}")
        return None

def apagar_webhook(agente, url, id):
    headers = {
        "token": agente.token,
        "Content-Type": "application/json"
    }

    payload = {
        "enabled": True,
        "url": url,
        "events": [
            "connection",
            "history",
            "messages",
            "messages_update",
            "call",
            "contacts",
            "presence",
            "groups",
            "labels",
            "chats",
            "chat_labels",
            "blocks",
            "leads",
            "wasSentByApi",
            "wasNotSentByApi",
            "fromMeYes",
            "fromMeNo",
            "isGroupYes",
            "IsGroupNo"
        ],
        "excludeMessages": [],
        "addUrlEvents": True,
        "addUrlTypesMessages": True,
        "action": "delete",
        "id": id

    }

    try:
        resp = requests.post(f"{BASE_URL}/webhook", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        print(f"Webhook {payload['url']} apagado com sucesso.")
        return resp.json()
    except requests.RequestException as e:
        print(f"⚠️ Erro ao apagar Webhook: {e}")
        return None

def atualizar_status_parallel(agentes, max_workers=20):  # Aumente max_workers
    """Atualiza status em paralelo"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_agente = {executor.submit(ag.atualizar_status): ag for ag in agentes}
        for future in as_completed(future_to_agente):
            ag = future_to_agente[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{ag.nome}] Erro inesperado ao atualizar: {e}")

def enviar_mensagens_parallel(agentes, numero, mensagem, max_workers=20):  # Aumente max_workers
    """Envia mensagens em paralelo para todos os agentes"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_agente = {executor.submit(ag.enviar_mensagem, numero, mensagem): ag for ag in agentes}
        for future in as_completed(future_to_agente):
            ag = future_to_agente[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{ag.nome}] Erro inesperado no envio: {e}")

def qr():
    import cv2
    import numpy as np
    import requests

    url = "https://pps.whatsapp.net/v/t61.24694-24/534424608_770439622290480_6871407698259227592_n.jpg?ccb=11-4&oh=01_Q5Aa2QGCgkHxQy8fY0udR7GNx7bNLaqltd-uxyKPb-6Pfh4cBg&oe=68C5AB9B&_nc_sid=5e03e0&_nc_cat=105"

    # Faz o download da imagem
    response = requests.get(url)
    image_np = np.frombuffer(response.content, np.uint8)
    img = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    r = 114
    R = 82
    ativo = True
    while ativo:
        cv2.imshow("precione r para recarregar", img)
        key = cv2.waitKey(0)
        if key == r or key == R:
            cv2.destroyAllWindows()
            print("reabriu")
            print(key)
            qr()
            break
        else:
            cv2.destroyAllWindows()
            print("sair")
            break





