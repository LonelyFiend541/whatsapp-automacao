# utils/utilitys.py
from functools import wraps
import subprocess
from selenium.webdriver.common.by import By
from drivers import drivers_whatsapp_bussines as drivers_wa
import psutil

udids = drivers_wa.pegar_udids()

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
                f"adb -s {udid} shell settings put global animator_duration_scale 0",
                f"adb -s {udid} shell settings put global transition_animation_scale 0",
                f"adb -s {udid} shell settings put global window_animation_scale 0",
                f"adb -s {udid} shell am kill-all"
            ]
            for cmd in comandos:
                subprocess.run(cmd.split(), check=True)
            print(f"Aparelho {udid} otimizado.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao otimizar {udid}: {e}")

def limpar_whatsapp():
    for udid in udids:
        try:
            comando = f"adb -s {udid} shell pm clear com.whatsapp"
            subprocess.run(comando.split(), check=True)
            print(f"Whatsapp do aparelho {udid} Limpo.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao limpar {udid}: {e}")

def limpar_whatsapp_busines():
    for udid in udids:
        try:
            comando = f"adb -s {udid} shell pm clear com.whatsapp.w4b"
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


