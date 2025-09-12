import threading
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext
import re
import itertools
import aioodbc
from banco.dbo import carregar_novos_agentes, DB, carregar_agentes_do_banco, carregar_agentes_inter
from integration.api_GTI import atualizar_status_parallel
from maturar.maturacao import main

# ================= Funções auxiliares =================
def extrair_numero(nome):
    match = re.search(r'\d+', nome)
    return int(match.group()) if match else 0

def cor_status(conectado):
    return "#27ae60" if conectado else "#c0392b"

def log(text_widget, msg, tipo="info"):
    cores = {"info": "white", "sucesso": "#27ae60", "erro": "#e74c3c", "alerta": "#f39c12"}
    text_widget.insert("end", f"{msg}\n", tipo)
    text_widget.tag_config(tipo, foreground=cores.get(tipo, "white"))
    text_widget.see("end")

# ================= Placeholders funções externas =================
async def carregar_agentes_async_do_banco_async():
    # Aqui você pode colocar a versão async do carregar_agentes_do_banco
    return carregar_agentes_do_banco(DB)

async def conversar_async(a1, a2, quantidade, flag, get_ia_response):
    # Função simulada de conversação
    await asyncio.sleep(1)
    return f"{a1.nome} conversou com {a2.nome}"

async def get_ia_response_ollama(msg):
    return f"Resposta Ollama para: {msg}"

async def get_ia_response_gemini(msg):
    return f"Resposta Gemini para: {msg}"

# ================= Classe Principal =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("📊 Central de Recadastro")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg="#f5f6fa")

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg="white", width=220)
        self.sidebar.pack(side="left", fill="y")

        logo = tk.Label(self.sidebar, text="📱 Logotype", font=("Helvetica", 16, "bold"),
                        bg="white", fg="#3498db")
        logo.pack(pady=20)

        # Páginas
        self.pages = {}
        self.pages["dashboard"] = self.criar_dashboard()
        self.pages["maturacao"] = self.criar_maturacao()
        self.pages["instancias"] = self.criar_instancia()
        self.pages["settings"] = self.criar_settings()

        # Botões sidebar
        self.criar_botao("📊 Dashboard", "dashboard")
        self.criar_botao("📋 Maturação", "maturacao")
        self.criar_botao("Instâncias", "instancias")
        self.criar_botao("⚙ Configurações", "settings")

        # Rodapé
        user_frame = tk.Frame(self.sidebar, bg="white")
        user_frame.pack(side="bottom", pady=20)
        tk.Label(user_frame, text="👤", font=("Helvetica", 18), bg="white").pack(side="left", padx=5)
        tk.Label(user_frame, text="User Name", bg="white", fg="#2c3e50",
                 font=("Helvetica", 12)).pack(side="left")

        # Página inicial
        self.mostrar_pagina("dashboard")

    # ================= Controle de navegação =================
    def criar_botao(self, texto, pagina_key):
        btn = tk.Button(self.sidebar, text=texto, anchor="w", relief="flat",
                        bg="white", fg="#2c3e50",
                        font=("Helvetica", 12), padx=20, pady=10,
                        activebackground="#3498db", activeforeground="white",
                        command=lambda: self.mostrar_pagina(pagina_key))
        btn.pack(fill="x", pady=2)

    def mostrar_pagina(self, key):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)

    # ================= Página: Dashboard =================
    def criar_dashboard(self):
        frame = tk.Frame(self.root, bg="#f5f6fa")
        header = tk.Frame(frame, bg="#f5f6fa")
        header.pack(fill="x", pady=10)
        tk.Label(header, text="Dashboard", font=("Helvetica", 20, "bold"),
                 bg="#f5f6fa", fg="#2c3e50").pack(side="left")
        ttk.Entry(header).pack(side="right", padx=10)

        # Cards
        top_frame = tk.Frame(frame, bg="#f5f6fa")
        top_frame.pack(fill="x", pady=10)
        cards_frame = tk.Frame(top_frame, bg="#f5f6fa")
        cards_frame.pack(side="left", padx=50)

        def criar_card(master, titulo, valor, cor="#3498db"):
            card = tk.Frame(master, bg="white", width=130, height=50,
                            highlightthickness=1, highlightbackground="#dcdde1")
            card.pack(side="left", padx=5, pady=5)
            card.pack_propagate(False)
            tk.Label(card, text=titulo, font=("Helvetica", 11),
                     fg="#7f8c8d", bg="white").pack(anchor="w", padx=10, pady=5)
            tk.Label(card, text=valor, font=("Helvetica", 16, "bold"),
                     fg=cor, bg="white").pack(anchor="w", padx=10)
            return card

        agentes = carregar_novos_agentes(DB)
        ag_ativos = [a for a in agentes if a.conectado]
        ag_inativos = [a for a in agentes if not a.conectado]

        criar_card(cards_frame, "Ativos", f"{len(ag_ativos)}", "#27ae60")
        criar_card(cards_frame, "Pendentes", f"{len(ag_inativos)}", "#f39c12")
        criar_card(cards_frame, "Erros", "2", "#c0392b")

        # Botão Atualizar Status
        btns_frame = tk.Frame(top_frame, bg="#f5f6fa")
        btns_frame.pack(side="right", padx=10)
        tk.Button(
            btns_frame,
            text="🔄 Atualizar Status",
            fg="white", bg="#f39c12",
            font=("Helvetica", 10, "bold"),
            relief="flat", padx=15, pady=8,
            command=lambda: threading.Thread(
                target=lambda: asyncio.run(atualizar_status_parallel(agentes)),
                daemon=True
            ).start()
        ).pack(side="left", padx=5)

        # Lista de agentes
        frame_agentes = tk.Frame(frame, bg="white")
        frame_agentes.pack(fill="both", expand=True, padx=20, pady=10)
        canvas = tk.Canvas(frame_agentes, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_agentes, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        agentes.sort(key=lambda x: extrair_numero(x.nome))
        linha = 0
        celular_count = 1

        for i in range(0, len(agentes), 6):
            coluna = 0
            for c in range(3):
                if i + c * 2 >= len(agentes):
                    break
                tk.Label(scrollable_frame, text=f"📱 Celular {celular_count}",
                         font=("Helvetica", 12, "bold"), bg="#ecf0f1",
                         anchor="w", padx=10).grid(row=linha, column=coluna, columnspan=2,
                                                   pady=(20, 10), padx=20, sticky="nsew")
                for j in range(2):
                    idx = i + c * 2 + j
                    if idx < len(agentes):
                        ag = agentes[idx]
                        frame_ag = tk.Frame(scrollable_frame, bg="white",
                                            highlightthickness=1, highlightbackground="#dcdde1",
                                            padx=3, pady=3)
                        frame_ag.grid(row=linha + 1, column=coluna + j, padx=10, pady=5, sticky="nsew")
                        scrollable_frame.columnconfigure(coluna + j, weight=1)
                        status = tk.Canvas(frame_ag, width=15, height=15, bg="white", highlightthickness=0)
                        status.create_oval(2, 2, 13, 13, fill=cor_status(ag.conectado))
                        status.pack(side="top", pady=5)
                        btn = tk.Button(frame_ag, text=f"{ag.nome}\n{ag.numero or 'Sem número'}",
                                        bg=cor_status(ag.conectado), fg="white",
                                        font=("Helvetica", 9, "bold"), relief="raised",
                                        width=12, height=3, command=lambda a=ag: a.gerar_qr())
                        btn.pack(expand=True, fill="both")
                coluna += 2
                celular_count += 1
            linha += 2

        # Log
        frame_log = tk.Frame(frame, bg="white")
        frame_log.pack(fill="x", pady=10)
        self.log_text = tk.Text(frame_log, bg="#2c3e50", fg="white", wrap="word",
                                relief="flat", height=10)
        self.log_text.pack(fill="x", side="left", expand=True)
        scroll_log = ttk.Scrollbar(frame_log, orient="vertical", command=self.log_text.yview)
        scroll_log.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll_log.set)

        return frame

    # ================= Página: Maturação =================
    def criar_maturacao(self):
        frame = tk.Frame(self.root, bg="#f5f6fa")
        tk.Label(frame, text="📋 Maturação", font=("Helvetica", 20, "bold"),
                 bg="#f5f6fa", fg="#2c3e50").pack(pady=20)
        self.log_text = scrolledtext.ScrolledText(frame, height=10, bg="#2c3e50", fg="white", wrap="word")
        self.log_text.pack(fill="x", padx=10, pady=10)

        async def verificar_pares():
            try:
                log(self.log_text, "🔄 Verificando agentes e pares...", "info")
                agentes = await carregar_agentes_async_do_banco_async()
                agentes_conectados = [a for a in agentes if a.conectado]
                log(self.log_text, f"Agentes conectados: {len(agentes_conectados)}", "sucesso")
                pares = [tuple(par) for par in itertools.zip_longest(*[iter(agentes_conectados)]*2) if None not in par]
                log(self.log_text, f"Novos pares detectados: {len(pares)}", "info")
                return pares
            except Exception as e:
                log(self.log_text, f"❌ Erro ao verificar pares: {str(e)}", "erro")
                return []

        async def executar_maturacao():
            try:
                pares = await verificar_pares()
                if not pares:
                    log(self.log_text, "⚠️ Nenhum par disponível para maturação.", "alerta")
                    return
                sem = asyncio.Semaphore(20)
                tarefas = []

                async def conversar_com_limite(a1, a2):
                    async with sem:
                        try:
                            await conversar_async(a1, a2, 100, False, get_ia_response_ollama)
                            log(self.log_text, f"✅ Conversa concluída: {a1.nome} + {a2.nome}", "sucesso")
                        except Exception:
                            await conversar_async(a1, a2, 100, False, get_ia_response_gemini)
                            log(self.log_text, f"⚠️ Conversa com fallback: {a1.nome} + {a2.nome}", "alerta")

                for par in pares:
                    tarefas.append(asyncio.create_task(conversar_com_limite(par[0], par[1])))
                log(self.log_text, "▶️ Iniciando conversas...", "info")
                await asyncio.gather(*tarefas, return_exceptions=True)
                log(self.log_text, "✅ Maturação finalizada!", "sucesso")
            except Exception as e:
                log(self.log_text, f"❌ Erro durante maturação: {str(e)}", "erro")

        botoes_frame = tk.Frame(frame, bg="#f5f6fa")
        botoes_frame.pack(pady=10)
        tk.Button(botoes_frame, text="▶️ Iniciar Maturação", bg="#2980b9", fg="white",
                  font=("Helvetica", 12, "bold"), relief="flat",
                  command=lambda: asyncio.create_task(executar_maturacao())).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="🔍 Verificar Pares", bg="#f39c12", fg="white",
                  font=("Helvetica", 12, "bold"), relief="flat",
                  command=lambda: asyncio.create_task(verificar_pares())).pack(side="left", padx=5)
        tk.Button(botoes_frame, text="⏹ Parar Maturação", bg="#e74c3c", fg="white",
                  font=("Helvetica", 12, "bold"), relief="flat",
                  command=lambda: log(self.log_text, "⏹ Parada manual ativada!", "alerta")).pack(side="left", padx=5)

        return frame

    # ================= Página: Instâncias =================
    def criar_instancia(self):
        frame = tk.Frame(self.root, bg="#f5f6fa")
        tk.Label(frame, text="⚙ Instâncias", font=("Helvetica", 20, "bold"),
                 bg="#f5f6fa", fg="#2c3e50").pack(pady=20)
        tk.Button(
            frame,
            text="➕ Adicionar Maturação 1",
            bg="#27ae60",
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=5,
            command=lambda: threading.Thread(
                target=lambda: asyncio.run(carregar_agentes_inter("MATURACAO1")),
                daemon=True
            ).start()
        ).pack(pady=10)

        tk.Button(
            frame,
            text="➕ Adicionar Maturação 2",
            bg="#27ae60",
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=5,
            command=lambda: threading.Thread(
                target=lambda: asyncio.run(carregar_agentes_inter("MATURACAO2")),
                daemon=True
            ).start()
        ).pack(pady=10)

        tk.Button(
            frame,
            text="➕ Adicionar Novos",
            bg="#27ae60",
            fg="white",
            font=("Helvetica", 11, "bold"),
            padx=10,
            pady=5,
            command=lambda: threading.Thread(
                target=lambda: asyncio.run(carregar_agentes_inter("MATURACAO")),
                daemon=True
            ).start()
        ).pack(pady=10)

        canvas_frame = tk.Frame(frame, bg="#f5f6fa")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)
        canvas = tk.Canvas(canvas_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        agentes = carregar_agentes_do_banco(DB)
        agentes.sort(key=lambda x: x.nome)

        linha = 0
        for i in range(0, len(agentes), 7):
            coluna = 0
            for j in range(2):
                idx = i + j
                if idx >= len(agentes):
                    break
                ag = agentes[idx]
                frame_ag = tk.Frame(scrollable_frame, bg="white",
                                    highlightthickness=1, highlightbackground="#dcdde1",
                                    padx=5, pady=5, width=250, height=80)
                frame_ag.grid(row=linha, column=coluna, padx=10, pady=10)
                frame_ag.grid_propagate(False)

                status_canvas = tk.Canvas(frame_ag, width=15, height=15, bg="white", highlightthickness=0)
                status_canvas.create_oval(2, 2, 13, 13,
                                          fill="#27ae60" if getattr(ag, 'conectado', False) else "#c0392b")
                status_canvas.pack(side="left", padx=5)

                tk.Label(frame_ag, text=f"{ag.nome}", font=("Helvetica", 10, "bold"), bg="white").pack(anchor="w")
                tk.Label(frame_ag, text=f"Código: {getattr(ag, 'codigo', 'N/A')}", font=("Helvetica", 9),
                         bg="white").pack(anchor="w")
                tk.Label(frame_ag, text=f"Status: {'Ativo' if getattr(ag, 'conectado', False) else 'Inativo'}",
                         font=("Helvetica", 9), bg="white").pack(anchor="w")
                tk.Button(frame_ag, text="Detalhes", font=("Helvetica", 9), bg="#3498db", fg="white").pack(side="bottom", pady=2)
                coluna += 1
            linha += 1

        frame_log = tk.Frame(frame, bg="white")
        frame_log.pack(fill="x", pady=5)
        self.log_text = tk.Text(frame_log, bg="#2c3e50", fg="white", wrap="word",
                                relief="flat", height=5)
        self.log_text.pack(fill="x", side="left", expand=True)
        scroll_log = ttk.Scrollbar(frame_log, orient="vertical", command=self.log_text.yview)
        scroll_log.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll_log.set)

        return frame

    # ================= Página: Configurações =================
    def criar_settings(self):
        frame = tk.Frame(self.root, bg="#f5f6fa")
        tk.Label(frame, text="⚙ Configurações", font=("Helvetica", 20, "bold"),
                 bg="#f5f6fa", fg="#2c3e50").pack(pady=20)
        return frame

# ================= Main =================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
