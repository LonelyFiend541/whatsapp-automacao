import time
import re
import subprocess


from re import match
from unittest import expectedFailure

from selenium.webdriver.common.by import  By

from until.waits import esperar_elemento_visivel, verificar_elemento_visivel


class WebDriverException:
    pass


class WhatsAppPage:


    def __init__(self, driver):
        self.driver = driver


    def pegarNumero(self):
        try:
            self.driver.press_keycode(3)
            #esperar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[@content-desc="Telefone"]'))
            self.driver.activate_app('com.samsung.android.dialer')
            esperar_elemento_visivel(self.driver, (By.ID, "com.samsung.android.dialer:id/dialpad_spacer_view") ).click()

            subprocess.run('adb shell am start -a android.intent.action.CALL -d tel:*846%23', shell=True)
            esperar_elemento_visivel(self.driver, (By.XPATH, "//android.widget.TextView[contains(@text, 'Recarga Facil')]"))
            campoNumero = esperar_elemento_visivel(self.driver, (By.ID, "android:id/message"))
            numeros = campoNumero.text
            print(numeros)
            numeros = re.findall(r"\[(\d+)\]", campoNumero.text)
            esperar_elemento_visivel(self.driver, (By.ID, 'android:id/button1')).click()
            numero = int(numeros[0])
            print(numero)
            self.driver.terminate_app("com.samsung.android.dialer")
            return numero

        except:
            pass

    def abrirWhatsapp(self):
        time.sleep(2)
        self.driver.activate_app('com.whatsapp')



    def selecionar_linguagem(self):
        esperar_elemento_visivel(self.driver, (By.XPATH,'//android.widget.CheckBox[@content-desc="Selecionar (idioma do dispositivo) como idioma do app"]')).click()

    def clicar_prosseguir(self):
        esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/eula_accept')).click()

    def inserir_numero(self, numero):
        #notificacao = esperar_elemento_visivel(self.driver, (By.ID, "com.android.permissioncontroller:id/permission_allow_button"))
        #notificacao.click()

        campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/registration_phone"))
        campo.send_keys(numero)

        dd = self.driver.find_element(By.ID, 'com.whatsapp:id/registration_cc')
        dd.send_keys('55')

        botao = self.driver.find_element(By.ID, "com.whatsapp:id/registration_submit")
        botao.click()

        confirmar = esperar_elemento_visivel(self.driver, (By.ID, "android:id/button1"))
        confirmar.click()
        time.sleep(0.5)




        try:
            elements = verificar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/submit'))

            if elements:
                self.concluir_perfil()


        except TimeoutException:
            print(f"[TIMEOUT] Elemento {locator} não encontrado após {timeout}s.")

        except WebDriverException as e:
            print(f"[WEBDRIVER ERROR] Falha ao procurar {locator}. Erro: {e}")

            pass

        try:

            tipoDeRecebimento = verificar_elemento_visivel(self.driver,
                                                           (By.ID, 'com.whatsapp:id/entire_content_holder'))

            if tipoDeRecebimento:
                esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/secondary_button')).click()
                esperar_elemento_visivel(self.driver, (By.XPATH,
                                                       '(//android.widget.RadioButton[@resource-id="com.whatsapp:id/reg_method_checkbox"])[2]')).click()
                esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/continue_button')).click()

            def abrirAppMensagens(self):
                esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
                self.driver.activate_app('com.samsung.android.messaging')

            def pegarCodigoSms(self):
                # Localiza o elemento que contém a mensagem com o código de verificação
                esperar_elemento_visivel(self.driver, (By.XPATH,
                                                       '(//android.widget.LinearLayout[@resource-id="com.samsung.android.messaging:id/card_view_sub_layout"])[1]')).click()

                # Busca pela mensagem que contém o código de verificação
                esperar_elemento_visivel(self.driver, (By.XPATH,
                                                       "//android.widget.LinearLayout[contains(@content-desc, 'WhatsApp')]"))
                mensagens = self.driver.find_elements(By.XPATH,
                                                      "//android.widget.LinearLayout[contains(@content-desc, 'WhatsApp')]")
                # Se houver mensagens que correspondem ao critério

            if mensagens:
                # Pegue a última mensagem que contém "Código do WhatsApp"
                ultima_mensagem = mensagens[-1]

                # Extraímos o texto ou o content-desc dessa última mensagem
                codigoCompleto = ultima_mensagem.get_attribute('content-desc')

                padrao = r'(\d+)-(\d+)'

                resultado = re.search(padrao, codigoCompleto)

                codigo = resultado.group(1) + resultado.group(2)

                return codigo

            def voltarWhatsapp(self):
                self.driver.activate_app("com.whatsapp")
                campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
                campo.click()

            def inserir_codigo_sms(self, codigo):
                campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
                campo.send_keys(codigo)

            def concluir_perfil(self):
                esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/submit")).click()
                esperar_elemento_visivel(self.driver,
                                         (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                time.sleep(1)
                esperar_elemento_visivel(self.driver,
                                         (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                time.sleep(1)
                esperar_elemento_visivel(self.driver,
                                         (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                esperar_elemento_visivel(self.driver, (By.ID, "android:id/button2")).click()

                campo_nome = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/registration_name"))
                campo_nome.send_keys("Call Center")
                botao = self.driver.find_element(By.ID, "com.whatsapp:id/register_name_accept")
                botao.click()



        except TimeoutException:
            print(f"[TIMEOUT] Elemento {locator} não encontrado após {timeout}s.")
            pass
        except WebDriverException as e:
            print(f"[WEBDRIVER ERROR] Falha ao procurar {locator}. Erro: {e}")
            pass



    def verificarAnal(self):
        try:
            verificar_elemento_visivel(self.driver, (By.XPATH, '//android.widget.TextView[contains(@text="Esta conta não pode mais usar o WhatsApp por envio de spam"])'))
            esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/action_button')).click()
            esperar_elemento_visivel(self.driver, (By.ID, 'com.whatsapp:id/action_button')).click()

        except:
            pass






    def abrirAppMensagens(self):
        campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input"))
        self.driver.activate_app('com.samsung.android.messaging')

    def pegarCodigoSms(self) :
        # Localiza o elemento que contém a mensagem com o código de verificação
        esperar_elemento_visivel(self.driver, (By.XPATH, '(//android.widget.LinearLayout[@resource-id="com.samsung.android.messaging:id/card_view_sub_layout"])[1]')).click()

        # Busca pela mensagem que contém o código de verificação
        esperar_elemento_visivel(self.driver, (By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, 'WhatsApp')]"))
        mensagens = self.driver.find_elements(By.XPATH, "//android.widget.LinearLayout[contains(@content-desc, 'WhatsApp')]")
        # Se houver mensagens que correspondem ao critério
        if mensagens:
            # Pegue a última mensagem que contém "Código do WhatsApp"
            ultima_mensagem = mensagens[-1]

            # Extraímos o texto ou o content-desc dessa última mensagem
            codigoCompleto = ultima_mensagem.get_attribute('content-desc')

            padrao = r'(\d+)-(\d+)'

            resultado = re.search(padrao, codigoCompleto)

            codigo = resultado.group(1)+resultado.group(2)

            self.driver.terminate_app("com.samsung.android.messaging")

            return codigo

    def voltarWhatsapp(self):
        self.driver.activate_app("com.whatsapp")
        campo = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input")).click()




    def inserir_codigo_sms(self, codigo):
        esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/verify_sms_code_input")).send_keys(codigo)


    def concluir_perfil(self):
        esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/submit")).click()

        permissao =verificar_elemento_visivel(self.driver, (By.ID, 'com.android.permissioncontroller:id/permission_allow_button'))
        try:
            if permissao:
                esperar_elemento_visivel(self.driver, (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                time.sleep(1)
                esperar_elemento_visivel(self.driver, (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()
                time.sleep(1)
                esperar_elemento_visivel(self.driver, (By.ID, "com.android.permissioncontroller:id/permission_allow_button")).click()

        except:
            pass


        esperar_elemento_visivel(self.driver, (By.ID, "android:id/button2")).click()


        campo_nome = esperar_elemento_visivel(self.driver, (By.ID, "com.whatsapp:id/registration_name"))
        campo_nome.send_keys("Call Center")
        botao = self.driver.find_element(By.ID, "com.whatsapp:id/register_name_accept")
        botao.click()


