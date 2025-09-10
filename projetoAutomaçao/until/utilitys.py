import os
import subprocess
import psutil
import time
from functools import wraps
from selenium.webdriver.common.by import By
from until.waits import esperar_elemento_visivel
from concurrent.futures import ThreadPoolExecutor, as_completed
import shlex

# ===========================
# Configura Android SDK
# ===========================
ANDROID_SDK_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "patch"))
os.environ["ANDROID_HOME"] = ANDROID_SDK_PATH
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "platform-tools")
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "cmdline-tools", "latest", "bin")
ADB_PATH = os.path.join(ANDROID_SDK_PATH, "platform-tools", "adb.exe")


# ===========================
# Decorador Retry
# ===========================
def retry(max_tentativas: int = 3, delay: int = 2, exceptions: tuple = (Exception,)) -> callable:
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


# ===========================
# Encerrar Appium
# ===========================
def encerrar_appium():
    encontrados = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == 'node.exe':
                if any('appium' in str(arg).lower() for arg in proc.info['cmdline']):
                    encontrados.append(proc.info['pid'])
                    print(f"🛑 Encontrado Appium (PID {proc.info['pid']}). Encerrando...")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if encontrados:
        print(f"✅ {len(encontrados)} processo(s) Appium encerrado(s).")
    else:
        print("ℹ Nenhum processo Appium em execução.")

# ===========================
# Encerrar uiautomator2
# ===========================
def liberar_portas(range_inicio=8200, range_fim=8299):
    liberadas = []
    for conn in psutil.net_connections(kind="inet"):
        laddr = conn.laddr.port if conn.laddr else None
        if laddr and range_inicio <= laddr <= range_fim:
            try:
                proc = psutil.Process(conn.pid)
                print(f"🛑 Encerrando PID {conn.pid} que ocupava a porta {laddr} ({proc.name()})")
                proc.kill()
                liberadas.append(laddr)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    if liberadas:
        print(f"✅ Portas liberadas: {liberadas}")
    else:
        print("ℹ Nenhuma porta ocupada no range 8200–8299.")

# ===========================
# Função genérica ADB
# ===========================
def otimizar_app(udids):
    for udid in udids:
        try:
            comandos = [
                [ADB_PATH, "-s", udid, "shell", "settings", "put", "global", "animator_duration_scale", "0"],
                [ADB_PATH, "-s", udid, "shell", "settings", "put", "global", "transition_animation_scale", "0"],
                [ADB_PATH, "-s", udid, "shell", "settings", "put", "global", "window_animation_scale", "0"],
                [ADB_PATH, "-s", udid, "shell", "am", "kill-all"]
            ]
            for cmd in comandos:
                subprocess.run(cmd, check=True)
            print(f"Aparelho {udid} otimizado.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao otimizar {udid}: {e}")

def limpar_whatsapp(udids):
    for udid in udids:
        try:
            comando = [ADB_PATH, "-s", udid, "shell", "pm", "clear", "com.whatsapp"]
            subprocess.run(comando, check=True)
            print(f"Whatsapp do aparelho {udid} Limpo.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao limpar {udid}: {e}")

def limpar_whatsapp_busines(udids):
    for udid in udids:
        try:
            comando = [ADB_PATH, "-s", udid, "shell", "pm", "clear", "com.whatsapp.w4b"]
            subprocess.run(comando, check=True)
            print(f"Whatsapp Business do aparelho {udid} Limpo.")
        except subprocess.CalledProcessError as e:
            print(f"[ERRO] Falha ao limpar {udid}: {e}")

# ===========================
# Executar em paralelo
# ===========================
def executar_em_paralelo(func, udids, max_workers=5):
    resultados_finais = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, udid): udid for udid in udids}
        for future in as_completed(futures):
            udid, resultados = future.result()
            resultados_finais[udid] = resultados
            print(f"📱 {udid} → {resultados}")
    return resultados_finais

# ===========================
# Função utilitária para status de elementos
# ===========================
def esta_ativo_por_xpath(driver, xpath):
    """
    Verifica se um elemento está marcado como ativo (checked="true") com base no XPath.
    """
    try:
        elemento = esperar_elemento_visivel(driver, (By.XPATH, xpath))
        checked = elemento.get_attribute("checked")
        return checked == "true"
    except Exception as e:
        print(f"[esta_ativo_por_xpath] Erro ao verificar estado do elemento: {e}")
        return False