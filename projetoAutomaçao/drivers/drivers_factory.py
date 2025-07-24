from appium import webdriver
from appium.options.android import UiAutomator2Options
import subprocess


def pegar_udid():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    udid = [line.split('\t')[0]
    for line in lines if 'device' in line]
    print(udid)
    return udid


def criar_driver(porta, udid):
    # Criando as opções para o Appium
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.device_name = udid
    options.automation_name = "UiAutomator2"
    options.udid = udid
    options.app_package = "com.whatsapp"
    options.app_activity = "com.whatsapp.Main"
    options.auto_grant_permissions = True

    # Inicializando o driver com as opções
    driver = webdriver.Remote(
        command_executor=f'http://localhost:{porta}/wd/hub',
        options=options
    )

    return driver


