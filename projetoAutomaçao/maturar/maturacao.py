import itertools
from banco.dbo import carregar_agentes_do_banco, DB
from integration.IA import conversar


agentes = carregar_agentes_do_banco(DB)
agentes_conectados = []
agentes_desconectados = []
for agente in agentes:
    if agente.conectado:
        agentes_conectados.append(agente)
    else:
        agentes_desconectados.append(agente)

pares_agentes = itertools.batched(agentes_conectados, 2)
for par in pares_agentes:
    try:
        conversar(par[0], par[1])
    except Exception as ex:
        print(ex)
        pass

