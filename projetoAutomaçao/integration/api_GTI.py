import asyncio
import base64
import threading
from io import BytesIO

import requests
import httpx
import tkinter as tk
from PIL import Image, ImageTk
from concurrent.futures import ThreadPoolExecutor

from banco.dbo import carregar_agentes_do_banco, DB
from integration.IA import tratar_erro_ia

BASE_URL = "https://api.gtiapi.workers.dev"

class AgenteGTI:
    def __init__(self, token, nome=None, timeout=20, debug=False):
        self.token = token
        self.nome = nome or "Agente GTI"
        self.timeout = timeout
        self.debug = debug

        self.numero = None
        self.conectado = False
        self.qrcode = None
        self.status_data = {}

        # Sessão síncrona para requests
        self.session = requests.Session()
        self.session.headers.update({"token": self.token, "Content-Type": "application/json"})

        # Cliente async para asyncio
        self.client = httpx.AsyncClient(timeout=timeout, headers={"token": self.token, "Content-Type": "application/json"})

        # Atualiza status inicial
        self.atualizar_status()

    # ======================== STATUS ========================
    def atualizar_status(self):
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

    async def atualizar_status_async(self):
        try:
            resp = await self.client.get(f"{BASE_URL}/instance/status")
            data = resp.json()
            self.numero = data.get("instance", {}).get("owner")
            self.conectado = data.get("status", {}).get("connected", False)
            self.qrcode = data.get("instance", {}).get("qrcode", "")
            self.status_data = data
        except Exception as e:
            print(f"[{self.nome}] Erro async ao atualizar status: {e}")
            print(tratar_erro_ia(e))
            self.conectado = False

    # ======================== ENVIAR MENSAGEM ========================
    def enviar_mensagem(self, numero, mensagem, mentions=""):
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
            resp = self.session.post(f"{BASE_URL}/send/text", json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return None

    def verificar_webhook(self):
        try:
            resp = self.session.get(f"{BASE_URL}/webhook", timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return None

    def apagar_webhook(self):
        data = agente.verificar_webhook()
        id = data[0].get("id")
        payload = {
            "enabled": False,
            "url": 'webhook',
            "events": [
                "messages",
                "messages_update"
            ],
            "excludeMessages": [
                "fromMeYes"
            ],
            "addUrlEvents": True,
            "addUrlTypesMessages": True,
            "action": "delete",
            "id": id
        }
        try:
            resp = self.session.post(f"{BASE_URL}/webhook", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            print(f"webhook do {agente.nome} apagado")
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return None

    def atualizar_webhook(self, webhook):
        payload = {
    "enabled": True,
    "url": webhook,
    "events": [
        "messages",
        "messages_update",
        "groups",
        "wasSentByApi",
        "wasNotSentByApi",
        "isGroupYes",
        "IsGroupNo"





    ],
    "excludeMessages": [
        "fromMeYes"

    ],
    "addUrlEvents": True,
    "addUrlTypesMessages": True,
    "action": "add"
    }
        try:
            resp = self.session.post(f"{BASE_URL}/webhook", json=payload, timeout=self.timeout)
            resp.raise_for_status()
            print(f"webhook do {self.nome} atualizado para {webhook}")
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return None

    async def enviar_mensagem_async(self, numero, mensagem, mentions=""):
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
            return True, resp.json()
        except httpx.RequestError as e:
            print(f"[{self.nome}] Erro async ao enviar mensagem: {e}")
            tratar_erro_ia(e)
            return False, None

    # ======================== QR CODE ========================
    def gerar_qr(self):
        """Gera QR code e exibe em janela Tkinter (thread safe)"""
        threading.Thread(target=self._gerar_qr_thread, daemon=True).start()

    def _gerar_qr_thread(self):
        import tkinter.messagebox as messagebox
        try:
            resp = self.session.post(f"{BASE_URL}/instance/connect", timeout=self.timeout)
            if resp.status_code == 409:
                messagebox.showinfo("Já conectado", f"[{self.nome}] Instância já conectada!")
                self.atualizar_status()
                return
            resp.raise_for_status()
            data = resp.json()
            qr_base64 = data.get("instance", {}).get("qrcode", "")
            if qr_base64.startswith("data:image/png;base64,"):
                qr_base64 = qr_base64.split(",")[1]
            self.qrcode = qr_base64
            if self.qrcode:
                self.abrir_qr_tkinter(self.qrcode)
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao gerar QR: {e}")

    def abrir_qr_tkinter(self, qr_base64):
        """Abre QR code em janela Tkinter"""
        qr_data = base64.b64decode(qr_base64 + "=" * (-len(qr_base64) % 4))
        img = Image.open(BytesIO(qr_data))
        window = tk.Toplevel()
        window.title(f"QR {self.nome}")
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(window, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)
        # Botão para fechar
        tk.Button(window, text="Fechar", command=window.destroy, bg="#e74c3c", fg="white").pack(pady=5)

    # ======================== DESCONEXÃO ========================
    def desconectar(self):
        try:
            resp = self.session.post(f"{BASE_URL}/instance/disconnect", timeout=self.timeout)
            resp.raise_for_status()
            self.atualizar_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao desconectar: {e}")
            return None

    async def desconectar_async(self):
        try:
            resp = await self.client.post(f"{BASE_URL}/instance/disconnect")
            resp.raise_for_status()
            await self.atualizar_status_async()
            return resp.json()
        except httpx.RequestError as e:
            print(f"[{self.nome}] Erro async ao desconectar: {e}")
            return None

    # ======================== DADOS ========================
    def dados(self):
        print(f"{self.nome} | Número: {self.numero} | Conectado: {self.conectado}")

# ======================== FUNÇÕES PARA VÁRIOS AGENTES ========================
async def atualizar_status_parallel(agentes):
    tasks = [ag.atualizar_status_async() for ag in agentes]
    await asyncio.gather(*tasks, return_exceptions=True)

def enviar_mensagens_parallel(agentes, numero, mensagem, max_workers=20):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(ag.enviar_mensagem, numero, mensagem): ag for ag in agentes}
        for f in futures:
            ag = futures[f]
            try:
                f.result()
            except Exception as e:
                print(f"[{ag.nome}] Erro paralelo: {e}")

'''
agentes = carregar_agentes_do_banco(DB)

for agente in agentes:
    if agente.nome == 'web_9':
        wb9 = agente
        wb9.atualizar_webhook('https://d35053657dd2.ngrok-free.app/webhook')
        #wb9.apagar_webhook()'''

'''agentes = carregar_agentes_do_banco(DB)

for agente in agentes:
    agente.apagar_webhook()
    agente.atualizar_webhook('https://8865d3731f7c.ngrok-free.app/webhook')'''
