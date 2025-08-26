import re
from selenium.common.exceptions import TimeoutException
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from until.waits import *
import subprocess
import time


class WaBussinesPage:

    def __init__(self, driver):
        self.driver = driver

    # Nota: Este mét0do utiliza o decorador @retry para tentar novamente até 3 vezes em caso de falha, com 1 segundos de espera entre as tentativas.
    #@retry(max_tentativas=3, delay=1)
    def pegar_numero_chip2(self, udid):
        """
        Tenta obter o número do chip via discador Samsung.
        Retorna o número ou lança exceção em caso de erro.
        """

        try:
            subprocess.run(f'adb -s {udid} shell am start -a android.intent.action.CALL -d tel:*846%23', shell=True)
            try:
                escolher_chip = esperar_um_dos_elementos_visiveis(self.driver, (
                    (By.ID, 'com.samsung.android.incallui:id/title'),
                    (By.ID, 'android:id/alertTitle'),
                    (By.ID, 'android:id/alertTitle'),))

                if escolher_chip:
                    chip2 = esperar_um_dos_elementos_visiveis(self.driver, ((By.XPATH,'//android.widget.TextView[@text="SIM 2"]'),
                    (By.XPATH, '(//android.widget.TextView[@resource-id="com.google.android.dialer:id/label"])[2]'), ))
                    chip2.click()
            except:
                pass
            ok = esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button1'))
            mensagem_elem = esperar_elemento_visivel(self.driver, (By.ID, "android:id/message"), 20)
            if mensagem_elem:
                mensagem_texto = mensagem_elem.text

                if re.search(r"\[\d+\]", mensagem_texto):
                    numero = int(re.search(r"\[(\d+)]", mensagem_texto).group(1))
                    print(f"Número encontrado: {numero}")
                    ok.click()
                    return numero

                elif 'MMI inválido' in mensagem_texto:
                    ok.click()
                    raise RuntimeError('Número cancelado')

                elif 'UNKNOWN APPLICATION' in mensagem_texto:
                    ok.click()
                    raise RuntimeError('Chip da TIM não identificado')

                else:
                    ok.click()
                    raise RuntimeError(f"Mensagem inesperada: {mensagem_texto}")
            else:
                raise RuntimeError('Nenhuma mensagem retornada pelo USSD')
        except Exception as e:
            print(f"[pegar_numero_chip2] Exceção inesperada: {e}")
            raise

    def aceitar_termos(self):
        try:
            termos = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/eula_accept'))
            termos.click()
        except:
            print("[aceitar_termos] Erro: Não aceitou os termos")
            return False

    def usar_outro_chip(self):
        try:
            outro_chip = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/use_a_different_number"), 7)
            outro_chip.click()
        except:
            print("nao usou o mesmo numero")
            pass

    def registrar_numero(self, numero):
        try:
            registrar_phone = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/registration_phone"))
            registrar_phone.send_keys(numero)
            ddd = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/registration_cc"))
            if ddd.text != "Código do país de Brasil, mais 55":
                ddd.clean()
                ddd.send_keys("55")
            submit = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/registration_submit'))
            submit.click()
            bolean, mudarChip = elemento_esta_visivel(self.driver, (By.ID, 'android:id/message'))
            if bolean:
                mudarChip = esperar_elemento_visivel(self.driver, (By.ID, "android:id/button1"))
                mudarChip.click()
        except:
            return False

    def usar_numero(self):
        try:
            confirmar, elemento = elemento_esta_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/restore_from_consumer_view"),)
            if confirmar:
                mesmo_numero = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/use_consumer_app_info_button"))
                mesmo_numero.click()
        except:
            pass

    def confirmar_sms(self, numero):
        try:
            outro_metodo = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/secondary_button'))
            outro_metodo.click()
            sms = esperar_elemento_visivel(self.driver, (By.XPATH, '(//android.widget.RadioButton[@resource-id="com.whatsapp.w4b:id/reg_method_checkbox"])[2]'))
            sms.click()
            bt_continue = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/continue_button'))
            bt_continue.click()
        except:
            return False

    def verificar_banido(self, numero):
        try:
            banido = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/action_button"))
            if banido.text == "REGISTRAR NOVO NÚMERO DE TELEFONE":
                print("❌ Numero Banido ❌")
                status = 'Banido'
                return True, status
        except:
            return False, None

    def verificar_analise(self,numero):
        try:
            analise = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/action_button'))
            if analise.text == 'VERIFICAR STATUS DA ANÁLISE':
                print('⛔ Em Analise ⛔')
                status = 'Analise'
                return True, status
        except:
            return False, None

    def colocar_em_analise(self, numero):
        try:
            pedirAnalise = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/action_button'))
            if pedirAnalise.text == "PEDIR ANÁLISE":
                pedirAnalise.click()
                enviar = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/submit_button'))
                enviar.click()
                analise = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/appeal_submitted_heading'))
                print(analise.text)
                status = 'Analise'
                return True, status
        except:
            return False, None

    def confirmar_chip(self):
        try:
            confirmar = esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button1'))
            confirmar.click()
        except :
            return False

    def abrir_app_mensagens(self):
        try:
            time.sleep(5)
            campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/verify_sms_code_input"))
            time.sleep(1)
            self.driver.activate_app('com.samsung.android.messaging')
            print('abriu o app')
            return True
        except Exception as e:
            print(f"[abrir_app_mensagens] Erro: Não abriu o app de mensagem")
            return False

    def pegarCodigoSms(self):
        try:
            achou, elemento = esperar_elemento_scroll(self.driver, (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'Codigo do WhatsApp Business:')]"), 30)
            elemento.click()
            mensagens = esperar_elementos_xpath(self.driver, '//android.widget.TextView[contains(@text, "Codigo do WhatsApp Business:")]')
            if mensagens:
                ultima_mensagem = mensagens[0]
                codigoCompleto = ultima_mensagem.get_attribute('text')
                padrao = r'(\d+)-(\d+)'
                resultado = re.search(padrao, codigoCompleto)
                codigo = resultado.group(1) + resultado.group(2)
                print(f'pegou o codigo {codigo}')
                self.driver.terminate_app("com.samsung.android.messaging")
                return True, codigo
            print('[pegarCodigoSms] Nenhuma mensagem encontrada.')
            self.driver.terminate_app("com.samsung.android.messaging")
            return False, None
        except:
            self.driver.terminate_app("com.samsung.android.messaging")
            print(f"[pegarCodigoSms] Não pegou o codigo")
            return False, None

    def voltarWhatsapp(self):
        try:
            self.driver.activate_app("com.whatsapp.w4b")
            campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/action_button"))
            campo.click()
            print('voltou')
            return True
        except:
            print(f"[voltarWhatsapp] Erro: Não voltou para o whatsapp")
            pass

    def colocar_codigo(self, codigo):
        try:
            print(codigo)
            input_codigo = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/verify_sms_code_input'))
            input_codigo.send_keys(codigo)
        except:
            print("[colocar_codigo] Erro: Não inseriu o código")
            return False

    def negar_backup(self):
        try:
            bolean, permissao = elemento_esta_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/submit'))
            if bolean:
                permissao.click()
            negar = esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button2'), 20)
            negar.click()
            return True
        except:
            print("[negar_backup] Erro: Não clicou em negar backup")
            return False

    def colocar_nome(self):
        try:
            nome = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.EditText'))
            if nome.text != "Call Center":
                nome.send_keys("Call Center")
                continuar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
                continuar.click()
            else:
                continuar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
                continuar.click()
        except:
            print(f"[colocar_nome] Erro: Não colocou o nome")
            return False

    def selecionar_empresa(self):
        try:
            empresa = esperar_elemento_visivel(self.driver, (By.XPATH,'//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]/android.view.View[1]'))
            xpath_botao_outros = esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[3]'))
            checked = xpath_botao_outros.get_attribute("enabled")
            if checked == "true":
                avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
                avancar.click()
            else:
                achou, categoria = existe_um_dos_elementos(self.driver, ((By.XPATH, '//android.widget.TextView[@content-desc="Não é uma empresa"]'), (By.XPATH, '//android.widget.TextView[@text="Outras empresas"]'),))
                #categoria = esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]/android.view.View[1]'))
                if achou:
                    categoria.click()
                    print("empresa selecionada ")
                    avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
                    avancar.click()
                else:
                    mais_categoria = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Mais categorias"]'))
                    mais_categoria.click()
                    achou, categoria = existe_um_dos_elementos(self.driver, ((By.XPATH,'//android.widget.TextView[@content-desc="Não é uma empresa"]'),
                                                                             (By.XPATH,'//android.widget.TextView[@text="Outras empresas"]'),))
                    categoria.click()
                    avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
                    avancar.click()

            return True

        except Exception as e:
            print(f"[selecionar_empresa] Erro: Não selecionou a empresa -> {e}")
            return False

    def horario_de_atendimento(self):
        try:
            esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]'))
            horario = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Sempre aberta"]'))
            horario.click()
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
            avancar.click()
            esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]'))
            avancar_2 = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
            avancar_2.click()
        except:
            print("[horario_de_atendimento] Erro: Não concluiu o horário")
            return False

    def foto_perfil(self):
        try:
            esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Adicionar foto do perfil"]'))
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[2]'))
            avancar.click()
        except:
            print("[foto_perfil] Erro: Não avançou na foto de perfil")
            return False

    def formas_encontrar_empresa(self):
        try:
            esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Mais formas de encontrar sua empresa"]'))
            pular = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Pular"]'))
            pular.click()
            esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Adicionar descrição da empresa"]'))
            pular_2 = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Pular"]'))
            pular_2.click()
        except:
            print('[formas_encontrar_empresa] Erro: Não concluiu o pulo')
            return False

    def selecionar_descricao(self):
        try:
            esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Adicionar descrição da empresa"]'))
            descricao = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.EditText/android.view.View[2]'))
            descricao.send_key("Empresa especializada em soluções de atendimento ao cliente, oferecendo suporte eficiente, central de chamadas e serviços de relacionamento para maximizar a satisfação e fidelização dos clientes.")
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[2]'))
            checked = avancar.get_attribute("enabled")
            if checked == 'true':
                avancar.click()
            else:
                pular = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Pular"]'))
                pular.click()
            teve, email = elemento_esta_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/headline'))
            if teve:
                esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/secondary_button')).click()
            print("Whatsapp Bussines concluido")
        except:
            pass

    def selecionar_menu(self):
        menu = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/menuitem_overflow'))
        menu.click()
        dispositivo = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@resource-id="com.whatsapp.w4b:id/title" and @text="Dispositivos conectados"]'))
        dispositivo.click()

    def conectar_dispositivo(self):
        conectar = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/link_device_button'))
        conectar.click()
        conectar_numero = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/bottom_banner'))
        conectar_numero.click()

    def colocar_codigo_instancia(self, codigo_api):
        campo = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/enter_code_boxes'))
        codigo_1 = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.EditText[@content-desc="Insira o código de 8 caracteres, campo 1 de 8"]'))
        codigo_1.send_keys(codigo_api)

    def salvar(self, numero):
        nome = esperar_elemento_visivel(self.driver, (By.ID, 'com.samsung.android.app.contacts:id/arrowButton'))
        nome.send_keys(f"Call Center: {numero}")
        telefone = esperar_elemento_visivel(self.driver, (By.XPATH, '(//android.widget.RelativeLayout[@resource-id="com.samsung.android.app.contacts:id/titleLayout"])[1]'))
        telefone.send_keys(numero)
        salvar = esperar_elemento_visivel(self.driver, (By.ID, 'com.samsung.android.app.contacts:id/menu_done'))
        salvar.click()
        self.driver.terminate_app("	com.samsung.android.app.contacts")
