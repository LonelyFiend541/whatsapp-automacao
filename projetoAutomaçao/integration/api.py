import requests

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