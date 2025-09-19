import asyncio
import threading
import re
import tkinter as tk
from tkinter import ttk
from collections import defaultdict

# === Ajuste para seus módulos reais ===
from banco.dbo import (
    carregar_novos_agentes,
    carregar_agentes_inter,
    DB,
)
from integration.api_GTI import atualizar_status_parallel
from maturar.maturacao import main, criar_pares


# =====================================================
# Funções auxiliares
# =====================================================
def extrair_numero(nome: str) -> int:
    m = re.search(r'\d+', nome)
    return int(m.group()) if m else 0


def cor_status(conectado: bool) -> str:
    return "#27ae60" if conectado else "#c0392b"


# =====================================================
# Loop global do asyncio em thread separada
# =====================================================
loop = asyncio.new_event_loop()


def _start_loop():
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=_start_loop, daemon=True).start()


def run_async(coro):
    """Agenda uma corrotina no loop global."""
    return asyncio.run_coroutine_threadsafe(coro, loop)


# =====================================================
# App principal
# =====================================================
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Painel de Maturação GTI")
        self.root.geometry("1200x700")
        self.root.configure(bg="#222")
        self.root.option_add("*Font", "Segoe 10")

        # Cache simples
        self.cache_agentes = defaultdict(list)
        self.cache_tipo_rota = {}

        self._build_sidebar()
        self._build_pages()
        self.mostrar_pagina("dashboard")

    # -------------------------------------------------
    # Sidebar
    # -------------------------------------------------
    def _build_sidebar(self):
        self.sidebar = tk.Frame(self.root, bg="#333", width=180)
        self.sidebar.pack(side="left", fill="y")

        botoes = [
            ("Dashboard", lambda: self.mostrar_pagina("dashboard")),
            ("Maturação", lambda: self.mostrar_pagina("maturacao")),
            ("Instâncias", lambda: self.mostrar_pagina("instancias")),
            ("Config", lambda: self.mostrar_pagina("settings")),
        ]
        for txt, cmd in botoes:
            tk.Button(
                self.sidebar, text=txt, command=cmd,
                bg="#444", fg="white", relief="flat",
                activebackground="#555", activeforeground="white",
                width=20, pady=8
            ).pack(pady=5)

    # -------------------------------------------------
    # Páginas
    # -------------------------------------------------
    def _build_pages(self):
        self.pages = {}
        container = tk.Frame(self.root, bg="#222")
        container.pack(side="right", fill="both", expand=True)

        # Dashboard
        frame_dash = tk.Frame(container, bg="#222")
        self.pages["dashboard"] = frame_dash
        self._build_dashboard(frame_dash)

        # Maturação
        frame_mat = tk.Frame(container, bg="#222")
        self.pages["maturacao"] = frame_mat
        self._build_maturacao(frame_mat)

        # Instâncias
        frame_inst = tk.Frame(container, bg="#222")
        self.pages["instancias"] = frame_inst
        self._build_instancias(frame_inst)

        # Config
        frame_cfg = tk.Frame(container, bg="#222")
        self.pages["settings"] = frame_cfg
        tk.Label(frame_cfg, text="Configurações", fg="white", bg="#222").pack(pady=20)

    def mostrar_pagina(self, nome):
        for f in self.pages.values():
            f.pack_forget()
        self.pages[nome].pack(fill="both", expand=True)

    # -------------------------------------------------
    # Dashboard
    # -------------------------------------------------
    def _build_dashboard(self, frame):
        tk.Label(frame, text="Dashboard", fg="white", bg="#222", font=("Segoe", 14)).pack(pady=10)

        self.status_frame = tk.Frame(frame, bg="#222")
        self.status_frame.pack(fill="both", expand=True)

        tk.Button(
            frame, text="adicionar agentes",
            command=self.carregar_agentes,
            bg="#444", fg="white"
        ).pack(pady=10)
        tk.Button(
            frame, text="atualizar status",
            command= self._atualizar_status,
            bg="#444", fg="white"
        ).pack(pady=10)
    def carregar_agentes(self):
        async def agente_load():
            agentes = await carregar_agentes_inter("MATURACAO")
            self.cache_agentes = agentes
            self.root.after(0, self._refresh_dashboard)
            return self.cache_agentes
        run_async(agente_load())

    def _atualizar_status(self):
        agentes = self.cache_agentes.get("dashboard", [])
        async def task():
            await atualizar_status_parallel(agentes)
            self.cache_agentes["dashboard"] = agentes
            self.root.after(0, self._refresh_dashboard)
        run_async(task())

    def _refresh_dashboard(self):
        for w in self.status_frame.winfo_children():
            w.destroy()

        agentes = sorted(
            self.cache_agentes,
            key=lambda a: extrair_numero(a.nome)
        )

        ativos = sum(a.conectado for a in agentes)
        inativos = len(agentes) - ativos

        resumo = f"Total: {len(agentes)} | Ativos: {ativos} | Inativos: {inativos}"
        tk.Label(self.status_frame, text=resumo, fg="white", bg="#222").pack(pady=5)

        # Grade 4 colunas x 2 linhas por grupo de celular
        grid = tk.Frame(self.status_frame, bg="#222")
        grid.pack(fill="both", expand=True)

        linha = 0
        celular_count = 1
        for i in range(0, len(agentes), 8):
            col = 0
            for c in range(4):
                if i + c * 2 >= len(agentes):
                    break

                tk.Label(
                    grid, text=f"📱 Celular {celular_count}",
                    font=("Segoe", 12, "bold"),
                    bg="#333", fg="white"
                ).grid(row=linha, column=col, columnspan=2, pady=(15, 5), padx=10, sticky="nsew")

                for j in range(2):
                    idx = i + c * 2 + j
                    if idx >= len(agentes):
                        break
                    ag = agentes[idx]

                    frame_ag = tk.Frame(grid, bg="#222", padx=5, pady=5)
                    frame_ag.grid(row=linha + 1, column=col + j, padx=5, pady=5)

                    status = tk.Canvas(frame_ag, width=15, height=15,
                                       bg="#222", highlightthickness=0)
                    status.create_oval(2, 2, 13, 13, fill=cor_status(ag.conectado))
                    status.pack()

                    tk.Button(
                        frame_ag,
                        text=f"Desconectar {ag.nome}",
                        bg=cor_status(ag.conectado),
                        fg="white", width=10, height=2,
                        command=lambda a=ag: a.desconectar()
                    ).pack()

                    tk.Button(
                        frame_ag,
                        text=f"{ag.nome}\n{ag.numero or 'Sem número'}",
                        bg=cor_status(ag.conectado),
                        fg="white", width=12, height=3,
                        command=lambda a=ag: a.gerar_qr()
                    ).pack()

                col += 2
                celular_count += 1
            linha += 2

    # -------------------------------------------------
    # Maturação
    # -------------------------------------------------
    def _build_maturacao(self, frame):
        tk.Label(frame, text="Maturação", fg="white", bg="#222", font=("Segoe", 14)).pack(pady=10)

        tk.Button(frame, text="Iniciar Maturação",
                  command=lambda: run_async(main()),
                  bg="#444", fg="white").pack(pady=5)

        for nome in ["MATURACAO1", "MATURACAO2", "MATURACAO"]:
            tk.Button(frame, text=f"Carregar {nome}",
                      command=lambda n=nome: run_async(carregar_agentes_inter(n)),
                      bg="#444", fg="white").pack(pady=5)

        tk.Button(frame, text="Verificar Pares",
                  command=self.verificar_pares,
                  bg="#444", fg="white").pack(pady=5)

    def verificar_pares(self):
        agentes = []
        for lista in self.cache_agentes.values():
            agentes.extend(lista)
        run_async(criar_pares(agentes))

    # -------------------------------------------------
    # Instâncias
    # -------------------------------------------------
    def _build_instancias(self, frame):
        tk.Label(frame, text="Instâncias", fg="white", bg="#222", font=("Segoe", 14)).pack(pady=10)
        self.inst_frame = tk.Frame(frame, bg="#222")
        self.inst_frame.pack(fill="both", expand=True)

        for txt in ["MATURACAO1", "MATURACAO2", "MATURACAO"]:
            tk.Button(frame, text=txt, bg="#444", fg="white",
                      command=lambda t=txt: self.buscar_agentes(t)).pack(pady=4)

    def buscar_agentes(self, tipo):
        async def task():
            agentes = await carregar_agentes_inter(tipo)
            rotas = [a.tipo_rota for a in agentes]
            if rotas != self.cache_tipo_rota.get(tipo):
                self.cache_tipo_rota[tipo] = rotas
                self.cache_agentes[tipo] = agentes
                self.root.after(0, lambda: self._atualizar_instancias(tipo))
        run_async(task())

    def _atualizar_instancias(self, tipo):
        for w in self.inst_frame.winfo_children():
            w.destroy()
        for ag in self.cache_agentes.get(tipo, []):
            tk.Label(self.inst_frame,
                     text=f"{ag.nome} ({ag.tipo_rota})",
                     fg="white", bg="#222").pack(anchor="w", padx=20)


# =====================================================
# Execução
# =====================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)


    def preload():
        app.carregar_agentes()

    root.after(1, preload)

    root.mainloop()
