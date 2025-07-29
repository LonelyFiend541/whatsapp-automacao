import subprocess
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import AppiumService
from until.retries import retry


# 🔌 Busca os dispositivos conectados via ADB
def pegar_udid():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]  # Ignora o cabeçalho
    udids = [line.split('\t')[0] for line in lines if '\tdevice' in line]

    print(f"📱 Dispositivos conectados: {udids}")
    return udids


# 🚀 Criação do driver com tentativas automáticas em caso de falha
@retry(max_tentativas=3, delay=1)
def criar_driver(porta, udid):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = udid
    options.automation_name = "UiAutomator2"
    options.udid = udid
    options.app_package = "com.whatsapp"
    options.app_activity = "com.whatsapp.Main"
    options.auto_grant_permissions = True

    print(f"🧩 Criando driver para dispositivo {udid} na porta {porta}...")

    # ⚠️ Corrigir endpoint se usar Appium 2.x com `--base-path /`
    driver = webdriver.Remote(
        command_executor=f'http://localhost:{porta}/wd/hub',  # /wd/hub não é mais necessário com base-path '/'
        options=options
    )
    return driver


# 🟢 Instância única para controle do serviço Appium
appium_service = AppiumService()


# ▶️ Inicia o servidor Appium
def appium_server():
    if appium_service.is_running:
        print("✅ Appium já está rodando.")
    else:
        print("🟡 Iniciando Appium Server...")
        appium_service.start(
            node=r"C:\Program Files\nodejs\node.exe",
            npm=r"C:\Program Files\nodejs\npm.cmd",
            main_script=r"C:\Users\user\AppData\Roaming\npm\node_modules\appium\build\lib\main.js",
            args=[
                '--port', '4723',
                '--base-path', '/',
                '--use-drivers', 'uiautomator2'
            ]
        )

        # ⏳ Aguarda até estar ativo
        for _ in range(10):
            if appium_service.is_running:
                print("✅ Appium iniciado com sucesso.")
                break
            time.sleep(1)
        else:
            raise RuntimeError("❌ Não foi possível iniciar o Appium.")


# ⏹ Encerra o servidor Appium
def parar_appium():
    if appium_service.is_running:
        print("🛑 Parando Appium...")
        appium_service.stop()
