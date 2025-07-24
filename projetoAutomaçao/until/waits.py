from typing import Any
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def esperar_elemento_visivel(driver: object, locator: object, timeout: object = 10) -> Any:
    """

    :rtype: Any
    """
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))

def verificar_elemento_visivel(driver: object, locator: object, timeout: object = 10) -> Any:
    try:
        esperar_elemento_visivel(driver, locator, timeout)
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        print(f"Elemento {locator} não apareceu após {timeout} segundos.")
        return None
        pass


