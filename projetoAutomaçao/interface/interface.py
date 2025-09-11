import json
import sys
import threading
import tkinter
from tkinter import simpledialog, messagebox
from threading import Thread
from tkinter.scrolledtext import ScrolledText
import tkinter as tk
import subprocess
import os

# imports do seu projeto (mantive como você tinha)
from appium.webdriver.common.appiumby import AppiumBy
from drivers.drivers_whatsapp import whatsapp, pegar_udids
from drivers.drivers_whatsapp_bussines import bussines
from integration.IA import tratar_erro_ia
from until.utilitys import *
from wireless.wireless import *

# === Janela principal ===
janela = tk.Tk()
janela.title('Central de Recadastro')
janela.geometry('1000x700')

# Container principal
container = tk.Frame(janela, bg="#f0f0f0")
container.place(relx=0.5, rely=0.5, anchor="center")

# === Logo (tenta carregar imagem) ===
try:
    fundo = tk.PhotoImage(file="ALT360_logo.png")
    logo = tk.Label(container, image=fundo, bg="#f0f0f0")
    logo.grid(row=1, column=0, columnspan=3, pady=(0, 20))
except Exception:
    logo = tk.Label(container, text="ALT360", bg="#f0f0f0", font=("Helvetica", 16, "bold"))
    logo.grid(row=1, column=0, columnspan=3, pady=(0, 20))

# === Aparência dos botões ===
aparencia_botao = {
    "bg": "#EF4036",
    "fg": "white",
    "font": ("Helvetica", 10, "bold"),
    "relief": "groove",
}

# === Área de log ===
log_area = ScrolledText(container, height=10, width=90, state='disabled', bg="black", fg="white")
log_area.grid(row=4, column=0, columnspan=3, pady=(20, 10))

# Redireciona stdout/stderr para o log_area
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        # mantém o widget em readonly exceto durante a escrita
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, message)
        self.widget.configure(state='disabled')
        self.widget.see(tk.END)

    def flush(self):
        pass

sys.stdout = TextRedirector(log_area)
sys.stderr = TextRedirector(log_area)

# == Funcao para pegar udids ==
HISTORICO_DIR = "Numeros"
os.makedirs(HISTORICO_DIR, exist_ok=True)

def carregar_recadastro():
    caminho = os.path.join(HISTORICO_DIR, f"dados_recadastro.json")
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler histórico: {e}")
            tratar_erro_ia(e)
    return []

def salvar_json(dados):
    caminho = os.path.join(HISTORICO_DIR, f"dados_recadastro.json")
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(tratar_erro_ia(e))
        print(f"⚠️ Erro ao salvar histórico: {e}")

def pegar_udids_interface():
    # usa ADB para pegar devices conectados
    try:
        result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        udids = [line.split('\t')[0] for line in lines if '\tdevice' in line]
        return udids
    except Exception as e:
        print(f"Erro pegar_udids_interface: {e}")
        return []

# === Funções de ação dos botões (mantive suas implementações) ===
class MeuDialogo(simpledialog.Dialog):
    def __init__(self, parent, title, label_resultado=None, udid=""):
        self.label_resultado = label_resultado
        self.udid = udid
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Chip 1:").grid(row=0, column=0, sticky="e")
        tk.Label(master, text="Chip 2:").grid(row=1, column=0, sticky="e")
        self.entry_chip1 = tk.Entry(master)
        self.entry_chip2 = tk.Entry(master)
        self.entry_chip1.grid(row=0, column=1)
        self.entry_chip2.grid(row=1, column=1)
        sinalizar_btn = tk.Button(master, text="📱 Sinalizar Celular", command=self.sinalizar_celular, bg="#FFC107")
        sinalizar_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        return self.entry_chip1

    def validate(self):
        try:
            self.chip1 = self.entry_chip1.get().strip()
            self.chip2 = self.entry_chip2.get().strip()
            if not self.chip1 or not self.chip2:
                raise ValueError("Campos vazios")
            return True
        except ValueError:
            messagebox.showerror("Erro", "Preencha os dados corretamente!")
            return False

    def apply(self):
        self.resultado = {"UDID": self.udid, "Chip 1": self.chip1, "Chip 2": self.chip2}
        if self.label_resultado:
            self.label_resultado.config(text=f"UDID: {self.udid} | Chip 1: {self.chip1} | Chip 2: {self.chip2}")
        dados_recadastro = carregar_recadastro()
        for linha in dados_recadastro:
            if self.udid == linha.get("UDID"):
                linha["Chip 1"] = self.chip1
                linha["Chip 2"] = self.chip2
                break
        else:
            dados_recadastro.append(self.resultado)
        salvar_json(dados_recadastro)

    def sinalizar_celular(self):
        try:
            caminho_local = os.path.abspath("SomBotao.mp3")
            destino_android = "/sdcard/SomBotao.mp3"
            if not os.path.exists(caminho_local):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_local}")
            print(f"📁 Enviando: {caminho_local}")
            subprocess.run(["adb", "-s", self.udid, "push", caminho_local, destino_android], check=True)
            try:
                subprocess.run(["adb", "-s", self.udid, "shell", "media", "volume", "--stream", "3", "--set", "15"], check=True)
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(["adb", "-s", self.udid, "shell", "service", "call", "audio", "3", "i32", "3", "i32", "15"], check=True)
                except subprocess.CalledProcessError:
                    print(f"⚠️ Alternativa de volume também falhou em {self.udid}")
            subprocess.run(["adb", "-s", self.udid, "shell", "cmd", "notification", "post", "-S", "bigtext", "-t", "ATENÇÃO", "recadastro", f"{self.udid}"], check=True)
            subprocess.run(["adb", "-s", self.udid, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", "file:///sdcard/SomBotao.mp3", "-t", "audio/mp3"], check=True)
            print(f"📢 Sinalização enviada para o celular {self.udid}")
        except Exception as e:
            print(f"❌ Erro ao sinalizar o celular {self.udid}: {e}")

def abrir_dialogo_com_udid(udid, label_resultado=None):
    MeuDialogo(janela, title=udid, label_resultado=label_resultado, udid=udid)

def ver_dados(u):
    dados = carregar_recadastro()
    for dado in dados:
        if u == dado.get("UDID"):
            info = f"UDID: {dado.get('UDID')}\nChip 1: {dado.get('Chip 1')}\nChip 2: {dado.get('Chip 2')}"
            print(info)
            # mostra em popup para facilitar
            messagebox.showinfo(f"Dados - {u}", info)
            return
    messagebox.showinfo(f"Dados - {u}", "Nenhum dado de recadastro encontrado.")

# Ações principais (mantidas)
def executar():
    label.config(text="WHATSAPP")
    Thread(target=whatsapp).start()

def executartd():
    label.config(text="BUSINESS")
    Thread(target=bussines).start()

def wireless_action():
    label.config(text="CONECTANDO 📡")
    Thread(target=wireless).start()

def encerrar_serv():
    label.config(text="ENCERRAR")
    Thread(target=encerrar_appium).start()

def otimizar_cel():
    label.config(text="OTIMIZAR")
    Thread(target=otimizar_app, args=(pegar_udids_interface(),)).start()

def limpar_whatsapp_ui():
    label.config(text="Limpar Whatsapp")
    Thread(target=limpar_whatsapp, args=(pegar_udids_interface(),)).start()

def limpar_whatsapp_bussines_ui():
    label.config(text="Limpar Whatsapp Bussines")
    Thread(target=limpar_whatsapp_busines, args=(pegar_udids_interface(),)).start()

# === Label principal ===
label = tk.Label(container, text="Conecte o celular para executar o recadastro 🔃")
label.grid(row=0, column=0, columnspan=3, pady=(10,20))

# === Botões de ação principais ===
BTexec = tk.Button(container, text="WHATSAPP", command=executar, **aparencia_botao)
BTexec.grid(row=2, column=0, padx=10, pady=5)

BTexectd = tk.Button(container, text="BUSINESS", command=executartd, **aparencia_botao)
BTexectd.grid(row=2, column=1, padx=10, pady=5)

BTwireless = tk.Button(container, text="WIRELESS", command=wireless_action, **aparencia_botao)
BTwireless.grid(row=2, column=2, padx=10, pady=5)

# limpar log (corrigida)
def limpar():
    label.config(text="LIMPO 🗑️")
    try:
        log_area.configure(state='normal')
        log_area.delete('1.0', tk.END)
        log_area.configure(state='disabled')
    except Exception as e:
        print(f"Erro ao limpar log: {e}")

BTlimpar = tk.Button(container, text="LIMPAR", command=limpar, **aparencia_botao)
BTlimpar.grid(row=3, column=2, padx=10, pady=5)

BTotimizar = tk.Button(container, text="OTIMIZAR", command=otimizar_cel, **aparencia_botao)
BTotimizar.grid(row=3, column=1, padx=10, pady=5)

BTencerrar = tk.Button(container, text="ENCERRAR", command=encerrar_serv, **aparencia_botao)
BTencerrar.grid(row=5, column=0, padx=10, pady=5)

BTlimparwhatsapp = tk.Button(container, text="Limpar Whatsapp", command=limpar_whatsapp_ui, **aparencia_botao)
BTlimparwhatsapp.grid(row=5, column=1, padx=10, pady=5)

BTlimparwhatsappBussines = tk.Button(container, text="Limpar Bussines", command=limpar_whatsapp_bussines_ui, **aparencia_botao)
BTlimparwhatsappBussines.grid(row=5, column=2, padx=10, pady=5)

# Botão para abrir diálogos (mantido)
btn = tk.Button(janela, text="Abrir diálogos", command=lambda: Thread(target=abrir_dialogos_em_threads).start())
btn.pack(pady=6)

# === Área rolável para lista de celulares ===
frame_scroll = tk.Frame(container, bg="#f0f0f0")
frame_scroll.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)

canvas_udids = tk.Canvas(frame_scroll, height=220, bg="#f0f0f0", highlightthickness=0)
scrollbar_udids = tk.Scrollbar(frame_scroll, orient="vertical", command=canvas_udids.yview)
scrollable_frame = tk.Frame(canvas_udids, bg="#f0f0f0")

scrollable_frame.bind("<Configure>", lambda e: canvas_udids.configure(scrollregion=canvas_udids.bbox("all")))
canvas_udids.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas_udids.configure(yscrollcommand=scrollbar_udids.set)

canvas_udids.pack(side="left", fill="both", expand=True)
scrollbar_udids.pack(side="right", fill="y")

# Dicionário para guardar widgets por UDID (armazenamos frame e botões)
botoes_udids = {}
grid_cols = 5  # número de colunas na grid de botões

# Garante que as colunas expandam igualmente
for c in range(grid_cols):
    scrollable_frame.grid_columnconfigure(c, weight=1)

# Função que atualiza UI: adiciona novos e remove desconectados
def atualizar_botao_udids(udids):
    atuais = set(udids)
    existentes = set(botoes_udids.keys())

    # remover desconectados
    para_remover = existentes - atuais
    for udid in para_remover:
        try:
            item = botoes_udids.pop(udid)
            item['frame'].destroy()
            print(f"❌ Removido: {udid}")
        except Exception as e:
            print(f"Erro ao remover botão {udid}: {e}")

    # adicionar novos (mantendo ordem)
    ordenados = list(udids)
    for i, udid in enumerate(ordenados):
        row = i // grid_cols
        col = i % grid_cols
        if udid not in botoes_udids:
            # Frame que contém os botões do UDID
            cell = tk.Frame(scrollable_frame, bg="#ffffff", bd=0, relief='flat')
            # botão principal abre diálogo (QR / edição)
            main_btn = tk.Button(cell,
                                 text=f"📱 {udid}",
                                 command=lambda u=udid: abrir_dialogo_com_udid(u),
                                 **aparencia_botao)
            # botão menor para ver dados
            info_btn = tk.Button(cell,
                                 text="Ver dados",
                                 command=lambda u=udid: ver_dados(u),
                                 bg="#3498db", fg="white",
                                 font=("Helvetica", 8, "bold"))
            # layout interno do cell
            main_btn.pack(fill='both', expand=True)
            info_btn.pack(fill='x', pady=(4,0))
            # posiciona o cell na grade
            cell.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            botoes_udids[udid] = {'frame': cell, 'main': main_btn, 'info': info_btn}
            # garante expandir a coluna
            scrollable_frame.grid_columnconfigure(col, weight=1)
            print(f"➕ Adicionado: {udid}")
        else:
            # reposiciona o frame para manter ordem correta na grid
            item = botoes_udids[udid]
            item['frame'].grid_configure(row=row, column=col)

# Worker que busca udids em thread e atualiza a UI com janela.after
def atualizar_udids_worker():
    label.config(text="ATUALIZANDO 🔄")
    udids = pegar_udids_interface()
    janela.after(0, lambda: atualizar_botao_udids(udids))
    janela.after(0, lambda: label.config(text=f"Conectados: {len(udids)}"))

# Função pública chamada pelo botão VERIFICAR
def verificarsf():
    Thread(target=atualizar_udids_worker, daemon=True).start()

# Botão VERIFICAR/ATUALIZAR
BTverificar = tk.Button(container, text="VERIFICAR/ATUALIZAR", command=verificarsf, **aparencia_botao)
BTverificar.grid(row=3, column=0, padx=20, pady=5)

# === Abrir diálogos em threads ===
def abrir_dialogos_em_threads():
    udids = pegar_udids_interface()
    for udid in udids:
        janela.after(0, abrir_dialogo_com_udid, udid, label)

# inicia loop da interface
janela.mainloop()
