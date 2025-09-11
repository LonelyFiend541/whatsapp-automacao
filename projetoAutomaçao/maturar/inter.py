import threading
import asyncio
import tkinter as tk
from tkinter import ttk
from banco.dbo import carregar_novos_agentes, DB
from maturar.maturacao import main
import re


# === Funções auxiliares ===
def extrair_numero(nome):
    match = re.search(r'\d+', nome)
    return int(match.group()) if match else 0


def log(msg, tipo="info"):
    cores = {"info": "white", "sucesso": "#27ae60", "erro": "#e74c3c", "alerta": "#f39c12"}
    log_text.insert("end", f"{msg}\n", tipo)
    log_text.tag_config(tipo, foreground=cores.get(tipo, "white"))
    log_text.see("end")


def cor_status(conectado):
    return "#27ae60" if conectado else "#c0392b"


def atualizar_status_async():
    def task():
        for ag in agentes:
            ag.atualizar_status()
        for ag in agentes:
            if ag.nome in botao_agentes:
                botao = botao_agentes[ag.nome]
                botao.config(
                    text=f"{ag.nome}\n{ag.numero or 'Sem número'}",
                    bg=cor_status(ag.conectado)
                )
        log("🔄 Status atualizado.", "sucesso")

    threading.Thread(target=task, daemon=True).start()


def rodar_maturacao():
    def task():
        log("🚀 Iniciando processo de maturação...", "info")
        asyncio.run(main())
        log("✅ Maturação finalizada.", "sucesso")

    threading.Thread(target=task, daemon=True).start()


# === Janela principal ===
janela = tk.Tk()
janela.title("📊 Central de Recadastro")
janela.geometry("1200x800")
janela.minsize(1000, 700)
janela.configure(bg="#f5f6fa")
janela.grid_rowconfigure(0, weight=1)
janela.grid_columnconfigure(1, weight=1)

# === Sidebar ===
sidebar = tk.Frame(janela, bg="white", width=220)
sidebar.grid(row=0, column=0, rowspan=2, sticky="ns")
sidebar.grid_propagate(False)

logo = tk.Label(sidebar, text="📱 Logotype", font=("Helvetica", 16, "bold"),
                bg="white", fg="#3498db")
logo.pack(pady=20)

menu_items = ["📂 Desbloqueio", "📊 Statistics", "🎞 Instancias",
              "📋 Maturacao", "📑 Numeros", "⚙ Settings"]
for item in menu_items:
    btn = tk.Button(sidebar, text=item, anchor="w", relief="flat",
                    bg="white", fg="#2c3e50",
                    font=("Helvetica", 12), padx=20, pady=10,
                    activebackground="#3498db", activeforeground="white",
                    borderwidth=0)
    btn.pack(fill="x", pady=2)

user_frame = tk.Frame(sidebar, bg="white")
user_frame.pack(side="bottom", pady=20)
tk.Label(user_frame, text="👤", font=("Helvetica", 18), bg="white").pack(side="left", padx=5)
tk.Label(user_frame, text="User Name", bg="white", fg="#2c3e50",
         font=("Helvetica", 12)).pack(side="left")

# === Conteúdo principal ===
content = tk.Frame(janela, bg="#f5f6fa")
content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
content.grid_rowconfigure(2, weight=1)  # Lista de agentes expande
content.grid_columnconfigure(0, weight=1)
content.grid_columnconfigure(1, weight=1)

# Header
header = tk.Frame(content, bg="#f5f6fa")
header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)
tk.Label(header, text="Dashboard", font=("Helvetica", 20, "bold"),
         bg="#f5f6fa", fg="#2c3e50").pack(side="left")
search_entry = ttk.Entry(header)
search_entry.pack(side="right", padx=10)

# === Cards à esquerda e Botões à direita ===
top_frame = tk.Frame(content, bg="#f5f6fa")
top_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=10)
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(1, weight=1)

# Cards
cards_frame = tk.Frame(top_frame, bg="#f5f6fa")
cards_frame.grid(row=0, column=0, sticky="w", padx=10)


def criar_card(master, titulo, valor, cor="#3498db"):
    card = tk.Frame(master, bg="white", width=200, height=100, highlightthickness=1, highlightbackground="#dcdde1")
    card.pack(side="left", padx=10, pady=5)
    card.pack_propagate(False)
    tk.Label(card, text=titulo, font=("Helvetica", 12), fg="#7f8c8d", bg="white").pack(anchor="w", padx=10, pady=5)
    tk.Label(card, text=valor, font=("Helvetica", 18, "bold"), fg=cor, bg="white").pack(anchor="w", padx=10)
    return card


# Botões
btns_frame = tk.Frame(top_frame, bg="#f5f6fa")
btns_frame.grid(row=0, column=1, sticky="e", padx=10)
btn_maturacao = tk.Button(btns_frame, text="▶️ Iniciar Maturação", fg="white", bg="#2980b9",
                          font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=8,
                          command=rodar_maturacao)
btn_maturacao.pack(side="left", padx=5)

btn_parar = tk.Button(btns_frame, text="⏹ Parar", fg="white", bg="#e74c3c",
                      font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=8,
                      command=lambda: log("⛔ Parada solicitada.", "alerta"))
btn_parar.pack(side="left", padx=5)

btn_atualizar = tk.Button(btns_frame, text="🔄 Atualizar Status", fg="white", bg="#f39c12",
                          font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=8,
                          command=atualizar_status_async)
btn_atualizar.pack(side="left", padx=5)

# Carrega agentes
agentes = carregar_novos_agentes(DB)
botao_agentes = {}
ag_ativos = [a for a in agentes if a.conectado]
ag_inativos = [a for a in agentes if not a.conectado]

criar_card(cards_frame, "Ativos", f"{len(ag_ativos)}", "#27ae60")
criar_card(cards_frame, "Pendentes", f"{len(ag_inativos)}", "#f39c12")
criar_card(cards_frame, "Erros", "2", "#c0392b")

# === Lista de agentes (2 por linha) ===
frame_agentes = tk.Frame(content, bg="white")
frame_agentes.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
frame_agentes.grid_rowconfigure(0, weight=1)
frame_agentes.grid_columnconfigure(0, weight=1)
frame_agentes.grid_columnconfigure(1, weight=1)

canvas = tk.Canvas(frame_agentes, bg="white", highlightthickness=0)
scrollbar = ttk.Scrollbar(frame_agentes, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="white")

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

celular_count = 1
linha = 0
agentes.sort(key=lambda x: extrair_numero(x.nome))

for i in range(0, len(agentes), 2):
    label = tk.Label(scrollable_frame, text=f"📱 Celular {celular_count}",
                     font=("Helvetica", 12, "bold"), bg="#ecf0f1",
                     anchor="w", padx=10)
    label.grid(row=linha, column=2, columnspan=2, pady=(10, 5), sticky="ew")
    linha += 1


    for j in range(2):  # 2 agentes por linha
        if i + j < len(agentes):
            ag = agentes[i + j]
            frame_ag = tk.Frame(scrollable_frame, bg="white", highlightthickness=1,
                                highlightbackground="#dcdde1", padx=5, pady=5)
            frame_ag.grid(row=linha, column=j, padx=10, pady=5, sticky="nsew")

            # Status do agente
            status = tk.Canvas(frame_ag, width=15, height=15, bg="white", highlightthickness=0)
            status.create_oval(2, 2, 13, 13, fill=cor_status(ag.conectado))
            status.pack(side="top", pady=5)

            # Botão do agente
            btn = tk.Button(frame_ag, text=f"{ag.nome}\n{ag.numero or 'Sem número'}",
                            bg=cor_status(ag.conectado), fg="white",
                            font=("Helvetica", 10, "bold"), relief="raised", width=18, height=4,
                            command=lambda a=ag: threading.Thread(
                                target=lambda: (a.gerar_qr(), log(f"📲 QR gerado para {a.nome}", "sucesso")),
                                daemon=True
                            ).start())
            btn.pack(expand=True, fill="both")
            botao_agentes[ag.nome] = btn
    linha += 1
    celular_count += 1

# === Log na parte inferior, full width ===
frame_log = tk.Frame(content, bg="white")
frame_log.grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)
frame_log.grid_columnconfigure(0, weight=1)

log_text = tk.Text(frame_log, bg="#2c3e50", fg="white", wrap="word", relief="flat", height=6)
log_text.grid(row=0, column=0, sticky="ew")

scroll_log = ttk.Scrollbar(frame_log, orient="vertical", command=log_text.yview)
scroll_log.grid(row=0, column=1, sticky="ns")
log_text.configure(yscrollcommand=scroll_log.set)

janela.mainloop()
