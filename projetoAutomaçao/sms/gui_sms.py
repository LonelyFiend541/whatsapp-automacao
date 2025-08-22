import tkinter as tk
from tkinter import scrolledtext
from sms_modem import listar_portas, testar_sms_porta, consultar_operadora, consultar_numero

# -------------------
# Interface gráfica
# -------------------

class SMSGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador SMS")

        self.serial_sms = None

        # Frame de botões
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(padx=10, pady=5)

        self.btn_operadora = tk.Button(frame_botoes, text="Verificar Operadora", width=20, command=self.verificar_operadora)
        self.btn_operadora.grid(row=0, column=0, padx=5)

        self.btn_numero = tk.Button(frame_botoes, text="Verificar Número", width=20, command=self.verificar_numero)
        self.btn_numero.grid(row=0, column=1, padx=5)

        self.btn_limpar = tk.Button(frame_botoes, text="Limpar Log", width=20, command=self.limpar_log)
        self.btn_limpar.grid(row=0, column=2, padx=5)

        # Log
        self.txt_log = scrolledtext.ScrolledText(root, width=80, height=25, state='disabled')
        self.txt_log.pack(padx=10, pady=10)

        # Inicializa portas
        self.inicializar_porta()

    def log(self, texto):
        self.txt_log.configure(state='normal')
        self.txt_log.insert(tk.END, texto + "\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state='disabled')

    def limpar_log(self):
        self.txt_log.configure(state='normal')
        self.txt_log.delete(1.0, tk.END)
        self.txt_log.configure(state='disabled')

    def inicializar_porta(self):
        portas = listar_portas()
        self.log("Portas disponíveis: " + ", ".join(portas))

        for porta in portas:
            self.serial_sms = testar_sms_porta(porta, log_callback=self.log)
            if self.serial_sms:
                break

        if self.serial_sms:
            operadora = consultar_operadora(self.serial_sms)
            self.log(f"Operadora detectada: {operadora}")
        else:
            self.log("⚠️ Nenhuma porta respondeu corretamente aos comandos SMS.")

    def verificar_operadora(self):
        if self.serial_sms:
            op = consultar_operadora(self.serial_sms)
            self.log(f"Operadora: {op}")
        else:
            self.log("Nenhuma porta ativa.")

    def verificar_numero(self):
        if self.serial_sms:
            numero = consultar_numero(self.serial_sms)
            self.log("Número do SIM:\n" + numero)
        else:
            self.log("Nenhuma porta ativa.")

# -------------------
# Loop principal
# -------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SMSGUI(root)
    root.mainloop()
