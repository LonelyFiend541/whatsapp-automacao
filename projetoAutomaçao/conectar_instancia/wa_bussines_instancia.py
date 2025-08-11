from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import AppiumService
from drivers.drivers_whatsapp_bussines import *
from integration.api import *
from pages.wa_bussines import *


def iniciar_ambiente_para_todos():
    """
    Inicia Appium e drivers para todos os dispositivos em paralelo.
    Retorna lista de tuplas (driver, service).
    """
    udids = pegar_udids()
    drivers_services = []

    with ThreadPoolExecutor(max_workers=len(udids)) as executor:
        futures = [
            executor.submit(iniciar_appium_para_udid, udid, gerar_porta_por_udid(udid))
            for udid in udids
        ]
        for future in as_completed(futures):
            driver_service = future.result()
            if driver_service[0] and driver_service[1]:
                drivers_services.append(driver_service)

    return drivers_services

def iniciar_appium_para_udid(udid, porta):
    """
    Inicia Appium e driver para um udid específico.
    Retorna (driver, service) ou (None, None) em caso de erro.
    """
    try:
        service = iniciar_appium(porta)
        driver = criar_driver_wa(udid, porta)
        return (driver, service)
    except Exception as e:
        print(f"❌ Erro ao iniciar Appium para {udid}: {e}")
        return (None, None)

def criar_driver_wa(udid, porta):
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = udid
    options.automation_name = "UiAutomator2"
    options.udid = udid
    options.app_package = "com.whatsapp.w4b"
    options.app_activity = "com.whatsapp.HomeActivity"
    options.auto_grant_permissions = True
    options.no_reset = True

    print(f"🧩 Criando driver para dispositivo {udid} na porta {porta}...")

    driver = webdriver.Remote(
        command_executor=f"http://localhost:{porta}",  # Appium 2.x não usa /wd/hub
        options=options
    )
    return driver




def rodar_conectar_instancia(driver):
    try:
        print(f"▶️ Iniciando automação no dispositivo: {driver.capabilities['deviceName']}")
        whatsappbussines = WaBussinesPage(driver)
        udid = driver.capabilities["deviceName"]
        print(f"📱 Iniciando automação para: {udid}")
        numero = whatsappbussines.pegar_numero_chip2(udid)
        whatsappbussines.selecionar_menu()
        whatsappbussines.conectar_dispositivo()
        codigo_api = get_codigo(numero)
        whatsappbussines.colocar_codigo_instancia(codigo_api)
        print(f"✅ Automação concluída para: {udid}")

    except Exception as e:
        print(f"❌ Erro no dispositivo {driver.capabilities['deviceName']}: {e}")


    # def instancia_bussines():


if __name__ == "__main__":
    drivers_services = iniciar_ambiente_para_todos()
    drivers = [ds[0] for ds in drivers_services if ds[0] is not None]

    with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
        futures = [executor.submit(rodar_conectar_instancia, driver) for driver in drivers]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Erro durante execução paralela: {e}")

    for _, service in drivers_services:
        if service and service.is_running:
            print("🛑 Parando Appium...")
            service.stop()
