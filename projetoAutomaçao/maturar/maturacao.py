import asyncio
import itertools
import random
import keyboard
from banco.dbo import carregar_agentes_async_do_banco_async, carregar_novos_agentes, DB
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

import itertools
import re

# função auxiliar para extrair o número do nome
def extrair_numero(nome):
    m = re.search(r'\d+', nome)
    return int(m.group()) if m else 0

async def criar_pares(agentes_conectados, pares_atuais=set()):
    # Ordena pelos números do nome
    agentes_ordenados = sorted(agentes_conectados, key=lambda a: extrair_numero(a.nome))

    # Agrupa em pares sequenciais completos
    pares_agentes = [(agentes_ordenados[i], agentes_ordenados[i+1])
                     for i in range(0, len(agentes_ordenados)-1, 2)]

    # Filtra apenas pares novos usando ids
    novos_pares = []
    for a1, a2 in pares_agentes:
        chave = (id(a1), id(a2))
        if chave not in pares_atuais:
            novos_pares.append((a1, a2))
            pares_atuais.add(chave)  # marca como em execução

    print(f"Novos pares de agentes detectados: {len(novos_pares)}")
    return novos_pares


# ===========================
# Função principal
# ===========================
# ===========================
# Função principal ajustada
# ===========================
async def main():
    sem = asyncio.Semaphore(20)  # limite de tarefas concorrentes
    tarefas = []
    pares_em_execucao = set()
    turno = 100  # número de turnos

    # Carrega agentes do banco
    agentes = carregar_novos_agentes(DB)
    agentes_conectados = await verificar_agentes(agentes)

    # Cria pares ordenados sequencialmente
    async def criar_pares_ordenados():
        # Ordena pelos números no nome
        agentes_ordenados = sorted(agentes_conectados, key=lambda a: extrair_numero(a.nome))
        pares_agentes = [(agentes_ordenados[i], agentes_ordenados[i + 1])
                         for i in range(0, len(agentes_ordenados) - 1, 2)]
        # Filtra apenas pares novos
        novos = [par for par in pares_agentes if par not in pares_em_execucao]
        return novos

    novos_pares = await criar_pares_ordenados()

    # Função para iniciar conversa entre um par
    async def conversar_com_limite(a1, a2, turno, sem):
        async with sem:
            try:
                await conversar_async(a1, a2, turno, False, get_ia_response_ollama)
            except Exception:
                await conversar_async(a1, a2, turno, False, get_ia_response_ollama)

    # Criar tarefas iniciais
    for par in novos_pares:
        tarefa = asyncio.create_task(conversar_com_limite(par[0], par[1], turno, sem))
        tarefas.append(tarefa)
        pares_em_execucao.add(par)

    print("Pressione 'r' para atualizar agentes ou 'q' para parada emergencial...")

    # Monitoramento de teclas
    async def monitorar_teclas():
        nonlocal tarefas, pares_em_execucao
        while True:
            await asyncio.sleep(0.2)
            if keyboard.is_pressed('r'):
                print("🔄 Atualizando status dos agentes...")
                await atualizar_status_parallel(agentes)
                agentes_conectados = await verificar_agentes(agentes)
                novos_pares = await criar_pares_ordenados()
                for par in novos_pares:
                    tarefa = asyncio.create_task(conversar_com_limite(par[0], par[1], turno, sem))
                    tarefas.append(tarefa)
                    pares_em_execucao.add(par)

            if keyboard.is_pressed('q'):
                print("deveria parar mas desabilitei a opcao")  #print("\n⏹ Parada emergencial detectada! Cancelando todas as conversas...")
                for t in tarefas:
                    print("nao vai parar")
                    #t.cancel()
                break
        print("Encerrando monitoramento de teclas...")

    # Executa todas as tarefas + monitoramento
    await asyncio.gather(*tarefas, monitorar_teclas(), return_exceptions=True)

# ===========================
# Rodar script
# ===========================
if __name__ == "__main__":
    asyncio.run(main())
