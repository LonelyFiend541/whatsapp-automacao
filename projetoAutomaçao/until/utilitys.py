# utils/utilitys.py
import time
from functools import wraps
import psutil


def retry(max_tentativas=3, delay=2, exceptions=(Exception,)):
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


