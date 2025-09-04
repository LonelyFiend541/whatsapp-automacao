import asyncio
import itertools
import random

from banco.dbo import (
    carregar_agentes_do_banco,
    DB,
    carregar_agentes_do_banco_async,
    carregar_agentes_async_do_banco_async
)
from integration.IA import conversar_async


# ===========================
# Funções auxiliares
# ===========================

async def delay_ms_async(base=0.1):
    """Delay com jitter para evitar congestionamento"""
    await asyncio.sleep(base + random.random() * 0.2)





# ===========================
# Função principal
# ===========================

async def main():
    # Carregar agentes do banco
    agentes = await carregar_agentes_async_do_banco_async()
    agentes_conectados = []
    for agente in agentes:
        if agente.conectado and (agente.nome == "WD_24" or agente.nome == "WB_38"):
            agentes_conectados.append(agente)
    print(f"Agentes conectados: {len(agentes_conectados)}")

    # Criar pares
    pares_agentes = [par for par in itertools.batched(agentes_conectados, 2) if len(par) == 2]
    print(f"Pares de agentes criados: {len(pares_agentes)}")

    # Controle de concorrência (máx 20 conversas simultâneas)
    sem = asyncio.Semaphore(20)

    async def conversar_com_limite(ag1, ag2):
        async with sem:
            await conversar_async(ag1, ag2)

    # Criar tarefas
    tarefas = [conversar_com_limite(par[0], par[1]) for par in pares_agentes]

    if tarefas:
        await asyncio.gather(*tarefas)
    else:
        print("⚠️ Nenhum par disponível para conversar.")


# ===========================
# Rodar script
# ===========================
if __name__ == "__main__":
    asyncio.run(main())
