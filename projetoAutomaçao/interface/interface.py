import os
import sys
import tkinter as tk
import pygame
from threading import Thread
from tkinter.scrolledtext import ScrolledText

from drivers.drivers_whatsapp import whatsapp, pegar_udids
from drivers.drivers_whatsapp_bussines import bussines
from until.utilitys import *
from wireless.wireless import *

pygame.mixer.init()
#toca a musica quando inicia a interface
def tocar_audio():
    pygame.mixer.music.load("TemaInterface.mp3")
    pygame.mixer.music.play(-1)

som_path = os.path.join(os.path.dirname(__file__), "SomBotao.mp3")
som_clique = pygame.mixer.Sound(som_path)

def tocar_clique():
    som_clique.play()

# Lista de serviços de drivers (caso necessário)
drivers_services = []
udids = pegar_udids()
# === Janela principal ===
janela = tk.Tk()
janela.title('Central de Recadastro')
janela.geometry('800x600')

# Container principal
container = tk.Frame(janela, bg="#f0f0f0")
container.place(relx=0.5, rely=0.5, anchor="center")

# === Logo ===
fundo = tk.PhotoImage(file="ALT360_logo.png")
logo = tk.Label(container, image=fundo, bg="#f0f0f0")
logo.grid(row=1, column=0, columnspan=2, pady=(0, 20))

# === Aparência dos botões ===
aparencia_botao = {
    "bg": "#EF4036",
    "fg": "white",
    "font": ("Helvetica", 10, "bold"),
    "relief": "groove",
}

# === Aparência do log (opcional, atualmente não utilizado) ===
aparencia_LOG = {
    "fg": "black",
    "font": ("Arial", 20, "italic"),
}

# === Funções de ação dos botões ===
def executar():
    som_clique.play()
    label.config(text="WHATSAPP")
    Thread(target=whatsapp).start()  # Corrigido: não chamar diretamente

def executartd():
    som_clique.play()
    label.config(text="BUSINESS")
    Thread(target=bussines).start()
    # Coloque aqui o que a função deve fazer

def wireless():
    som_clique.play()
    label.config(text="CONECTANDO 📡")
    Thread(target=wireless).start()
    # Coloque aqui a lógica de conexão wireless

def verificarsf():
    som_clique.play()
    label.config(text="VERIFICANDO 🔍")
    Thread(target=pegar_udids).start()
    # Lógica de verificação

def limpar():
    som_clique.play()
    label.config(text="LIMPO 🗑️")
    log_area.configure(state='normal')
    log_area.delete(1.0, tk.END)
    log_area.configure(state='disabled')

def encerrar_serv():
    som_clique.play()
    label.config(text="ENCERRAR")
    Thread(target=encerrar_appium).start()

def otimizar_cel():
    som_clique.play()
    label.config(text="OTIMIZAR")
    Thread(target=otimizar_app, args=(udids,)).start()

# === Label principal ===
label = tk.Label(
    container,
    text="Conecte o celular para executar o recadastro 🔃"
)
label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

# === Botões ===
BTexec = tk.Button(container, text="WHATSAPP", command=executar, **aparencia_botao)
BTexec.grid(row=2, column=0, padx=10, pady=5)

BTexectd = tk.Button(container, text="BUSINESS", command=executartd, **aparencia_botao)
BTexectd.grid(row=2, column=1, padx=10, pady=5)

BTwireless = tk.Button(container, text="WIRELESS", command=wireless, **aparencia_botao)
BTwireless.grid(row=3, column=0, padx=10, pady=5)

BTverificar = tk.Button(container, text="VERIFICAR", command=verificarsf, **aparencia_botao)
BTverificar.grid(row=3, column=1, padx=10, pady=5)

BTlimpar = tk.Button(container, text="LIMPAR", command=limpar, **aparencia_botao)
BTlimpar.grid(row=4, column=0, padx=10, pady=5)

BTencerrar = tk.Button(container, text="ENCERRAR", command=encerrar_serv, **aparencia_botao)
BTencerrar.grid(row=4, column=1, padx=10, pady=5)

BTencerrar = tk.Button(container, text="OTIMIZAR", command=otimizar_cel, **aparencia_botao)
BTencerrar.grid(row=4, column=2, padx=10, pady=5)


# === Área de log ===
log_area = ScrolledText(container, height=10, width=60, state='disabled', bg="#f0f0f0")
log_area.grid(row=5, column=0, columnspan=2, pady=(20, 15))

# === Redirecionamento de stdout/stderr para log ===
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, message):
        self.widget.configure(state='normal')
        self.widget.insert(tk.END, message)
        self.widget.configure(state='disabled')
        self.widget.see(tk.END)

    def flush(self):
        pass

sys.stdout = TextRedirector(log_area)
sys.stderr = TextRedirector(log_area)

# === Iniciar interface ===
janela.after(100, tocar_audio)
janela.mainloop()
