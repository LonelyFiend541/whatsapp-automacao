import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from typing import Optional, Tuple
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # ✅ correto



# ...existing code...
def clicar_elemento(self, by, value, timeout=10):
    try:
        esperar_elemento_visivel(self.driver, (by, value), timeout).click()
        return True
    except Exception as e:
        print(f"Erro ao clicar elemento {value}: {e}")
        return False

def texto_elemento(self, by, value, timeout=10):
    try:
        elem = esperar_elemento_visivel(self.driver, (by, value), timeout)
        return elem.text if elem else ""
    except Exception as e:
        print(f"Erro ao obter texto do elemento {value}: {e}")
        return ""
# ...existing code...

def esperar_um_dos_elementos_visiveis(
    driver: WebDriver,
    locators: Tuple[Tuple[By, str], ...],
    timeout: int = 10
):
    """
    Aguarda até que pelo menos um dos elementos fornecidos fique visível.

    :param driver: Instância do WebDriver
    :param locators: Lista de tuplas (By, valor) com os elementos possíveis
    :param timeout: Tempo máximo de espera (em segundos)
    :return: O primeiro WebElement visível encontrado
    :raises TimeoutException: Se nenhum dos elementos estiver visível no tempo limite
    """
    try:
        wait = WebDriverWait(driver, timeout)

        def qualquer_visivel(driver):
            for locator in locators:
                try:
                    el = driver.find_element(*locator)
                    if el.is_displayed():
                        return el
                except Exception:
                    continue
            return False

        return wait.until(qualquer_visivel)

    except TimeoutException:
        print(f"⏰ Nenhum dos elementos {locators} ficou visível após {timeout}s.")
        raise
    except WebDriverException as e:
        print(f"🛑 Erro de comunicação com o driver: {e}")
        raise
def existe_um_dos_elementos(
    driver: WebDriver,
    locators: Tuple[Tuple[By, str], ...],
    timeout: int = 10
) -> Tuple[bool, Optional[WebElement]]:
    """
    Retorna (True, elemento) se pelo menos um dos elementos aparecer.
    Caso contrário, retorna (False, None).
    """
    try:
        def encontrar(d):
            for loc in locators:
                try:
                    el = d.find_element(*loc)
                    if el.is_displayed():
                        return el
                except Exception:
                    continue
            return False

        el = WebDriverWait(driver, timeout).until(encontrar)
        return True, el

    except (TimeoutException, WebDriverException):
        return False, None

def esperar_elemento_visivel(driver: object, locator: object, timeout: object = 10):
    try:
        return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    except WebDriverException as e:
        print(f"🛑 Erro de comunicação com Appium: {e}")
        raise  # propaga para o executor capturar
def verificar_elemento_visivel(driver: object, locator: object, timeout: object = 10) ->  Any:
    try:
        esperar_elemento_visivel(driver, locator, timeout)
        return WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
    except TimeoutException:
        print(f"Elemento {locator} não apareceu após {timeout} segundos.")
        return None
        pass

def executar_paralelo_arg(*funcoes):
    threads = []
    for func, *args in funcoes:
        thread = threading.Thread(target=func, args=tuple(args))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

def executar_paralelo_normal(*funcoes):
    with ThreadPoolExecutor(max_workers=len(funcoes)) as executor:
        # Envia cada função (sem argumentos) para execução
        futures = [executor.submit(func) for func in funcoes]

        for future in as_completed(futures):
            exc = future.exception()
            if exc:
                raise exc  # Propaga a exceção original corretamente



def executar_paralelo(*tarefas):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from collections.abc import Callable

    tarefas_padronizadas = []
    for t in tarefas:
        if isinstance(t, Callable):
            tarefas_padronizadas.append((t, (), {}))
        elif isinstance(t, tuple):
            if len(t) == 1 and isinstance(t[0], Callable):
                tarefas_padronizadas.append((t[0], (), {}))
            elif len(t) == 3:
                tarefas_padronizadas.append(t)
            else:
                raise ValueError("Tupla inválida. Use (func), (func, args, kwargs)")
        else:
            raise ValueError("Cada tarefa deve ser uma função ou uma tupla válida.")

    with ThreadPoolExecutor() as executor:
        futuros = {
            executor.submit(func, *args, **kwargs): func
            for func, args, kwargs in tarefas_padronizadas
        }
        for future in as_completed(futuros):
            try:
                resultado = future.result()
                if isinstance(resultado, tuple):
                    booleano, status = resultado
                else:
                    booleano, status = resultado, None

                if booleano:
                    for f in futuros:
                        if not f.done():
                            f.cancel()
                    print("⚠️ Uma das funções retornou True. Interrompendo automação.")
                    return True, status
            except Exception as e:
                print(f"❌ Erro ao executar função paralela: {e}")
    return False, None

def esperar_elemento_scroll(driver, locator, timeout=10, max_scrolls=5) -> Tuple[bool, Optional[object]]:
    """
    Espera um elemento ficar visível e rola a tela até encontrá-lo, se necessário.

    :param driver: Instância do driver Appium
    :param locator: Tupla (By.ID, "id_do_elemento") ou (By.XPATH, "xpath_do_elemento")
    :param timeout: Tempo máximo de espera por cada tentativa
    :param max_scrolls: Número máximo de scrolls caso o elemento não esteja visível
    :return: (True, elemento) se encontrado, (False, None) caso contrário
    """
    by, value = locator

    for _ in range(max_scrolls):
        try:
            elemento = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
            return True, elemento
        except (NoSuchElementException, WebDriverException):
            try:
                # Scroll para ID usando UiScrollable (Android)
                if by == AppiumBy.ID:
                    driver.find_element(
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView(new UiSelector().resourceId("{value}"));'
                    )
                # Scroll para XPath ou texto
                elif by == AppiumBy.XPATH:
                    tamanho = driver.get_window_size()
                    start_x = tamanho['width'] // 2
                    start_y = int(tamanho['height'] * 0.8)
                    end_y = int(tamanho['height'] * 0.2)
                    driver.swipe(start_x, start_y, start_x, end_y, 800)
                time.sleep(1)  # aguarda animação
            except Exception:
                pass  # ignora erro de scroll e tenta novamente

    # Se não encontrou após max_scrolls, retorna False
    return False, None


def esperar_elementos_xpath(driver, xpath, timeout=10):
    """
    Espera elementos aparecerem e retorna lista ordenada (mais recente primeiro).

    :param driver: Instância Appium
    :param xpath: String XPath para localizar os elementos
    :param timeout: Tempo máximo de espera
    :return: Lista de elementos ordenados (mais recente primeiro)
    """
    try:
        # Espera pelo menos um aparecer
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((AppiumBy.XPATH, xpath))
        )

        # Pega todos
        elementos = driver.find_elements(AppiumBy.XPATH, xpath)

        if not elementos:
            return []

        # Em apps de mensagens, geralmente o último é o mais recente
        # então invertendo para o mais recente ficar no índice 0
        elementos_ordenados = list(reversed(elementos))

        return elementos_ordenados

    except Exception as e:
        print(f"[esperar_elementos_xpath] Nenhum elemento encontrado: {e}")
        return []

def elemento_esta_visivel(
    driver: WebDriver,
    locator: Tuple[By, str],
    timeout: int = 5
) -> Tuple[bool, Optional[WebElement]]:
    """
    Verifica se o elemento está visível dentro do tempo limite.

    :param driver: Instância do WebDriver.
    :param locator: Tupla (By, valor) localizando o elemento.
    :param timeout: Tempo máximo de espera em segundos.
    :return: (True, elemento) se visível, ou (False, None) caso contrário.
    """
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )
        return True, el
    except TimeoutException:
        return False, None






class WebDriverException(Exception):
    pass


class ChipBanidoException(Exception):
    pass


class ChipEmAnaliseException(Exception):
    pass
