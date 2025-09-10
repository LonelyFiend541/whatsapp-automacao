from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.appium_service import AppiumService
from contatos import contatos
from contatos.contatos import *
import until.utilitys
from integration.IA import tratar_erro_ia
from pages.wa_bussines import *
from until.utilitys import *
import subprocess
import os

# Configura Android SDK para o Appium achar o adb
# Configura variáveis do Android SDK
ANDROID_SDK_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),  # pasta do script atual
        "..", "patch"
    )
)

NUMERO_DIR = "Numeros"
os.makedirs(NUMERO_DIR, exist_ok=True)

def carregar_recadastro():
    caminho = os.path.join(NUMERO_DIR, f"dados_recadastro.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}")
            tratar_erro_ia(e)
    return []

os.environ["ANDROID_HOME"] = ANDROID_SDK_PATH
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "platform-tools")
os.environ["PATH"] += os.pathsep + os.path.join(ANDROID_SDK_PATH, "cmdline-tools", "latest", "bin")

ADB_PATH = os.path.join(ANDROID_SDK_PATH, "platform-tools", "adb.exe")

# 🔌 Busca os dispositivos conectados via ADB
def pegar_udids():
    result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    udids = [line.split('\t')[0] for line in lines if 'device' in line]
    print(f"📱 Dispositivos conectados: {udids}")
    return udids


def porta_livre(porta_inicial=4723):
    porta = porta_inicial
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', porta)) != 0:
                return porta
            porta += 2  # evita conflitos de porta paralelos


def gerar_porta_por_udid(udid, base_porta=4723):
    hash_val = abs(hash(udid)) % 1000
    return base_porta + (hash_val * 2)


def iniciar_appium(porta):
    service = AppiumService()
    service.start(args=[
        '--port', str(porta),
        '--base-path', '/',
        '--use-drivers', 'uiautomator2'
    ])

    for _ in range(10):
        if service.is_running:
            print(f"✅ Appium iniciado na porta {porta}")
            return service
        time.sleep(1)

    raise RuntimeError(f"❌ Falha ao iniciar Appium na porta {porta}")


def criar_drivers_whatsapp_bussines(udid, porta):
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
        command_executor=f"http://localhost:{porta}",  # Appium 2.x não usa /wd/hub
        options=options
    )
    return driver


# 🟢 Instância única para controle do serviço Appium
def iniciar_appium_para_udid(udid, porta):
    """
    Inicia Appium e driver para um udid específico.
    Retorna (driver, service) ou (None, None) em caso de erro.
    """
    try:
        service = iniciar_appium(porta)
        driver = criar_drivers_whatsapp_bussines(udid, porta)
        return (driver, service)
    except Exception as e:
        print(f"❌ Erro ao iniciar Appium para {udid}: {e}")
        return (None, None)


def rodar_automacao_whatsapp_bussines(driver):
    try:
        print(f"▶️ Iniciando automação no dispositivo: {driver.capabilities['deviceName']}")
        whatsappbussines = WaBussinesPage(driver)
        udid = driver.capabilities["deviceName"]
        print(f"📱 Iniciando automação para: {udid}")
        dados = carregar_recadastro()
        for dado in dados:
            if dado["UDID"] == udid:
                chip2 = dado.get("Chip 2")
                print(chip2)
        if not chip2:
            try:
                numero = whatsappbussines.pegar_numero_chip2(udid)
            except Exception as e:
                tratar_erro_ia(e)
                return None
        else:
            numero = chip2
        whatsappbussines.aceitar_termos()
        whatsappbussines.usar_outro_chip()
        whatsappbussines.registrar_numero(numero)
        whatsappbussines.usar_numero()
        whatsappbussines.confirmar_chip()
        boolean, status = executar_paralelo(

            (whatsappbussines.verificar_banido, (numero, ), {}),
            (whatsappbussines.verificar_analise, (numero, ), {}),
            (whatsappbussines.colocar_em_analise, (numero, ), {}),
            (whatsappbussines.confirmar_sms, (numero, ), {})
        )
        if boolean:
            print(f"⛔ Chip com problema detectado no dispositivo {udid}. Encerrando automação.")
            #table.salvar_numeros(numero, status)
            return
        if whatsappbussines.abrir_app_mensagens():
            sn, codigo = whatsappbussines.pegarCodigoSms()
            whatsappbussines.colocar_codigo(codigo)
        whatsappbussines.negar_backup()
        #table.salvar_numeros(numero, status)
        whatsappbussines.colocar_nome()
        whatsappbussines.selecionar_empresa()
        whatsappbussines.horario_de_atendimento()
        whatsappbussines.foto_perfil()
        whatsappbussines.formas_encontrar_empresa()
        whatsappbussines.selecionar_descricao()

        print(f"✅ Automação concluída para: {udid}")

    except Exception as e:
        print(f"❌ Erro no dispositivo {driver.capabilities['deviceName']}: {e}")


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

def bussines():
#if __name__ == "__main__":
    drivers_services = iniciar_ambiente_para_todos()
    drivers = [ds[0] for ds in drivers_services if ds[0] is not None]

    with ThreadPoolExecutor(max_workers=len(drivers)) as executor:
        futures = [executor.submit(rodar_automacao_whatsapp_bussines, driver) for driver in drivers]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Erro durante execução paralela: {e}")

    for _, service in drivers_services:
        if service and service.is_running:
            print("🛑 Parando Appium...")
            service.stop()
