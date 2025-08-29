import os
import base64
from io import BytesIO
from PIL import Image
import re
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
BASE_URL = "https://api.gtiapi.workers.dev"


class AgenteGTI:
    def __init__(self, token, nome=None, timeout=10, debug=False):
        self.token = token
        self.nome = nome or "Agente GTI"
        self.numero = None
        self.conectado = False
        self.qrcode = ""
        self.status_data = {}
        self.timeout = timeout
        self.debug = debug

        self.atualizar_status()

    def atualizar_status(self):
        """Atualiza status da instância usando apenas o token"""
        try:
            resp = requests.get(f"{BASE_URL}/instance/status", headers={'token': self.token}, timeout=self.timeout)
            data = resp.json()
            # Número do dono
            self.numero = data.get("instance", {}).get("owner")
            # Status real de conexão
            self.conectado = data.get("status", {}).get("connected", False)
            # QR code atual
            self.qrcode = data.get("instance", {}).get("qrcode", "")
            self.status_data = data
        except Exception as e:
            print(f"[{self.nome}] Erro ao atualizar status: {e}")
            self.conectado = False

    def check_status(self):
        """Consulta status da instância"""
        try:
            url = f"{BASE_URL}/instance/status"
            headers = {'token': self.token}
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json().get("instance", {})
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao consultar status: {e}")
            return {}

    def enviar_mensagem(self, numero, mensagem):
        """Envia mensagem via API GTI com payload correto"""
        url = f"{BASE_URL}/send/text"
        headers = {
            "token": self.token,
            "Content-Type": "application/json"
        }
        payload = {
            "number": numero,  # número do destinatário
            "text": mensagem,  # conteúdo da mensagem
            "linkPreview": False,  # não gerar preview de links
            "replyid": "",  # se for responder alguma mensagem, coloque o ID
            "mentions": "",  # "all" ou lista separada por vírgula
            "readchat": True,  # marcar chat como lido
            "delay": 0  # atraso para envio
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao enviar mensagem: {e}")
            return None

    def exibir_qr(self):
        """Exibe o QR code decodificando a imagem Base64"""
        if not self.qrcode:
            print(f"[{self.nome}] Nenhum QR code disponível")
            return

        try:
            img_bytes = base64.b64decode(self.qrcode)
            img = Image.open(BytesIO(img_bytes))
            img.show()  # Abre no visualizador padrão do sistema
        except Exception as e:
            print(f"[{self.nome}] Erro ao abrir QR code: {e}")

    def gerar_qr_terminal(self, qr_string=None):
        """Exibe QR code no terminal (texto)"""
        qr_string = qr_string or self.qrcode
        if not qr_string:
            print(f"[{self.nome}] Nenhum QR code disponível")
            return

        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(qr_string)
        qr.make(fit=True)

        for linha in qr.get_matrix():
            print("".join(["██" if celula else "  " for celula in linha]))

    def gerar_qr(self, modo="img"):
        """Gera QR code usando apenas o token"""
        try:
            url = f"{BASE_URL}/instance/connect"
            headers = {'token': self.token}
            resp = requests.post(url, headers=headers, timeout=self.timeout)

            if resp.status_code == 409:
                # Instância já conectada, atualizar status e usar QR existente
                print(f"[{self.nome}] Instância já conectada. Usando QR code existente.")
                self.atualizar_status()
            else:
                resp.raise_for_status()
                data = resp.json()
                qr_base64 = data.get("instance", {}).get("qrcode", "")
                if qr_base64.startswith("data:image/png;base64,"):
                    qr_base64 = qr_base64.split(",")[1]
                self.qrcode = qr_base64
                if self.debug:
                    print(f"[{self.nome}] Debug QR code data: {data}")

            if self.qrcode:
                print(f"\n[{self.nome}] QR Code disponível:")
                if modo == "terminal":
                    self.gerar_qr_terminal(self.qrcode)
                else:
                    self.exibir_qr()
            else:
                print(f"[{self.nome}] Nenhum QR code disponível")
        except requests.RequestException as e:
            print(f"[{self.nome}] Erro ao gerar QR code: {e}")

    def dados(self):
        """Exibe informações do agente"""
        print(f"[{self.nome}] Número: {self.numero} | Conectado: {self.conectado}")


def carregar_agentes_do_env():
    """Carrega tokens do .env e cria agentes"""
    agentes_gti = []
    pattern = re.compile(r'GTI_(\d+)')
    for key, value in os.environ.items():
        match = pattern.match(key)
        if match:
            numero = match.group(1)
            token = value
            agentes_gti.append(AgenteGTI(token=token, nome=f"Agente {numero}"))
    return agentes_gti


def gerar_qr_parallel(agentes, max_workers=5, modo="img"):
    """Gera QR codes de múltiplos agentes em paralelo"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_agente = {executor.submit(ag.gerar_qr, modo): ag for ag in agentes}
        for future in as_completed(future_to_agente):
            ag = future_to_agente[future]
            try:
                future.result()
            except Exception as e:
                print(f"[{ag.nome}] Erro inesperado: {e}")



agentes_gti = carregar_agentes_do_env()
print(f"Carregados {len(agentes_gti)} agentes")

# Gera QR codes em paralelo
#gerar_qr_parallel(agentes_gti, max_workers=5, modo="img")

# Exibe dados resumidos
#for ag in agentes_gti:
    #ag.dados()
