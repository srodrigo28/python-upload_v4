import paramiko
import sys
import time
from datetime import datetime

# Configurações
HOST = '77.37.126.7'
PORT = 22
USERNAME = 'srodrigo'
PASSWORD = '@dV#sRnAt98!'
REMOTE_PATH = '/var/www/precifex.com'

def test_write_permission():
    print(f"--- TESTE DE ESCRITA: {REMOTE_PATH} ---")
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # 1. Conexão
        print("1. Conectando...", end=' ')
        client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=10)
        print("OK")
        
        sftp = client.open_sftp()
        
        # 2. Teste de Escrita
        test_file = f"{REMOTE_PATH}/teste_escrita_{int(time.time())}.txt"
        print(f"2. Tentando criar arquivo: {test_file}...", end=' ')
        
        try:
            with sftp.open(test_file, 'w') as f:
                f.write("Teste de permissao de escrita OK")
            print("OK (Arquivo criado)")
            
            # 3. Verificacao
            print("3. Verificando se arquivo existe...", end=' ')
            try:
                sftp.stat(test_file)
                print("OK (Arquivo encontrado)")
            except IOError:
                print("FALHA (Arquivo nao encontrado apos escrit)")
                
            # 4. Limpeza
            print("4. Removendo arquivo de teste...", end=' ')
            try:
                sftp.remove(test_file)
                print("OK (Arquivo removido)")
                print("\nResultado Final: PERMISSAO DE ESCRITA CONFIRMADA!")
            except IOError:
                print("FALHA (Nao foi possivel remover o arquivo)")
                
        except IOError as e:
            print(f"FALHA NA ESCRITA: {e}")
            print("\nResultado Final: SEM PERMISSAO DE ESCRITA.")
            
        sftp.close()
        client.close()
        
    except Exception as e:
        print(f"\nERRO DE CONEXAO OU SISTEMA: {e}")

if __name__ == "__main__":
    test_write_permission()
