import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.z-api.io"
CLIENT_TOKEN = os.getenv('CLIENT_TOKEN')

class Agente:
    def __init__(self, nome, instance_id, token, numero=None, conectado=False):
        self.nome = nome
        self.instance_id = instance_id
        self.token = token
        self.numero = numero
        self.conectado = conectado
        # Atualiza dados automaticamente
        self.atualizar_status()

    def atualizar_status(self):
        """Atualiza o status de conexão e número do dispositivo"""
        self.status = self.check_status()
        self.device = self.check_device()
        self.numero = self.device.get("phone", self.numero)
        self.conectado = self.status.get("connected", self.conectado)

    def check_device(self):
        """Consulta device da instância"""
        try:
            url = f"{BASE_URL}/instances/{self.instance_id}/token/{self.token}/device"
            headers = {'Client-Token': CLIENT_TOKEN}
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return {}

    def check_status(self):
        """Consulta status da instância"""
        try:
            url = f"{BASE_URL}/instances/{self.instance_id}/token/{self.token}/status"
            headers = {'Client-Token': CLIENT_TOKEN}
            resp = requests.get(url, headers=headers, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return {}

    def enviar_mensagem(self, numero, mensagem):
        """Envia mensagem de texto via Z-API"""
        try:
            url = f"{BASE_URL}/instances/{self.instance_id}/token/{self.token}/send-text"
            payload = {"phone": numero, "message": mensagem}
            headers = {'Client-Token': CLIENT_TOKEN}
            resp = requests.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            print(f"Erro ao enviar mensagem para {numero}: {e}")
            return None

    def dados(self):
        """Imprime informações do agente"""
        print(f"Agente: {self.nome} | Número: {self.numero} | Conectado: {self.conectado} | ID: {self.instance_id}")


# =====================
# Carrega instâncias e cria objetos Agente automaticamente
# =====================
import re

def carregar_instancias():
    instances = []
    pattern = re.compile(r'ZAPI_LENTO_(\d+)_ID')
    for key, value in os.environ.items():
        match = pattern.match(key)
        if match:
            numero = match.group(1)
            token = os.getenv(f'ZAPI_LENTO_{numero}_TOKEN')
            if token:
                instances.append({
                    'numero': int(numero),
                    'id': value,
                    'token': token
                })
    return instances

# Cria objetos Agente
agentes = []
for ins in carregar_instancias():
    ag = Agente(f"Zapi Lento {ins['numero']}", ins['id'], ins['token'])
    agentes.append(ag)

# Teste: imprime todos os agentes
'''for ag in agentes:
    ag.dados()'''



