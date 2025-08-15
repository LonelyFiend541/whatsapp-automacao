import json
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
import subprocess
import os


# Configura variáveis do Android SDK
ANDROID_SDK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "patch"))
os.environ["ANDROID_HOME"] = ANDROID_SDK_PATH
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "platform-tools")
ADB_PATH = os.path.join(ANDROID_SDK_PATH, "platform-tools", "adb.exe")


def criar_contato(numero, udid=None):
    """
    Abre a tela de criação de contato no Android via Intent.
    O usuário precisa confirmar o contato na UI.

    :param numero: número do telefone (ex: 11999999999)
    :param udid: UDID do dispositivo, se houver mais de um
    """
    nome = f"Call Center: {numero}"
    telefone = f"55{numero}"  # adiciona DDI

    cmd = [ADB_PATH]
    if udid:
        cmd += ["-s", udid]

    cmd += [
        "shell", "am", "start",
        "-a", "android.intent.action.INSERT",
        "-t", "vnd.android.cursor.dir/contact",
        "--es", "name", nome,
        "--es", "phone", telefone
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stderr.strip():
        print("[ERRO]", result.stderr.strip())
        return False
    else:
        print(f"[INFO] Intent enviado: {nome} ({telefone})")
        return True


def numero_existe(telefone, udid=None):
    """
    Verifica se um número já está salvo na agenda do dispositivo via ADB.

    :param telefone: Número sem DDI, ex: 11999999999
    :param udid: UDID do dispositivo, se houver mais de um
    :return: True se existir, False se não existir
    """
    cmd = [ADB_PATH]
    if udid:
        cmd += ["-s", udid]

    numero_com_ddi = f"55{telefone}"
    cmd += [
        "shell", "content", "query",
        "--uri", "content://com.android.contacts/data/phones",
        "--projection", "data1",
        "--where", f"data1='{numero_com_ddi}'"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()

    if output and "No result found" not in output:
        print(f"== Número {numero_com_ddi} já cadastrado ==")
        return True

    return False

# pega o diretório raiz do projeto
RAIZ_PROJETO = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(RAIZ_PROJETO, "numeros")
ARQUIVO = os.path.join(PASTA, "numeros.json")

# cria a pasta se não existir
os.makedirs(PASTA, exist_ok=True)

# cria o arquivo se não existir
if not os.path.exists(ARQUIVO):
    with open(ARQUIVO, "w") as f:
        json.dump([], f)

def salvar_numero(numero: str):
    with open(ARQUIVO, "r") as f:
        numeros = json.load(f)
    if numero not in numeros:
        numeros.append(numero)
    with open(ARQUIVO, "w") as f:
        json.dump(numeros, f, indent=4)

def ler_numeros():
    with open(ARQUIVO, "r") as f:
        return json.load(f)


