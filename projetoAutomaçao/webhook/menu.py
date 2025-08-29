from wsgiref.validate import check_status

import conectar_instancia
from conectar_instancia import *


def bt_verificar_instancia(inst):
    conectar_instancia.MonitorThread.check_status(inst)



bt_verificar_instancia(inst)