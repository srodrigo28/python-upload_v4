import paramiko
import sys
import time
from datetime import datetime

# Forçar UTF-8 no Windows
sys.stdout.reconfigure(encoding='utf-8')

def test_permissions():
    host = '77.37.126.7'
    port = 22
    username = 'srodrigo'
    password = '@dV#sRnAt98!'
    remote_path = '/var/www/precifex.com'

    print(f"--- Iniciando Teste de Permissões ---")
    print(f"Host: {host}")
    print(f"Usuário: {username}")
    print(f"Caminho Remoto: {remote_path}")
    print("-" * 30)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # 1. Testar Conexão SSH
        print(f"[1/4] Conectando via SSH...", end=' ')
        client.connect(host, port=port, username=username, password=password, timeout=10)
        print("[OK] Sucesso!")
    except Exception as e:
        print(f"[ERRO] Falha na conexão SSH: {e}")
        return

    sftp = None
    try:
        sftp = client.open_sftp()
        
        # 2. Testar Leitura (Listar Diretório)
        print(f"[2/4] Testando LEITURA em '{remote_path}'...", end=' ')
        try:
            files = sftp.listdir(remote_path)
            print("[OK] Conteúdo listado.")
            print(f"      {len(files)} itens encontrados:")
            for f in files:
                print(f"      - {f}")
        except IOError as e:
            print(f"[ERRO] Falha de LEITURA: {e}")
        
        # 3. Testar Escrita (Criar Arquivo)
        test_filename = f"test_perm_{int(time.time())}.txt"
        full_path = f"{remote_path}/{test_filename}"
        print(f"[3/4] Testando ESCRITA (criando '{test_filename}')...", end=' ')
        
        try:
            with sftp.open(full_path, 'w') as f:
                f.write(f"Teste de escrita realizado em {datetime.now()}")
            print("[OK] Arquivo criado.")
            
            # 4. Limpeza (Deletar Arquivo)
            print(f"[4/4] Limpando (removendo arquivo de teste)...", end=' ')
            try:
                sftp.remove(full_path)
                print("[OK] Arquivo removido.")
            except IOError as e:
                print(f"[AVISO] Escrita funcionou, mas falhou ao deletar: {e}")

        except IOError as e:
            print(f"[ERRO] Falha de ESCRITA: {e}")
            print("      Provavelmente o usuário não tem permissão de escrita nesta pasta.")

    except Exception as e:
        print(f"\n[ERRO] Erro inesperado durante operação SFTP: {e}")
    finally:
        if sftp: sftp.close()
        client.close()
        print("-" * 30)
        print("Teste finalizado.")

if __name__ == "__main__":
    try:
        test_permissions()
    except ImportError:
        print("Erro: Paramiko não instalado. Instale com 'pip install paramiko'")
