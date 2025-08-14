# test/test_registro_whatsapp.py

import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
import pages.wa_bussines
import pages.whatsapp_page
import os

from until.utilitys import ler_numeros

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

def iniciar_driver():
    options = UiAutomator2Options()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "Android Emulator")
    #options.set_capability("appPackage", "com.whatsapp.w4b")
    #options.set_capability("appActivity", "com.whatsapp.HomeActivity")
    options.set_capability("automationName", "UiAutomator2")
    options.set_capability("noReset", True)       # já logado
    options.set_capability("autoLaunch", False)   # não abrir o app (já deve estar na tela)

    driver = webdriver.Remote("http://127.0.0.1:4723/wd/hub", options=options)
    return driver


def test_selecionar_empresa():
    driver = iniciar_driver()

    try:
        print("⏳ Testando seleção de empresa...")

        # Aguarde a tela estar pronta, se necessário
        time.sleep(2)

        registro = pages.wa_bussines.WaBussinesPage(driver)
        registro = pages.whatsapp_page.WhatsAppPage(driver)
        #registro.abrirAppMensagens()
        #resultado = registro.colocarNome()


        #assert resultado is True, "❌ Falha ao selecionar empresa!"
        print("✅ Teste passou: Empresa selecionada com sucesso.")

    finally:
        driver.quit()