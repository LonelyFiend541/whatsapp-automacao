# utils/utilitys.py
import json
from functools import wraps
import subprocess
from selenium.webdriver.common.by import By
from drivers import drivers_whatsapp_bussines as drivers_wa
import psutil
import subprocess
import os
from until.waits import esperar_elemento_visivel
import time

# Configura variáveis do Android SDK
ANDROID_SDK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),"..", "patch"))
os.environ["ANDROID_HOME"] = ANDROID_SDK_PATH
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "platform-tools")
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "cmdline-tools", "latest", "bin")
ADB_PATH = os.path.join(ANDROID_SDK_PATH, "platform-tools", "adb.exe")

#udids = drivers_wa.pegar_udids()

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


def retry(max_tentativas: int = 3, delay: int = 2, exceptions: tuple = (Exception,)) -> callable:
    """
    Decorador para repetir a execução de uma função em caso de exceção.

    :param max_tentativas: Número máximo de tentativas
    :param delay: Tempo (em segundos) entre tentativas
    :param exceptions: Tupla de exceções que devem ser tratadas para retry
    :return: Resultado da função ou None
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for tentativa in range(1, max_tentativas + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"Tentativa {tentativa} falhou: {e}")
                    if tentativa == max_tentativas:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def encerrar_appium():
    appium_encontrado = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'].lower() == 'node.exe':
                if any('appium' in str(arg).lower() for arg in proc.info['cmdline']):
                    appium_encontrado = True
                    print(f"Encontrado Appium (PID {proc.info['pid']}). Encerrando...")
                    proc.kill()
                    print("Servidor Appium encerrado com sucesso")
        except (psutil.NoSuchProcess, psutil.AcessDenied):
            continue

    if not appium_encontrado:
        print('Nenhum processo appium foi encontrado em execução')

def otimizar_app(udids):
    """
    Otimiza o desempenho do dispositivo Android desativando animações e fechando apps em segundo plano.

    :param udids: Lista de UDIDs dos dispositivos conectados
    """
    for udid in udids:
        try:
            comandos = [
                f"{ADB_PATH} -s {udid} shell settings put global animator_duration_scale 0",
                f"{ADB_PATH} -s {udid} shell settings put global transition_animation_scale 0",
                f"{ADB_PATH} -s {udid} shell settings put global window_animation_scale 0",
                f"{ADB_PATH} -s {udid} shell am kill-all"
            ]
            for cmd in comandos:
                subprocess.run(cmd.split(), check=True)
            print(f"Aparelho {udid} otimizado.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao otimizar {udid}: {e}")

def limpar_whatsapp(udids):
    for udid in udids:
        try:
            comando = f"{ADB_PATH} -s {udid} shell pm clear com.whatsapp"
            subprocess.run(comando.split(), check=True)
            print(f"Whatsapp do aparelho {udid} Limpo.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao limpar {udid}: {e}")

def limpar_whatsapp_busines(udids):
    for udid in udids:
        try:
            comando = f"{ADB_PATH} -s {udid} shell pm clear com.whatsapp.w4b"
            subprocess.run(comando.split(), check=True)
            print(f"Whatsapp Business do aparelho {udid} Limpo.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao limpar {udid}: {e}")


def esta_ativo_por_xpath(driver, xpath):
    """
    Verifica se um elemento está marcado como ativo (checked="true") com base no XPath.
    """
    try:
        elemento = esperar_elemento_visivel(driver, (By.XPATH, xpath))
        checked = elemento.get_attribute("checked")
        print(checked)
        return checked == "true"
    except Exception as e:
        print(f"[esta_ativo_por_xpath] Erro ao verificar estado do elemento: {e}")
        return False





