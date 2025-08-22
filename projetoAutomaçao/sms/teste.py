import serial
import serial.tools.list_ports
import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

# =====================
# Funções Modulares
# =====================

def listar_portas():
    """Lista todas as portas COM disponíveis"""
    return [porta.device for porta in serial.tools.list_ports.comports()]

def testar_sms_porta(porta):
    """Testa se a porta responde aos comandos SMS"""
    try:
        ser = serial.Serial(porta, 115200, timeout=2)
        time.sleep(1)

        ser.write(b'AT\r')
        time.sleep(0.5)
        resposta = ser.read_all().decode(errors='ignore')
        if "OK" not in resposta:
            ser.close()
            return None

        ser.write(b'AT+CMGF=1\r')
        time.sleep(0.2)
        ser.write(b'AT+CNMI=2,1,0,0,0\r')
        time.sleep(0.2)
        ser.write(b'AT+CMGL="ALL"\r')
        time.sleep(0.5)
        resposta_sms = ser.read_all().decode(errors='ignore')

        if "+CMGL:" in resposta_sms or "OK" in resposta_sms:
            log(f"[OK] Porta SMS encontrada: {porta}")
            return ser
        else:
            ser.close()
            return None
    except Exception as e:
        log(f"[ERRO] {porta}: {e}")
        return None

def consultar_operadora(ser):
    """Consulta a operadora do SIM conectado"""
    try:
        if ser and ser.is_open:
            ser.write(b'AT+COPS?\r')
            time.sleep(0.5)
            resposta = ser.read_all().decode(errors='ignore').upper()

            if "CLARO" in resposta:
                return "CLARO"
            elif "TIM" in resposta:
                return "TIM"
            elif "VIVO" in resposta:
                return "VIVO"
            elif "OI" in resposta:
                return "OI"
            else:
                return "DESCONHECIDA"
        else:
            return "Porta fechada ou inválida"
    except Exception as e:
        log(f"[ERRO] Consulta operadora: {e}")
        return "ERRO"

def reset_modem(ser):
    """Reseta o modem/chipeira"""
    try:
        if ser and ser.is_open:
            ser.write(b'ATZ\r')  # Comando de reset
            time.sleep(1)
            ser.read_all()        # Limpa buffer
            log("📌 Modem resetado com sucesso")
        else:
            log("⚠️ Porta inválida ou fechada")
    except Exception as e:
        log(f"[ERRO] Reset do modem: {e}")

def mudar_slot(ser, slot_numero):
    """Ativa um slot específico e reseta o modem"""
    log(f"🔄 Mudando para o slot {slot_numero}")
    # Aqui você enviaria o comando para o microcontrolador/chipeira
    # Exemplo: microcontrolador.write(f"SLOT {slot_numero}\n")
    time.sleep(0.2)
    reset_modem(ser)

def monitorar_sms(ser, stop_event):
    """Monitora SMS em tempo real em thread separada"""
    log("📩 Monitorando SMS em tempo real...")
    try:
        while not stop_event.is_set():
            if ser.in_waiting:
                data = ser.read(ser.in_waiting).decode(errors='ignore').strip()
                if data:
                    log(f"Nova mensagem recebida:\n{data}")
            time.sleep(0.2)
    except Exception as e:
        log(f"[ERRO] Monitoramento: {e}")
    finally:
        if ser and ser.is_open:
            ser.close()
        log("🛑 Monitoramento encerrado")

# =====================
# Interface Tkinter
# =====================

def log(msg):
    """Adiciona mensagem ao log"""
    txt_log.configure(state='normal')
    txt_log.insert(tk.END, msg + "\n")
    txt_log.see(tk.END)
    txt_log.configure(state='disabled')

def iniciar_monitoramento():
    global stop_event, monitor_thread
    if serial_sms is None:
        messagebox.showwarning("Aviso", "Nenhuma porta SMS conectada")
        return
    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=monitorar_sms, args=(serial_sms, stop_event))
    monitor_thread.start()

def parar_monitoramento():
    if stop_event:
        stop_event.set()

def verificar_operadora():
    if serial_sms:
        op = consultar_operadora(serial_sms)
        log(f"Operadora detectada: {op}")
    else:
        log("Nenhuma porta ativa")

def limpar_log():
    txt_log.configure(state='normal')
    txt_log.delete(1.0, tk.END)
    txt_log.configure(state='disabled')

def reset_modem_gui():
    if serial_sms:
        reset_modem(serial_sms)
    else:
        log("Nenhuma porta ativa para resetar")

# =====================
# Inicialização GUI
# =====================

root = tk.Tk()
root.title("Gerenciador SMS")

# Frame de botões
frame_botoes = tk.Frame(root)
frame_botoes.pack(padx=10, pady=10)

btn_operadora = tk.Button(frame_botoes, text="Verificar Operadora", command=verificar_operadora)
btn_operadora.grid(row=0, column=0, padx=5, pady=5)

btn_monitor = tk.Button(frame_botoes, text="Iniciar Monitoramento", command=iniciar_monitoramento)
btn_monitor.grid(row=0, column=1, padx=5, pady=5)

btn_reset = tk.Button(frame_botoes, text="RESET", command=reset_modem_gui)
btn_reset.grid(row=0, column=2, padx=5, pady=5)

btn_limpar = tk.Button(frame_botoes, text="Limpar Log", command=limpar_log)
btn_limpar.grid(row=0, column=3, padx=5, pady=5)

# Log de mensagens
txt_log = scrolledtext.ScrolledText(root, width=80, height=20, state='disabled')
txt_log.pack(padx=10, pady=10)

# Variáveis globais
serial_sms = None
stop_event = None
monitor_thread = None

# Detecta porta SMS automaticamente
portas = listar_portas()
log(f"Portas disponíveis: {portas}")
for porta in portas:
    serial_sms = testar_sms_porta(porta)
    if serial_sms:
        break

if serial_sms:
    op = consultar_operadora(serial_sms)
    log(f"Operadora detectada: {op}")
else:
    log("⚠️ Nenhuma porta respondeu corretamente aos comandos SMS.")

root.mainloop()
