import os
import requests
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://api.z-api.io"
CLIENT_TOKEN = os.getenv('CLIENT_TOKEN')


def check_status(instance_id, token):
    """
    Consulta o status da instância na Z-API.
    Retorna o JSON com o status ou None em caso de erro.
    """
    try:
        headers = {'Client-Token': CLIENT_TOKEN}
        url = f"{BASE_URL}/instances/{instance_id}/token/{token}/status"
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erro ao listar instância {instance_id}: {e}")
        return None


def get_codigo(instance_id, token, phone):
    """
    Consulta o código para o número de telefone na instância.
    Retorna o JSON com o código ou None em caso de erro.
    """
    try:
        headers = {'Client-Token': CLIENT_TOKEN}
        url = f"{BASE_URL}/instances/{instance_id}/token/{token}/phone-code/{phone}"
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Erro ao consultar código da instância {instance_id}: {e}")
        return None


def carregar_instancias():
    """
    Carrega as 10 instâncias do arquivo .env.
    Retorna uma lista de dicts com 'id' e 'token'.
    """
    instances = []
    for i in range(1, 11):
        instance_id = os.getenv(f'INSTANCE_ID_{i}')
        token = os.getenv(f'TOKEN_{i}')
        if instance_id and token:
            instances.append({'id': instance_id, 'token': token})
        else:
            print(f"Variáveis INSTANCE_ID_{i} ou TOKEN_{i} não definidas no .env")
    return instances
instances = carregar_instancias()
for ins in instances:
    print(ins)
