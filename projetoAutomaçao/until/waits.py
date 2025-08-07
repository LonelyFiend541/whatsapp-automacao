import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from typing import Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC  # ✅ correto
from selenium.webdriver.support.ui import WebDriverWait


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




class WebDriverException(Exception):
    pass


class ChipBanidoException(Exception):
    pass


class ChipEmAnaliseException(Exception):
    pass
