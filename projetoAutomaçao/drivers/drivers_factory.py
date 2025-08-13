from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import AppiumService

from drivers.drivers_whatsapp import *

# Configura Android SDK para o Appium achar o adb
# Configura variáveis do Android SDK
ANDROID_SDK_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # pasta do script atual
        "..", "patch"
    )
)

os.environ["ANDROID_HOME"] = ANDROID_SDK_PATH
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "platform-tools")
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "cmdline-tools", "latest", "bin")

ADB_PATH = os.path.join(ANDROID_SDK_PATH, "platform-tools", "adb.exe")
porta = porta_livre()
# 🔌 Busca os dispositivos conectados via ADB
def pegar_udid():
    result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]  # Ignora o cabeçalho
    udids = [line.split('\t')[0] for line in lines if '\tdevice' in line]

    print(f"📱 Dispositivos conectados: {udids}")
    return udids


@retry(max_tentativas=3, delay=1)
def criar_driver(porta, udid):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = udid
    options.automation_name = "UiAutomator2"
    options.udid = udid
    options.app_package = "com.whatsapp.w4b"
    options.app_activity = "com.whatsapp.HomeActivity"
    options.auto_grant_permissions = True

    print(f"🧩 Criando driver para dispositivo {udid} na porta {porta}...")

    driver = webdriver.Remote(
        command_executor=f'http://localhost:{porta}',  # correto com base-path '/'
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
                '--port', porta,
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
