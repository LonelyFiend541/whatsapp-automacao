import unittest
from drivers.drivers_factory import criar_driver, pegar_udid
from pages.whatsapp_page import WhatsAppPage, ChipBanidoException, ChipEmAnaliseException



class TestWhatsAppRegistro(unittest.TestCase):


    def test_registrar_novo_numero(self):
        try:
            udid = pegar_udid()
            driver = criar_driver(4723, udid[0])

            whatsapp = WhatsAppPage(driver)

            numero = whatsapp.pegarNumero(udid)
            whatsapp.abrirWhatsapp()
            whatsapp.selecionar_linguagem()
            whatsapp.clicar_prosseguir()
            whatsapp.inserir_numero(numero)
            whatsapp.confirmarNumero()
            whatsapp.verificarAnalise()
            whatsapp.verificarChip()
            whatsapp.abrirAppMensagens()
            codigo = whatsapp.pegarCodigoSms()
            whatsapp.voltarWhatsapp()
            whatsapp.inserir_codigo_sms(codigo)
            whatsapp.concluir_perfil()
            whatsapp.aceitarPermissao()
            whatsapp.colocarNome()
            whatsapp.finalizarPerfil()




        except ChipBanidoException as e:
            print(f"⚠️ Teste encerrado: {e}")
            self.skipTest("Número banido – teste ignorado.")

        except ChipEmAnaliseException as e:
            print(f"⚠️ Teste encerrado: {e}")
            self.skipTest("Número em análise – teste ignorado.")

        except Exception as e:

            self.fail(f"❌ Erro inesperado: {e}")

        finally:
            driver.quit()

    if __name__ == '__main__':
        unittest.main()

