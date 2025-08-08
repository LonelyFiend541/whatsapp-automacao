import requests
import os
'''

def enviar_para_api(numero):
    url = "http://localhost:5000/salvar_dados"  # URL do site
    payload = {
        "numero": numero
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Enviado com sucesso: {response.status_code}")
        return True
    except requests.RequestException as e:
        print(f"Erro ao enviar para a API: {e}")
        return False
'''


import requests
import os

def buscar_dados(numero) -> str:
    INSTANCE_ID = os.getenv("ZAPI_INSTANCE", "3DF1EF843EDCA1A466890A1EFCACDE10")
    TOKEN = os.getenv("ZAPI_TOKEN", "0872ABDCF8B0B9D525965D88")
    headers = {"Client-Token": "F55751aaa63d246558565321cdf8850f3S"}
    url = f"https://api.z-api.io/instances/{INSTANCE_ID}/token/{TOKEN}/phone-code/{numero}"

    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        # Supondo que a resposta tem um campo "code"
        codigo_api = data.get("code")
        if codigo_api:
            return str(codigo_api)
        else:
            return "Código não encontrado na resposta."
    except requests.RequestException as e:
        return f"Erro na requisição: {e}"
    except ValueError:
        return "Resposta inválida da API."




def instancia_status ():
    INSTANCE_ID = os.getenv("ZAPI_INSTANCE", "3DF1EFBED1D391A09A69FA8592F99CB9")
    TOKEN = os.getenv("ZAPI_TOKEN", "57B0796F36EBCEC9781F3B11")
    headers = {"Client-Token": "F55751aaa63d246558565321cdf8850f3S"}
    url = f" https://api.z-api.io/instances/{INSTANCE_ID}/token/{TOKEN}/status"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        print(r.json())
        return r.json()
    except requests.RequestException as e:
        print(f"Erro: {e}")



print(instancia_status())