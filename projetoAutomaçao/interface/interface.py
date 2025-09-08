import sys
from tkinter import simpledialog

from appium.webdriver.common.appiumby import AppiumBy
from threading import Thread
from tkinter.scrolledtext import ScrolledText
import tkinter as tk
from drivers.drivers_whatsapp import whatsapp, pegar_udids
from drivers.drivers_whatsapp_bussines import bussines
from until.utilitys import *
from wireless.wireless import *


# Lista de serviços de drivers (caso necessário)
drivers_services = []

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
logo.grid(row=1, column=0, columnspan=3, pady=(0, 20))

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

# == Funcao para pegar udids ==

def pegar_udids_interface():
    result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    udids = [line.split('\t')[0] for line in lines if 'device' in line]
    return udids

# === Funções de ação dos botões ===
def executar():
    m2m = str(simpledialog.askstring("Entrada necessária", "Digite seu nome:"))
    label.config(text="WHATSAPP")
    Thread(target=whatsapp, args=(m2m or None,)).start()


def executartd():

    label.config(text="BUSINESS")
    Thread(target=bussines).start()
    # Coloque aqui o que a função deve fazer

def wireless():

    label.config(text="CONECTANDO 📡")
    Thread(target=wireless).start()
    # Coloque aqui a lógica de conexão wireless

def verificarsf():

    label.config(text="VERIFICANDO 🔍")
    Thread(target=pegar_udids).start()
    # Lógica de verificação

def limpar():

    label.config(text="LIMPO 🗑️")
    log_area.configure(state='normal')
    log_area.delete(1.0, tk.END)
    log_area.configure(state='disabled')

def encerrar_serv():

    label.config(text="ENCERRAR")
    Thread(target=encerrar_appium).start()

def otimizar_cel():

    label.config(text="OTIMIZAR")
    Thread(target=otimizar_app, args=(pegar_udids_interface(),)).start()

# WhatsApp normal
def limpar_whatsapp_ui():
    label.config(text="Limpar Whatsapp")
    Thread(target=limpar_whatsapp, args=(pegar_udids_interface(),)).start()

# WhatsApp Business
def limpar_whatsapp_bussines_ui():
    label.config(text="Limpar Whatsapp Bussines")
    Thread(target=limpar_whatsapp_busines, args=(pegar_udids_interface(),)).start()

# === Label principal ===
label = tk.Label(
    container,
    text="Conecte o celular para executar o recadastro 🔃"
)
label.grid(row=0, column=0, columnspan=3, pady=(10,20))

# === Botões ===
BTexec = tk.Button(container, text="WHATSAPP", command=executar, **aparencia_botao)
BTexec.grid(row=2, column=0, padx=10, pady=5)

BTwireless = tk.Button(container, text="WIRELESS", command=wireless, **aparencia_botao)
BTwireless.grid(row=2, column=2, padx=10, pady=5)

BTlimpar = tk.Button(container, text="LIMPAR", command=limpar, **aparencia_botao)
BTlimpar.grid(row=3, column=2, padx=10, pady=5)

BTverificar = tk.Button(container, text="VERIFICAR", command=verificarsf, **aparencia_botao)
BTverificar.grid(row=3, column=0, padx=20, pady=5)

BTexectd = tk.Button(container, text="BUSINESS", command=executartd, **aparencia_botao)
BTexectd.grid(row=2, column=1, padx=10, pady=5)

BTotimizar=tk.Button(container, text="OTIMIZAR", command=otimizar_cel, **aparencia_botao)
BTotimizar.grid(row=3, column=1, padx=10, pady=5)

# === Área de log ===
log_area = ScrolledText(container, height=10, width=60, state='disabled', bg="black", fg="white")
log_area.grid(row=4, column=0, columnspan=3, pady=(20, 10))

BTencerrar = tk.Button(container, text="ENCERRAR", command=encerrar_serv, **aparencia_botao)
BTencerrar.grid(row=5, column=0, padx=10, pady=5)

BTlimparwhatsapp = tk.Button(container, text="Limpar Whatsapp", command=limpar_whatsapp_ui, **aparencia_botao)
BTlimparwhatsapp.grid(row=5, column=1, padx=10, pady=5)

BTlimparwhatsappBussines = tk.Button(container, text="Limpar Bussines", command=limpar_whatsapp_bussines_ui, **aparencia_botao)
BTlimparwhatsappBussines.grid(row=5, column=2, padx=10, pady=5)

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

janela.mainloop()
