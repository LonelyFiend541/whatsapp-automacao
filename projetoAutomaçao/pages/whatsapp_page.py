import re
from tkinter import simpledialog

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from appium.webdriver.common.appiumby import AppiumBy
from until.utilitys import *

from until.waits import *
import subprocess
import time


class WhatsAppPage:

    def __init__(self, driver):
        self.driver = driver

    @retry(max_tentativas=3, delay=1)
    def pegarNumeroChip1(self, udid):
        """
        Tenta obter o número do chip via discador Samsung.
        Retorna o número ou lança exceção em caso de erro.

        Nota: Este méodo utiliza o decorador @retry para tentar novamente até 3 vezes em caso de falha, com 1 segundos de espera entre as tentativas.
        """

        try:

            subprocess.run(f'adb -s {udid} shell am start -a android.intent.action.CALL -d tel:*846%23', shell=True)
            try:
                escolher_chip = esperar_um_dos_elementos_visiveis(self.driver,(
                (By.ID, 'com.samsung.android.incallui:id/title'),
                (By.ID, 'android:id/alertTitle'),))

                if escolher_chip:
                    chip1 = esperar_um_dos_elementos_visiveis(self.driver,((By.XPATH,'//android.widget.TextView[@text="SIM 1"]'),
                    (By.XPATH, '(//android.widget.TextView[@resource-id="com.google.android.dialer:id/label"])[1]')),)
                    chip1.click()
            except:
                pass
            ok = esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button1'))
            mensagem_elem = esperar_elemento_visivel(self.driver, (By.ID, "android:id/message"), 20)
            if mensagem_elem:
                mensagem_texto = mensagem_elem.text

                if re.search(r"\[\d+]", mensagem_texto):
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
            print(f"[pegar_numero_chip1] Exceção inesperada: {e}")
            raise

    def abrirWhatsapp(self):
        try:
            time.sleep(2)
            self.driver.activate_app('com.whatsapp')
            return True
        except Exception as e:
            print(f"[abrirWhatsapp] Erro: {e}")
            return False

    def selecionar_linguagem(self):
        try:
            boolean, idioma = esperar_elemento_visivel(self.driver, (By.XPATH,'//android.widget.CheckBox[@content-desc="Selecionar (idioma do dispositivo) como idioma do app"]'))
            if boolean:
                idioma.click()
        except:
            return False

    def clicar_prosseguir(self):
        try:
            esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/eula_accept')).click()
            return True
        except Exception as e:
            print(f"[clicar_prosseguir] Erro: {e}")
            return False

    def inserir_numero(self, numero):
        try:
            campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/registration_phone"))
            campo.send_keys(numero)
            dd = self.driver.find_element(By.ID, 'com.whatsapp:id/registration_cc')
            if dd.text == " ":
                dd.send_keys('55')
            botao = self.driver.find_element(By.ID, "com.whatsapp:id/registration_submit")
            botao.click()
            print('colocou o numero')
            return True
        except Exception as e:
            print(f"[inserir_numero] Erro: {e}")
            return False

    def confirmarNumero(self):
        try:
            confirmar = esperar_elemento_visivel(self.driver, (By.ID, "android:id/button1"), 30)
            confirmar.click()
            time.sleep(0.5)
            return True
        except Exception as e:
            return False

    def verificarBanido(self, numero):
        try:
            banido = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/action_button"))
            if banido.text == "REGISTRAR NOVO NÚMERO DE TELEFONE":
                print("❌ Numero Banido ❌")
                status = 'Banido'
                return True, status
        except:
            return False, None

    def pedirAnalise(self, numero):

        try:
            pedirAnalise = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/action_button'))
            if pedirAnalise.text == "PEDIR ANÁLISE":
                pedirAnalise.click()
                enviar = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/submit_button'))
                enviar.click()
                analise = esperar_elemento_visivel(self.driver,
                                                   (By.ID, 'com.whatsapp:id/appeal_submitted_heading'))
                print(analise.text)
                status = 'Analise'
                return True, status

        except:
            return False, None

    def verificarAnalise(self, numero):
        try:
            analise = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/action_button'))
            if analise.text == 'VERIFICAR STATUS DA ANÁLISE':
                print('⛔ Em Analise ⛔')
                status = 'Analise'
                return True, status
        except:
            return False, None

    def verificarChip(self, numero):
        try:

            tipoderecebimento = esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/entire_content_holder'))

            if tipoderecebimento:
                esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/secondary_button')).click()
                try:
                    esperar_elemento_visivel(self.driver, (By.XPATH,
                                                           '(//android.widget.RadioButton[@resource-id="com.whatsapp:id/reg_method_checkbox"])[2]')).click()
                    esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/continue_button')).click()
                except Exception as e:
                    print(f"[verificarChip] Erro ao pedir SMS: {e}")
                try:
                    esperar_elemento_visivel(self.driver, (By.ID,
                                                           'com.android.permissioncontroller:id/permission_allow_button')).click()
                    esperar_elemento_visivel(self.driver, (By.ID,
                                                           'com.android.permissioncontroller:id/permission_allow_button')).click()
                except Exception as e:

                    print(f"[verificarChip] Erro ao aceitar condições: Não verificou o Chip")

        except Exception as e:
            print(f"[verificarChip] Erro: Não verificou o Chip")

            return False

    def abrirAppMensagens(self):
        try:
            campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
            self.driver.activate_app('com.samsung.android.messaging')
            print('abriu o app')
            return True
        except Exception as e:
            print(f"[abrirAppMensagens] Erro: Não Abriu o App De Mensagem ")
            return False

    def pegarCodigoSms(self):
        try:
            achou, elemento = esperar_elemento_scroll(self.driver, (AppiumBy.XPATH, "//android.widget.TextView[contains(@text, 'Codigo do WhatsApp')]"))
            elemento.click()
            mensagens = esperar_elementos_xpath(self.driver, '//android.widget.TextView[contains(@text, "Codigo do WhatsApp")]')
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

    def enviar_dados_para_api(self, udid):
        try:
            numero = self.pegarNumeroChip1(udid)

            if numero:
                enviar_para_api(numero)
                print(f"Dados enviados: Número: {numero}")
                return True
            else:
                print("Erro ao capturar número ou código.")
                return False
        except Exception as e:
            print(f"[enviar_dados_para_api] Erro: {e}")
            return False

    def voltarWhatsapp(self):
        try:
            self.driver.activate_app("com.whatsapp")
            campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
            print('voltou')
            return True
        except Exception as e:
            print(f"[voltarWhatsapp] Erro: {e}")
            return False

    def inserir_codigo_sms(self, codigo):
        try:
            esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input")).send_keys(codigo)
            print('colocou o codigo')
            return True
        except:
            print(f"[inserir_codigo_sms] Não inseriu o codigo")
            return False

    def concluir_perfil(self):
        try:
            esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/submit")).click()
            print('clicou em aceitou')
            try:
                permissao = verificar_elemento_visivel(self.driver, (By.ID,
                                                                     'com.android.permissioncontroller:id/permission_allow_button'))
                if permissao:
                    esperar_elemento_visivel(self.driver,
                                             (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                    time.sleep(1)
                    esperar_elemento_visivel(self.driver,
                                             (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                    time.sleep(1)
                    esperar_elemento_visivel(self.driver,
                                             (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                print('aceitou as permissoes')
            except Exception as e:
                print(f"[concluir_perfil] Erro ao aceitar notificações: {e}")
            return True
        except Exception as e:

            print(f"[concluir_perfil] Erro: Erro ao Concluir perfil")

            return False

    def aceitarPermissao(self):
        try:
            esperar_elemento_visivel(self.driver, (By.ID, "android:id/button2")).click()
            print('negou o backup')
            return True
        except:
            print(f"[aceitarPermissao] Erro: Não Negou o Backup")
            return False

    def colocarNome(self):
        try:
            campo_nome = (esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/registration_name")))
            if campo_nome.text != "Call Center":
                campo_nome.clear()
                campo_nome.send_keys("Call Center")
                print("colocou o nome")
                return True
            else:
                return True
        except:
            print(f"[colocarNome] Erro: Não Colocou o Nome")
            return False

    def finalizarPerfil(self):
        try:
            self.driver.find_element(By.ID, "com.whatsapp:id/register_name_accept").click()
            if elemento_esta_visivel(self.driver, (By.ID, 'com.whatsapp:id/secondary_button')):
                verificar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/secondary_button')).click()
            print('concluiu')
            return True
        except Exception as e:
            print(f"[finalizarPerfil] Erro: Não Finalizou o Perfil")
            return False

    def salvar(self, numero):
        try:
            campos = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            campos[0].send_keys('Call Center')
            campos[1].send_keys(numero)
        except:
            pass

'''            nome = esperar_elemento_visivel(self.driver, (By.ID, 'com.samsung.android.app.contacts:id/nameEdit'))
            nome.send_keys(f"Call Center: {numero}")
            telefone = esperar_elemento_visivel(self.driver, (By.XPATH, '(//android.widget.EditText[@resource-id="com.samsung.android.app.contacts:id/forCursorEdit"])[1]'))
            telefone.send_keys(numero)
            salvar = esperar_elemento_visivel(self.driver, (By.ID, 'com.samsung.android.app.contacts:id/menu_done'))
            salvar.click()
            self.driver.terminate_app("com.samsung.android.app.contacts")'''
