import os
import random
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from google import genai
from google.genai import types
import ollama

# ==========================
# Configuração inicial
# ==========================
load_dotenv()
GENI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GENI_API_KEY)
executor = ThreadPoolExecutor(max_workers=20)

# ==========================
# Função delay assíncrono
# ==========================
async def delay_ms_async(test_mode=False):
    await asyncio.sleep(0.1 if test_mode else random.randint(60, 600))

# ==========================
# Função de envio assíncrono de mensagem
# ==========================
async def enviar_mensagem_async(agente, numero, mensagem):
    try:
        resultado = await agente.enviar_mensagem(numero, mensagem)
        return bool(resultado)
    except Exception as e:
        print(f"[{agente.nome}] Erro ao enviar mensagem async: {e}")
        return False

# ==========================
# Função para gerar resposta do Gemini
# ==========================
def get_ia_response_gemini(user_message, historico=None, prompt_extra=""):
    if not user_message:
        return "🤔 Não entendi sua mensagem."

    historico = historico or []

    # Resumo do histórico
    if len(historico) > 3:
        resumo = " ".join([m["content"] for m in historico[:-3]])
        historico = historico[-3:]
        historico.insert(0, {"role": "system", "content": f"Resumo: {resumo[:150]}..."})

    contexto = "\n".join([f"{m['role']}: {m['content']}" for m in historico])
    prompt = f"{prompt_extra}\n{contexto}\nuser: {user_message}\nassistant:"

    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # ou "gemini-2.5-flash"
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ Erro IA Gemini: {e}")
        return "⚠️ Deu ruim aqui 😅"

# ==========================
# Função para gerar resposta do Ollama
# ==========================
def get_ia_response_ollama(user_message, historico=None, prompt_extra=""):
    if not user_message:
        return "🤔 Não entendi sua mensagem."

    historico = historico or []
    if len(historico) > 3:
        resumo = " ".join([m["content"] for m in historico[:-3]])
        historico = historico[-3:]
        historico.insert(0, {"role": "system", "content": f"Resumo: {resumo[:150]}..."})

    mensagens = [{"role": "system", "content": (
        "Você é um amigo virtual que conversa no WhatsApp.\n"
        "Responda curto, casual, com gírias e emojis.\n"
        "Máx 60 caracteres.\n"
        "Considere o contexto e evite repetir."
    )}]
    if prompt_extra:
        mensagens.append({"role": "system", "content": prompt_extra})
    mensagens.extend(historico)
    mensagens.append({"role": "user", "content": user_message})

    try:
        response = ollama.chat(model="llama3.2:1b", messages=mensagens)
        return response.get("message", {}).get("content", "").strip() or "😅 Não consegui pensar em nada agora."
    except Exception as e:
        print(f"⚠️ Erro IA: {e}")
        return "⚠️ Deu ruim aqui 😅"

# ==========================
# Loop de conversa assíncrono
# ==========================
async def conversar_async(agente1, agente2, max_turnos=10, test_mode=False):
    historico = []
    print(f"🤖 Iniciando conversa entre {agente1.nome} e {agente2.nome}")

    msg = await asyncio.to_thread(get_ia_response_gemini, " ", historico, "Inicie uma conversa casual")
    count1, count2 = 0, 0

    for turno in range(max_turnos):
        # Agente 1 envia
        enviado = await enviar_mensagem_async(agente1, agente2.numero, msg)
        if not enviado:
            print(f"{agente1.nome} falhou no envio.")
            print(f"{agente1.nome}: enviou {count1} mensagens.")

            break
        historico.append({"role": "user", "content": msg})
        print(f"{agente1.nome}: {msg} → {agente2.nome}")
        count1 += 1
        await delay_ms_async(test_mode)

        # Agente 2 responde
        resposta = await asyncio.to_thread(get_ia_response_gemini, msg, historico, "Responda curto e natural")
        enviado = await enviar_mensagem_async(agente2, agente1.numero, resposta)
        if not enviado:
            print(f"{agente2.nome} falhou no envio.")
            print(f"{agente2.nome}: enviou {count2} mensagens.")
            break
        historico.append({"role": "assistant", "content": resposta})
        print(f"{agente2.nome}: {resposta} → {agente1.nome}")
        count2 += 1
        await delay_ms_async(test_mode)

        # Próxima rodada
        msg = await asyncio.to_thread(get_ia_response_gemini, resposta, historico, "Continue curto (<=120 caracteres)")
