from typing import Any

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def esperar_elemento_visivel(driver: object, locator: object, timeout: object = 15) -> Any:
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))

def verificar_elemento_visivel(driver: object, locator: object, timeout: object = 15) -> Any:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        print(f"Elemento {locator} não apareceu após {timeout} segundos.")
        return None

    return
