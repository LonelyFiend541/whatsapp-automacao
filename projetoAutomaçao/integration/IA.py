import time
from concurrent.futures import ThreadPoolExecutor
from integration.api import agentes
import ollama

executor = ThreadPoolExecutor(max_workers=2)

def get_ia_response(user_message, historico, prompt_extra=""):
    if not user_message:
        return "🤔 Opa, não entendi sua mensagem."

    # Adiciona mensagem do usuário ao histórico
    historico.append({"role": "user", "content": user_message})

    # Monta mensagens para o modelo
    mensagens = [
        {
            "role": "system",
            "content": (
                "Você é um amigo virtual que conversa pelo WhatsApp de forma natural e descontraída.\n"
                "Responda de forma curta, casual, com gírias e emojis, e lembre das mensagens anteriores."
            )
        }
    ]

    if prompt_extra:
        mensagens.append({"role": "system", "content": prompt_extra})

    # Limita histórico e gera resumo se necessário
    if len(historico) > 5:
        resumo = " ".join([m["content"] for m in historico[:-3]])
        mensagens.append({"role": "system", "content": f"Resumo da conversa anterior: {resumo}"})

    mensagens.extend(historico[-3:])  # Mantém apenas últimas 3 mensagens completas

    try:
        response = ollama.chat(model="codellama", messages=mensagens)
        resposta_texto = response["message"]["content"].strip()

        # Limita a resposta a 60 caracteres
        if len(resposta_texto) > 60:
            resposta_texto = resposta_texto[:57] + "…"

        historico.append({"role": "assistant", "content": resposta_texto})
        return resposta_texto

    except Exception as e:
        print(f"⚠️ Erro ao gerar resposta com Ollama: {e}")
        return "⚠️ Deu ruim aqui, não consegui pensar em nada 😅"


def enviar_mensagem_assincrona(agente, numero, mensagem):
    """Envia mensagens sem travar o loop principal"""
    executor.submit(agente.enviar_mensagem, numero, mensagem)


def conversar():
    historico = []
    print("🤖 IA: Fala! Manda aí o que tá pegando (digite 'sair' pra encerrar).")
    msg = input("Você: ")

    while True:
        if msg.lower() in ["sair", "exit", "quit"]:
            print("🤖 IA: Valeu, até a próxima! 👋")
            break

        # Gera resposta da IA
        resposta = get_ia_response(msg, historico, "de maneira resumida mas continuando a conversa de forma natural ")

        # Envia mensagens assíncronas para os agentes
        enviar_mensagem_assincrona(agentes[8], agentes[9].numero, msg)
        print(f"🤖 IA-8: {msg}")
        enviar_mensagem_assincrona(agentes[9], agentes[8].numero, resposta)
        print(f"🤖 IA-9: {resposta}")
        msg = get_ia_response(resposta, historico)


if __name__ == "__main__":
    conversar()
