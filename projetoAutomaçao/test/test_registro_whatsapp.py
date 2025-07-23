from drivers.drivers_factory import criar_driver
from pages.whatsapp_page import WhatsAppPage





def test_registrar_novo_numero():

    driver = criar_driver(4723, "R9QN905LRDK")

    whatsapp = WhatsAppPage(driver)

    #whatsapp.pegarNumero()
    numero = whatsapp.pegarNumero()
    whatsapp.abrirWhatsapp()
    whatsapp.selecionar_linguagem()
    whatsapp.clicar_prosseguir()
    whatsapp.inserir_numero(numero)
    whatsapp.verificarAnal()
    whatsapp.abrirAppMensagens()
    whatsapp.pegarCodigoSms()
    codigo = whatsapp.pegarCodigoSms()
    whatsapp.voltarWhatsapp()
    whatsapp.inserir_codigo_sms(codigo)
    whatsapp.concluir_perfil()



    # AQUI você colocaria o código automático recebido por SMS


    #driver.quit()
