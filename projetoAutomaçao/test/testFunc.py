from drivers.drivers_factory import criar_driver
from pages.whatsapp_page import WhatsAppPage
from drivers.drivers_factory import *
import sys

appium_server()
udid = pegar_udid()
driver = criar_driver(4723, udid[0])

