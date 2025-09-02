import itertools
from banco.dbo import carregar_agentes_do_banco, DB
from integration.IA import conversar

#GTI_2731 | Número: 5511984284121 | Conectado: True
#GTI_2736 | Número: 5511959069221 | Conectado: True
#GTI_2891 | Número: 5511959339638 | Conectado: True
#GTI_2927 | Número: 5513936191186 | Conectado: True

agentes = carregar_agentes_do_banco(DB)
#agentes = {'ag1', 'ag2', 'ag3', 'ag4', 'ag5', 'ag6', 'ag7', 'ag8', 'ag9', 'ag10'}
agentes_conectados = []
for agente in agentes:
    if agente.conectado and agente.nome == "GTI_2774" or agente.nome == "GTI_2789":
        agente.dados()
        agentes_conectados.append(agente)
pares_agentes = itertools.batched(agentes_conectados, 2)

for agentes in pares_agentes:
    try:
        conversar(agentes[0], agentes[1])
    except Exception as ex:
        print(ex)
        pass

'''def conversar(agente1, agente2):
    historico = []
    print("🤖 IA: Fala! Manda aí o que tá pegando (digite 'sair' pra encerrar).")
    msg = input("Você: ")
    enviar_mensagem_segura(agente1, agente2.numero, msg)
    time.sleep(5)
    while True:
         if msg.lower() in ["sair", "exit", "quit"]:
            print("🤖 IA: Valeu, até a próxima! 👋")
            break

        # Gera a resposta primeiro
        resposta = get_ia_response(msg, historico, "Responda curto e natural, como WhatsApp.")
        print(f"🤖 IA-9: {resposta}")

        # Envia a mensagem
        enviar_mensagem_segura(agente2, agente1.numero, resposta)
        time.sleep(5)

        # Atualiza a próxima mensagem (simulação de conversa contínua)
        msg = get_ia_response(resposta, historico, "Continue a conversa, <=120 caracteres")

        # Envia a mensagem do usuário simulada pelo agente
        enviar_mensagem_segura(agente1, agente2.numero, msg)
        print(f"🤖 IA-8: {msg}")
        time.sleep(5)'''