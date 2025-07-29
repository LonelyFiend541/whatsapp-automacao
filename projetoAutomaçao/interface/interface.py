import tkinter as tk
import threading
import subprocess

def rodar_automacao():
    # Exemplo: rodar um script principal do seu projeto
    subprocess.run(['python', 'projetoAutomaçao/drivers/mult_drivers.py'])

def iniciar_automacao():
    # Roda em thread para não travar a interface
    threading.Thread(target=rodar_automacao).start()

janela = tk.Tk()
janela.title('Automação WhatsApp')
janela.geometry('300x200')

btn_iniciar = tk.Button(janela, text="Iniciar Automação", command=iniciar_automacao, font=("Arial", 14))
btn_iniciar.pack(pady=60)

janela.mainloop()