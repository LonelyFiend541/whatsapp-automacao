import time
import ollama
from concurrent.futures import ThreadPoolExecutor, as_completed
executor = ThreadPoolExecutor(max_workers=5)


def enviar_mensagem_async(agente, numero, mensagem):
    """Envia mensagem de forma assíncrona"""
    future = executor.submit(enviar_mensagem_segura, agente, numero, mensagem)
    return future

def conversar_automatica_parallel(agente1, agente2, max_turnos=10):
    historico = []

    print("🤖 IA: Fala! Manda aí o que tá pegando (digite 'sair' pra encerrar).")
    user_msg = input("Você: ")

    if user_msg.lower() in ["sair", "exit", "quit"]:
        print("🤖 IA: Valeu, até a próxima! 👋")
        return

    # Primeiro envio do usuário
    future1 = enviar_mensagem_async(agente1, agente2.numero, user_msg)
    historico.append({"role": "user", "content": user_msg})
    turno = 0

    while turno < max_turnos:
        # Gera resposta do agente2 enquanto envia mensagem do agente1
        resposta_agente2 = get_ia_response(user_msg, historico, "Responda curto e natural, como WhatsApp.")

        # Envia resposta do agente2 e já envia automaticamente a resposta do agente1 em paralelo
        future2 = enviar_mensagem_async(agente2, agente1.numero, resposta_agente2)
        print(f"{agente2.nome}: {resposta_agente2}")
        historico.append({"role": "assistant", "content": resposta_agente2})

        resposta_agente1 = get_ia_response(resposta_agente2, historico, "Continue a conversa, <=120 caracteres")
        future1 = enviar_mensagem_async(agente1, agente2.numero, resposta_agente1)
        print(f"{agente1.nome}: {resposta_agente1}")
        historico.append({"role": "user", "content": resposta_agente1})

        # Aguarda envio do turno anterior
        for f in [future1, future2]:
            try:
                f.result(timeout=5)
            except Exception as e:
                print(f"⚠️ Erro no envio paralelo: {e}")

        user_msg = resposta_agente1
        turno += 1

    print("🤖 Conversa automática encerrada.")


def get_ia_response(user_message, historico=None, prompt_extra=""):
    if not user_message:
        return "🤔 Opa, não entendi sua mensagem."

    if historico is None:
        historico = []

    historico.append({"role": "user", "content": user_message})

    mensagens = [
        {
            "role": "system",
            "content": (
                "Você é um amigo virtual que conversa pelo WhatsApp de forma natural e descontraída.\n"
                "Responda de forma curta, casual, com gírias e emojis, lembrando do contexto da conversa."
            )
        }
    ]

    if prompt_extra:
        mensagens.append({"role": "system", "content": prompt_extra})

    if len(historico) > 6:
        resumo = " ".join([m["content"] for m in historico[:-3]])
        mensagens.append({
            "role": "system",
            "content": f"Resumo rápido da conversa até agora: {resumo[:200]}..."
        })

    mensagens.extend(historico[-3:])

    try:
        response = ollama.chat(model="llama3.2:1b", messages=mensagens)
        resposta_texto = response["message"]["content"].strip()
        historico.append({"role": "assistant", "content": resposta_texto})
        return resposta_texto
    except Exception as e:
        print(f"⚠️ Erro ao gerar resposta com Ollama: {e}")
        return "⚠️ Deu ruim aqui, não consegui pensar em nada 😅"




def enviar_mensagem_segura(agente, numero, mensagem):
    """Tenta enviar mensagem, reconectando se necessário"""
    if not agente.conectado:
        print(f"[{agente.nome}] Não está conectado. Tentando gerar QR e reconectar...")
        agente.gerar_qr(modo="img")
        agente.atualizar_status()
        if not agente.conectado:
            print(f"[{agente.nome}] Falha ao conectar. Mensagem não enviada.")
            return None

    return agente.enviar_mensagem(numero, mensagem)

def conversar(agente1, agente2):
    historico = []
    print("🤖 IA: Fala! Manda aí o que tá pegando (digite 'sair' pra encerrar).")
    msg = input(f"{agente1.numero}: ")
    time.sleep(5)
    while True:
        if msg.lower() in ["sair", "exit", "quit"]:
            print("🤖 IA: Valeu, até a próxima! 👋")
            break

        ag1 = enviar_mensagem_segura(agente1, agente2.numero, msg)
        if not ag1:
            print(f"Erro ao enviar mensagem.\n numero em analise: {agente1.numero}.")
            break
        historico.append(msg)
        time.sleep(5)
        print(f"{agente1.numero}: {msg}.")
        # Gera a resposta primeiro
        resposta = get_ia_response(msg, historico, "Responda curto e natural, como no WhatsApp.")

        # Envia a mensagem
        ag2 = enviar_mensagem_segura(agente2, agente1.numero, resposta)
        if not ag2:
            print(f"Erro ao enviar mensagem.\n numero em analise: {agente2.numero}.")
            break
        historico.append(resposta)
        print(f"🤖{agente2.numero}: {resposta}")
        time.sleep(5)

        # Atualiza a próxima mensagem (simulação de conversa contínua)
        msg = get_ia_response(resposta, historico, "Continue a conversa, <=120 caracteres")








if __name__ == "__main__":
    msg = "ola"
    ia = get_ia_response(msg, None, "Responda curto e natural, como WhatsApp.")
    print(ia)