# test/test_registro_whatsapp.py

from appium import webdriver
from appium.options.android import UiAutomator2Options

import pages.wa_bussines
from until.utilitys import esta_ativo_por_xpath
from pages.wa_bussines import *  # ajuste o caminho se necessário
from until.waits import esperar_elemento_visivel
import time


def iniciar_driver():
    options = UiAutomator2Options()
    options.set_capability("platformName", "Android")
    options.set_capability("deviceName", "Android Emulator")
    options.set_capability("appPackage", "com.whatsapp.w4b")
    options.set_capability("appActivity", "com.whatsapp.HomeActivity")
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
        registro.colocar_nome()
        resultado = registro.selecionar_empresa()

        assert resultado is True, "❌ Falha ao selecionar empresa!"
        print("✅ Teste passou: Empresa selecionada com sucesso.")

    finally:
        driver.quit()