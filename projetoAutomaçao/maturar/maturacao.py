from integration.IA import *
from integration.api_GTI import agentes_gti, carregar_agentes_do_env, agentes_conectados

agentes_gti = carregar_agentes_do_env()

agentes_dict = {agentes_gti.nome: agentes_gti for agentes_gti in agentes_gti}

print(agentes_dict["agente 2806"].conectado )
print(agentes_dict["agente 2807"].conectado)



