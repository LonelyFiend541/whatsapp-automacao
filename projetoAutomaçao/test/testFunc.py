from drivers.drivers_factory import criar_driver
from pages.whatsapp_page import WhatsAppPage
from drivers.drivers_factory import pegar_udid
import sys


udid = pegar_udid()
driver = criar_driver(4723, udid[0])

whatsapp = WhatsAppPage(driver)
whatsapp.verificarAnalise()
driver.quit()