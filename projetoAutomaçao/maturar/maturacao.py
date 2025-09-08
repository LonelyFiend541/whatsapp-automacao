import asyncio
import itertools
import random
import keyboard
from banco.dbo import carregar_agentes_async_do_banco_async
from integration.IA import conversar_async, get_ia_response_ollama, get_ia_response_gemini
from integration.api_GTI import atualizar_status_parallel


# ===========================
# Funções auxiliares
# ===========================
async def carregar_agentes():
    agentes = await carregar_agentes_async_do_banco_async()
    return agentes

async def verificar_agentes(agentes):
    agentes_conectados = [ag for ag in agentes if ag.conectado]
    print(f"Agentes conectados: {len(agentes_conectados)}")
    return agentes_conectados

async def criar_pares(agentes_conectados, pares_atuais=set()):
    pares_agentes = [tuple(par) for par in itertools.batched(agentes_conectados, 2) if len(par) == 2]
    # filtra apenas os pares novos
    novos_pares = [par for par in pares_agentes if par not in pares_atuais]
    print(f"Novos pares de agentes detectados: {len(novos_pares)}")
    return novos_pares

# ===========================
# Função principal
# ===========================
async def main():
    sem = asyncio.Semaphore(20)
    tarefas = []
    pares_em_execucao = set()

    agentes = await carregar_agentes()
    agentes_conectados = await verificar_agentes(agentes)
    novos_pares = await criar_pares(agentes_conectados, pares_em_execucao)

    # Criar tarefas iniciais
    for par in novos_pares:
        async def conversar_com_limite(a1, a2):
            async with sem:
                try:
                    await conversar_async(a1, a2, 2, False, get_ia_response_ollama)
                except Exception:
                    await conversar_async(a1, a2, 2, False, get_ia_response_gemini)
        tarefa = asyncio.create_task(conversar_com_limite(par[0], par[1]))
        tarefas.append(tarefa)
        pares_em_execucao.add(par)

    print("Pressione 'r' para atualizar agentes ou 'q' para parada emergencial...")

    # Loop de monitoramento das teclas
    async def monitorar_teclas():
        nonlocal tarefas, pares_em_execucao
        while True:
            await asyncio.sleep(0.2)
            if keyboard.is_pressed('r'):
                print("verificando novos agentes")
                atualizar_status_parallel(agentes)
                agentes_conectados = await verificar_agentes(agentes)
                novos_pares = await criar_pares(agentes_conectados, pares_em_execucao)
                for par in novos_pares:
                    async def conversar_com_limite(a1, a2):
                        async with sem:
                            try:
                                await conversar_async(a1, a2, 5, True, get_ia_response_ollama)
                            except Exception:
                                await conversar_async(a1, a2, 5, True, get_ia_response_gemini)
                    tarefa = asyncio.create_task(conversar_com_limite(par[0], par[1]))
                    tarefas.append(tarefa)
                    pares_em_execucao.add(par)
            if keyboard.is_pressed("q"):
                print("\n⏹ Parada emergencial detectada! Cancelando todas as conversas...")
                for t in tarefas:
                    t.cancel()
                break

        print("Encerrando monitoramento de teclas...")
        return True
    # Executa tarefas + monitoramento de teclas
    await asyncio.gather(*tarefas, monitorar_teclas(), return_exceptions=True)

# ===========================
# Rodar script
# ===========================
if __name__ == "__main__":
    asyncio.run(main())
