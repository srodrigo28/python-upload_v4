"""
Gerenciador de operações de deploy
Responsável por: Upload PSCP, SSH, Listagem de arquivos, Import SQL
"""
import subprocess
import paramiko
import os
from datetime import datetime


class DeployManager:
    """Classe para gerenciar operações de deploy"""
    
    def __init__(self):
        self.ssh_client = None
        self.sftp_client = None
        
    def upload_files(self, data):
        """Upload de arquivos via PSCP"""
        try:
            local_path = data['local_path']
            host = data['host']
            port = data['port']
            username = data['username']
            password = data['password']
            remote_path = data['remote_path']
            
            # Verificar se PSCP existe
            pscp_paths = [
                'pscp',
                r'C:\Program Files\PuTTY\pscp.exe',
                r'C:\Program Files (x86)\PuTTY\pscp.exe'
            ]
            
            pscp_cmd = None
            for path in pscp_paths:
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, timeout=2)
                    pscp_cmd = path
                    break
                except:
                    continue
            
            if not pscp_cmd:
                return False, "PSCP não encontrado. Instale o PuTTY e adicione ao PATH do Windows."
            
            # Construir comando PSCP
            cmd = [
                pscp_cmd,
                '-r',
                '-P', port,
                '-pw', password,
                f"{local_path}\\*",
                f"{username}@{host}:{remote_path}"
            ]
            
            # Executar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos timeout
            )
            
            if result.returncode == 0:
                return True, "Upload concluído com sucesso"
            else:
                error_msg = result.stderr or result.stdout or "Erro desconhecido no upload"
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, "Timeout: Upload demorou muito tempo"
        except FileNotFoundError:
            return False, "PSCP não encontrado. Instale o PuTTY e adicione ao PATH"
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def connect_ssh(self, data):
        """Conectar via SSH usando Paramiko"""
        try:
            if self.ssh_client:
                self.ssh_client.close()
                
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=data['host'],
                port=int(data['port']),
                username=data['username'],
                password=data['password'],
                timeout=10
            )
            
            return True, "Conectado com sucesso"
            
        except paramiko.AuthenticationException:
            return False, "Erro de autenticação: usuário ou senha incorretos"
        except paramiko.SSHException as e:
            return False, f"Erro SSH: {str(e)}"
        except Exception as e:
            return False, f"Erro de conexão: {str(e)}"
    
    def list_remote_files(self, data):
        """Listar arquivos no servidor remoto"""
        try:
            # Sempre reconectar para garantir conexão ativa
            success, msg = self.connect_ssh(data)
            if not success:
                return False, msg
            
            remote_path = data['remote_path']
            
            # Executar comando ls
            stdin, stdout, stderr = self.ssh_client.exec_command(f"ls -lah {remote_path}")
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if error and "cannot access" in error.lower():
                return False, error
            
            # Adicionar informações extras
            result = f"Conteúdo de: {remote_path}\n"
            result += "=" * 60 + "\n\n"
            result += output
            
            # Contar arquivos
            lines = output.strip().split('\n')
            file_count = len([l for l in lines if l and not l.startswith('total')])
            result += f"\n\n✅ Total: {file_count} itens encontrados"
            
            return True, result
            
        except Exception as e:
            return False, f"Erro ao listar arquivos: {str(e)}"
    
    def verify_sql_file(self, data):
        """Verificar se arquivo SQL existe no servidor"""
        try:
            if not self.ssh_client:
                success, msg = self.connect_ssh(data)
                if not success:
                    return False, msg
            
            sql_file = data['sql_file']
            remote_path = data['remote_path']
            
            # Construir caminho completo
            if sql_file.startswith('/'):
                full_sql_path = sql_file
            else:
                full_sql_path = os.path.join(remote_path, sql_file).replace('\\', '/')
            
            # Verificar se arquivo existe
            check_cmd = f"test -f {full_sql_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
            stdin, stdout, stderr = self.ssh_client.exec_command(check_cmd)
            check_result = stdout.read().decode().strip()
            
            if check_result == 'NOT_FOUND':
                return False, f"Arquivo SQL não encontrado: {full_sql_path}"
            
            return True, full_sql_path
            
        except Exception as e:
            return False, f"Erro ao verificar SQL: {str(e)}"
    
    def import_sql(self, data):
        """Importar arquivo SQL no banco de dados"""
        try:
            # Sempre reconectar para garantir conexão fresca
            # Fechar conexão antiga se existir
            if self.ssh_client:
                try:
                    self.ssh_client.close()
                except:
                    pass
                self.ssh_client = None
            
            # Criar nova conexão
            success, msg = self.connect_ssh(data)
            if not success:
                return False, f"Erro de conexão:\n{msg}"
            
            username = data['username']
            password = data['password']
            db_name = data['db_name']
            sql_file = data['sql_file']
            remote_path = data['remote_path']
            
            # Construir caminho completo do SQL
            if sql_file.startswith('/'):
                full_sql_path = sql_file
            else:
                full_sql_path = os.path.join(remote_path, sql_file).replace('\\', '/')
            
            log = f"=== Iniciando Import SQL ===\n"
            log += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            log += f"Database: {db_name}\n"
            log += f"SQL File: {full_sql_path}\n\n"
            
            # Verificar se arquivo existe
            check_cmd = f"test -f {full_sql_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
            stdin, stdout, stderr = self.ssh_client.exec_command(check_cmd)
            check_result = stdout.read().decode().strip()
            
            if check_result == 'NOT_FOUND':
                log += f"❌ ERRO: Arquivo SQL não encontrado: {full_sql_path}\n"
                return False, log
            
            log += f"✅ Arquivo SQL encontrado\n\n"
            
            # Executar import MySQL com --no-defaults para evitar erros de config
            mysql_cmd = f"mysql --no-defaults -u {username} -p'{password}' {db_name} < {full_sql_path}"
            
            log += f"Executando comando:\nmysql --no-defaults -u {username} -p*** {db_name} < {full_sql_path}\n\n"
            
            # Usar timeout maior para import SQL
            stdin, stdout, stderr = self.ssh_client.exec_command(mysql_cmd, timeout=60)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            # Log de saída
            if output:
                log += f"=== STDOUT ===\n{output}\n\n"
            
            if error:
                log += f"=== STDERR ===\n{error}\n\n"
            
            # MySQL pode retornar warnings no stderr que não são erros fatais
            # Verificar se deu erro fatal (contém "ERROR")
            if "ERROR" in error.upper():
                log += "❌ Import falhou com erros\n"
                return False, log
            
            log += "✅ Import SQL concluído com sucesso!\n"
            
            return True, log
            
        except Exception as e:
            return False, f"Erro ao importar SQL:\n{str(e)}"
    
    def upload_files_with_progress(self, data, progress_callback=None):
        """
        Upload com callback de progresso usando SFTP (Paramiko)
        Mais lento que PSCP, mas permite feedback de progresso
        """
        try:
            # Conectar SSH se necessário
            if not self.ssh_client:
                success, msg = self.connect_ssh(data)
                if not success:
                    return False, msg
            
            # Abrir SFTP
            sftp = self.ssh_client.open_sftp()
            
            local_path = data['local_path']
            remote_path = data['remote_path']
            
            # Listar todos os arquivos
            files_to_upload = []
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file, local_path)
                    remote_file = os.path.join(remote_path, relative_path).replace('\\', '/')
                    files_to_upload.append((local_file, remote_file))
            
            total_files = len(files_to_upload)
            
            for idx, (local_file, remote_file) in enumerate(files_to_upload):
                # Criar diretórios remotos se necessário
                remote_dir = os.path.dirname(remote_file)
                self._create_remote_dir(sftp, remote_dir)
                
                # Upload do arquivo
                sftp.put(local_file, remote_file)
                
                # Callback de progresso
                if progress_callback:
                    progress = (idx + 1) / total_files * 100
                    filename = os.path.basename(local_file)
                    progress_callback(progress, f"Enviando: {filename}")
            
            sftp.close()
            return True, f"Upload concluído: {total_files} arquivos"
            
        except Exception as e:
            return False, f"Erro: {str(e)}"
    
    def _create_remote_dir(self, sftp, remote_dir):
        """Criar diretório remoto recursivamente"""
        if not remote_dir or remote_dir == '/':
            return
            
        dirs = []
        current = remote_dir
        
        while current and current != '/':
            dirs.append(current)
            current = os.path.dirname(current)
        
        dirs.reverse()
        
        for d in dirs:
            try:
                sftp.stat(d)
            except IOError:
                try:
                    sftp.mkdir(d)
                except:
                    pass  # Pode já existir
    
    def close(self):
        """Fechar conexões SSH/SFTP"""
        if self.sftp_client:
            try:
                self.sftp_client.close()
            except:
                pass
            self.sftp_client = None
            
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except:
                pass
            self.ssh_client = None
    
    def backup_files(self, data: dict) -> tuple:
        """
        Fazer backup dos arquivos PHP do servidor
        
        Args:
            data: Dicionário com host, username, password, remote_path, backup_local_path
        
        Returns:
            (success, log_message)
        """
        log = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_php_{timestamp}.tar.gz"
        remote_backup = f"/tmp/{backup_filename}"
        local_backup = os.path.join(data['backup_local_path'], backup_filename)
        
        try:
            log.append("🔄 Iniciando backup dos arquivos PHP...")
            
            # Conectar SSH
            success, msg = self.connect_ssh(data)
            if not success:
                log.append(f"❌ Erro de conexão: {msg}")
                return False, "\n".join(log)
            
            ssh = self.ssh_client
            
            # Criar arquivo tar.gz no servidor
            remote_path = data['remote_path'].rstrip('/')
            tar_command = f"tar -czf {remote_backup} -C {os.path.dirname(remote_path)} {os.path.basename(remote_path)}"
            
            log.append(f"📦 Compactando: {remote_path}")
            stdin, stdout, stderr = ssh.exec_command(tar_command, timeout=300)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code != 0:
                error = stderr.read().decode()
                log.append(f"❌ Erro ao compactar: {error}")
                return False, "\n".join(log)
            
            log.append(f"✅ Arquivo compactado: {remote_backup}")
            
            # Download via SFTP
            log.append(f"⬇️ Baixando para: {local_backup}")
            sftp = ssh.open_sftp()
            sftp.get(remote_backup, local_backup)
            sftp.close()
            
            file_size = os.path.getsize(local_backup) / (1024 * 1024)  # MB
            log.append(f"✅ Backup baixado com sucesso! ({file_size:.2f} MB)")
            
            # Remover arquivo temporário do servidor
            ssh.exec_command(f"rm {remote_backup}")
            log.append(f"🧹 Arquivo temporário removido do servidor")
            
            ssh.close()
            return True, "\n".join(log)
            
        except Exception as e:
            log.append(f"❌ Erro no backup de arquivos: {str(e)}")
            return False, "\n".join(log)
    
    def backup_database(self, data: dict) -> tuple:
        """
        Fazer backup (dump) do banco de dados
        
        Args:
            data: Dicionário com host, username, password, db_name, db_user, db_pass, backup_local_path
        
        Returns:
            (success, log_message)
        """
        log = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_db_{timestamp}.sql"
        remote_backup = f"/tmp/{backup_filename}"
        local_backup = os.path.join(data['backup_local_path'], backup_filename)
        
        try:
            log.append("🔄 Iniciando backup do banco de dados...")
            
            # Conectar SSH
            success, msg = self.connect_ssh(data)
            if not success:
                log.append(f"❌ Erro de conexão: {msg}")
                return False, "\n".join(log)
            
            ssh = self.ssh_client
            
            # Fazer dump do banco
            db_user = data.get('db_user', data['username'])
            db_pass = data.get('db_pass', data['password'])
            db_name = data['db_name']
            
            dump_command = f"mysqldump --no-defaults -u {db_user} -p'{db_pass}' {db_name} > {remote_backup}"
            
            log.append(f"💾 Exportando banco: {db_name}")
            stdin, stdout, stderr = ssh.exec_command(dump_command, timeout=300)
            exit_code = stdout.channel.recv_exit_status()
            
            if exit_code != 0:
                error = stderr.read().decode()
                log.append(f"❌ Erro ao exportar: {error}")
                return False, "\n".join(log)
            
            log.append(f"✅ Dump criado: {remote_backup}")
            
            # Download via SFTP
            log.append(f"⬇️ Baixando para: {local_backup}")
            sftp = ssh.open_sftp()
            sftp.get(remote_backup, local_backup)
            sftp.close()
            
            file_size = os.path.getsize(local_backup) / (1024 * 1024)  # MB
            log.append(f"✅ Backup baixado com sucesso! ({file_size:.2f} MB)")
            
            # Remover arquivo temporário do servidor
            ssh.exec_command(f"rm {remote_backup}")
            log.append(f"🧹 Arquivo temporário removido do servidor")
            
            ssh.close()
            return True, "\n".join(log)
            
        except Exception as e:
            log.append(f"❌ Erro no backup do banco: {str(e)}")
            return False, "\n".join(log)
