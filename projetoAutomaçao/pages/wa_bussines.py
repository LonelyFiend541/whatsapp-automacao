import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from until.utilitys import esta_ativo_por_xpath
from until.utilitys import *
from until.waits import *


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
            ddd = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp.w4b:id/registration_phone"))
            if ddd.text == "":
                ddd.send_keys("55")
            submit = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp.w4b:id/registration_submit'))
            submit.click()
        except:
            print("[registrar_numero] Erro: Não registrou o número")
            return False

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

            appMensagem = esperar_elemento_visivel(self.driver, (By.XPATH,
                                                                 '//android.widget.TextView[@text="<#> Codigo do WhatsApp Business:"]'))
            appMensagem.click()

            mensagem = self.driver.find_elements(By.XPATH,
                                                 "//android.widget.LinearLayout[contains(@content-desc, 'WhatsApp')]")
            if mensagem:
                ultima_mensagem = mensagem[-1]
                codigoCompleto = ultima_mensagem.get_attribute('content-desc')
                padrao = r'(\d+)-(\d+)'
                resultado = re.search(padrao, codigoCompleto)
                codigo = resultado.group(1) + resultado.group(2)
                self.driver.terminate_app("com.samsung.android.messaging")
                print('pegou o codigo')
                return codigo
            print('[pegarCodigoSms] Nenhuma mensagem encontrada.')
            return None
        except Exception as e:
            print(f"[pegarCodigoSms] Erro: e")
            return None

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
            negar = esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button2'), 20)
            negar.click()
        except:
            print("[negar_backup] Erro: Não clicou em negar backup")
            return False

    def colocar_nome(self):
        try:
            nome = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.EditText'))
            nome.send_keys("Call Center")
            continuar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.Button'))
            continuar.click()
        except:
            print(f"[colocar_nome] Erro: Não colocou o nome")
            return False

    def selecionar_empresa(self):
        try:
            empresa = esperar_elemento_visivel(self.driver, (By.XPATH,'//android.widget.TextView[@text="Selecionar a categoria da sua empresa"]'))
            xpath_botao_outros = '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]/android.view.View[1]'
            ativo = esta_ativo_por_xpath(self.driver, xpath_botao_outros)
            if not ativo:
                categoria = esperar_elemento_visivel(self.driver,(By.XPATH, '//android.widget.TextView[@text="Outras empresas"]'))
                categoria.click()
            print("empresa selecionada ")
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
            avancar.click()
            return True

        except Exception as e:
            print(f"[selecionar_empresa] Erro: Não selecionou a empresa -> {e}")
            return False

    def horario_de_atendimento(self):
        try:
            horario = esperar_elemento_visivel(self.driver, (By.XPATH, '//androidx.compose.ui.platform.ComposeView/android.view.View/android.view.View/android.view.View[1]/android.view.View[2]/android.widget.RadioButton'))
            horario.click()
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
            avancar.click()
            time.sleep(1)
            avancar.click()
            time.sleep(1)
        except:
            print("[horario_de_atendimento] Erro: Não concluiu o horário")
            return False

    def foto_perfil(self):
        try:
            avancar = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Avançar"]'))
            avancar.click()
        except:
            print("[foto_perfil] Erro: Não avançou na foto de perfil")
            return False

    def formas_encontrar_empresa(self):
        try:
            pular = esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@text="Pular"]'))
            pular.click()
            time.sleep(1)
            pular.click()
        except:
            print('[formas_encontrar_empresa] Erro: Não concluiu o pulo')
            return False
