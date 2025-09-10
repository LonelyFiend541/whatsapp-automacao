import json
import sys
import threading
import tkinter
from doctest import master
from tkinter import simpledialog, messagebox

from appium.webdriver.common.appiumby import AppiumBy
from threading import Thread
from tkinter.scrolledtext import ScrolledText
import tkinter as tk

from drivers.drivers_whatsapp import whatsapp, pegar_udids
from drivers.drivers_whatsapp_bussines import bussines
from integration.IA import tratar_erro_ia
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

def pegar_udids_interface():
    result = subprocess.run([ADB_PATH, 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    udids = [line.split('\t')[0] for line in lines if 'device' in line]
    return udids

def sinalizar_dispositivo(udid):
    titulo = f"Atenção! {str(udid)}"
    mensagem = f"{str(udid)}"
    comando = [
        "adb", "-s", udid, "shell", "cmd", "notification", "post",
        "-S", "bigtext", "-t", titulo,  mensagem
    ]
    subprocess.run(comando)

# === Funções de ação dos botões ===

class MeuDialogo(simpledialog.Dialog):
    def __init__(self, parent, title, label_resultado=None, udid=""):
        self.label_resultado = label_resultado
        self.udid = udid  # Passa o UDID se quiser usar no resultado
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text="Chip 1:").grid(row=0, column=0, sticky="e")
        tk.Label(master, text="Chip 2:").grid(row=1, column=0, sticky="e")

        self.entry_chip1 = tk.Entry(master)
        self.entry_chip2 = tk.Entry(master)

        self.entry_chip1.grid(row=0, column=1)
        self.entry_chip2.grid(row=1, column=1)

        # 🔔 Botão de sinalizar celular
        sinalizar_btn = tk.Button(master, text="📱 Sinalizar Celular", command=self.sinalizar_celular, bg="#FFC107")
        sinalizar_btn.grid(row=2, column=0, columnspan=2, pady=(10, 0))

        return self.entry_chip1  # foco inicial

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
        self.resultado = {
            "UDID": self.udid,
            "Chip 1": self.chip1,
            "Chip 2": self.chip2
        }

        if self.label_resultado:
            self.label_resultado.config(
                text=f"UDID: {self.udid} | Chip 1: {self.chip1} | Chip 2: {self.chip2}"
            )
        dados_recadastro =carregar_recadastro()
        # Atualiza ou adiciona na lista
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
            import os
            caminho_local = os.path.abspath("SomBotao.mp3")
            destino_android = "/sdcard/SomBotao.mp3"

            if not os.path.exists(caminho_local):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho_local}")
            print(f"📁 Enviando: {caminho_local}")

            subprocess.run([
                "adb", "-s", self.udid, "push", caminho_local, destino_android
            ], check=True)

            # Tenta aumentar o volume
            try:
                subprocess.run([
                    "adb", "-s", self.udid, "shell", "media", "volume", "--stream", "3", "--set", "15"
                ], check=True)
            except subprocess.CalledProcessError:
                print(f"⚠️ Comando 'media volume' não suportado por {self.udid}. Tentando alternativa...")
                try:
                    subprocess.run([
                        "adb", "-s", self.udid, "shell", "service", "call", "audio", "3", "i32", "3", "i32", "15"
                    ], check=True)
                except subprocess.CalledProcessError:
                    print(f"⚠️ Alternativa de volume também falhou em {self.udid}")

            # Envia notificação
            subprocess.run([
                "adb", "-s", self.udid, "shell", "cmd", "notification", "post",
                "-S", "bigtext", "-t", "ATENÇÃO", "recadastro", f"{self.udid}"
            ], check=True)

            # Reproduz som
            subprocess.run([
                "adb", "-s", self.udid, "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", "file:///sdcard/SomBotao.mp3",
                "-t", "audio/mp3"
            ], check=True)

            print(f"📢 Sinalização enviada para o celular {self.udid}")

        except Exception as e:
            print(f"❌ Erro ao sinalizar o celular {self.udid}: {e}")


def abrir_dialogo_com_udid(udid, label_resultado=None):
    MeuDialogo(janela, title=udid, label_resultado=label_resultado, udid=udid)

def salvar_json(dados):
    caminho = os.path.join(HISTORICO_DIR, f"dados_recadastro.json")
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(tratar_erro_ia(e))
        print(f"⚠️ Erro ao salvar histórico: {e}")


def abrir_dialogos_em_threads():
    udids = pegar_udids_interface()
    for udid in udids:
        # agendar abertura na thread principal
        janela.after(0, abrir_dialogo_com_udid, udid, label)

def executar():
    label.config(text="WHATSAPP")
    Thread(target=whatsapp).start()


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

udids = pegar_udids_interface()

for i, udid in enumerate(udids):
    botao = tk.Button(container, text=f"Executar {udid}", command=lambda u=udid: executar(u), **aparencia_botao)
    botao.grid(row=6, column=i)


BTexec = tk.Button(container, text="WHATSAPP", command=executar, **aparencia_botao)
BTexec.grid(row=2, column=0, padx=10, pady=5)

btn = tk.Button(janela, text="Abrir diálogos", command=abrir_dialogos_em_threads)
btn.pack()

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
