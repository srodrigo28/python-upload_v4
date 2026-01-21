import paramiko
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

# Configurações do Servidor
HOST = '77.37.126.7'
PORT = 22
USERNAME = 'srodrigo'
PASSWORD = '@dV#sRnAt98!'
REMOTE_BASE_PATH = '/var/www/precifex.com'

def select_file():
    """Abre diálogo para selecionar arquivo local"""
    root = tk.Tk()
    root.withdraw() # Ocultar janela principal
    root.attributes('-topmost', True) # Garantir que apareça no topo
    
    file_path = filedialog.askopenfilename(title="Selecione um arquivo para upload de teste")
    root.destroy()
    return file_path

def upload_file(local_path):
    """Faz upload do arquivo selecionado"""
    if not local_path:
        print("Nenhum arquivo selecionado.")
        return

    filename = os.path.basename(local_path)
    remote_path = f"{REMOTE_BASE_PATH}/{filename}"
    
    print(f"--- INICIANDO UPLOAD ---")
    print(f"Local: {local_path}")
    print(f"Destino: {remote_path}")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("1. Conectando...", end=' ')
        client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=10)
        print("OK")
        
        sftp = client.open_sftp()
        
        # O sftp.put já sobrescreve se existir (atualiza) ou cria se não existir
        print(f"2. Enviando arquivo...", end=' ')
        
        # Callback para mostrar progresso (opcional, simples)
        def progress(transferred, total):
            # sys.stdout.write(f"\r    Progresso: {transferred}/{total} bytes")
            # sys.stdout.flush()
            pass

        sftp.put(local_path, remote_path, callback=progress)
        print("OK")
        
        print("\n✅ UPLOAD CONCLUÍDO COM SUCESSO!")
        print("O arquivo foi criado/atualizado no servidor.")
        
        sftp.close()
        client.close()
        
    except Exception as e:
        print(f"\n❌ ERRO NO UPLOAD: {e}")

if __name__ == "__main__":
    print("Selecione o arquivo na janela que abrirá...")
    local_file = select_file()
    if local_file:
        upload_file(local_file)
    else:
        print("Operação cancelada pelo usuário.")
