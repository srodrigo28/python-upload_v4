"""
Script de Teste - Verificação do Deploy
Testa conexão SSH e executa queries no banco de dados remoto
"""
import paramiko
import sys
from getpass import getpass


class DatabaseTester:
    """Testa conexão e estrutura do banco de dados remoto"""
    
    def __init__(self):
        self.ssh_client = None
        self.connection_data = {
            'host': '77.37.126.7',
            'port': 22,
            'username': 'srodrigo',
            'db_name': 'adv',
            'db_user': 'srodrigo'
        }
    
    def connect_ssh(self, password):
        """Conectar via SSH"""
        try:
            print("🔌 Conectando ao servidor...")
            
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.ssh_client.connect(
                hostname=self.connection_data['host'],
                port=self.connection_data['port'],
                username=self.connection_data['username'],
                password=password,
                timeout=10
            )
            
            print("✅ Conectado com sucesso!\n")
            return True
            
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def test_database_connection(self, db_password):
        """Testar conexão com banco de dados"""
        print("=" * 60)
        print("📊 TESTE 1: Conexão com Banco de Dados")
        print("=" * 60)
        
        try:
            cmd = f"mysql --no-defaults -u {self.connection_data['db_user']} -p'{db_password}' -e 'SELECT VERSION();'"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "ERROR" in error.upper():
                print(f"❌ Erro na conexão com MySQL:\n{error}")
                return False
            else:
                print(f"✅ Conexão com MySQL OK")
                print(f"Versão: {output.strip()}\n")
                return True
                
        except Exception as e:
            print(f"❌ Erro: {e}\n")
            return False
    
    def list_tables(self, db_password):
        """Listar todas as tabelas do banco"""
        print("=" * 60)
        print("📋 TESTE 2: Listar Tabelas")
        print("=" * 60)
        
        try:
            cmd = f"mysql --no-defaults -u {self.connection_data['db_user']} -p'{db_password}' {self.connection_data['db_name']} -e 'SHOW TABLES;'"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "ERROR" in error.upper():
                print(f"❌ Erro ao listar tabelas:\n{error}")
                return False
            
            lines = output.strip().split('\n')
            if len(lines) > 1:
                print(f"✅ Banco de dados '{self.connection_data['db_name']}' encontrado")
                print(f"Total de tabelas: {len(lines) - 1}\n")
                
                print("Tabelas encontradas:")
                for line in lines[1:]:  # Pular header
                    print(f"  • {line}")
                print()
                return True
            else:
                print(f"⚠️ Nenhuma tabela encontrada no banco '{self.connection_data['db_name']}'\n")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}\n")
            return False
    
    def test_table_structure(self, db_password, table_name='usuarios'):
        """Testar estrutura de uma tabela específica"""
        print("=" * 60)
        print(f"🔍 TESTE 3: Estrutura da Tabela '{table_name}'")
        print("=" * 60)
        
        try:
            cmd = f"mysql --no-defaults -u {self.connection_data['db_user']} -p'{db_password}' {self.connection_data['db_name']} -e 'DESCRIBE {table_name};'"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "ERROR" in error.upper():
                print(f"❌ Tabela '{table_name}' não existe ou erro:\n{error}")
                return False
            
            print(f"✅ Tabela '{table_name}' existe\n")
            print("Estrutura:")
            print(output)
            return True
                
        except Exception as e:
            print(f"❌ Erro: {e}\n")
            return False
    
    def count_records(self, db_password, table_name='usuarios'):
        """Contar registros em uma tabela"""
        print("=" * 60)
        print(f"📊 TESTE 4: Contagem de Registros em '{table_name}'")
        print("=" * 60)
        
        try:
            cmd = f"mysql --no-defaults -u {self.connection_data['db_user']} -p'{db_password}' {self.connection_data['db_name']} -e 'SELECT COUNT(*) as total FROM {table_name};'"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "ERROR" in error.upper():
                print(f"❌ Erro ao contar registros:\n{error}")
                return False
            
            lines = output.strip().split('\n')
            if len(lines) > 1:
                count = lines[1]
                print(f"✅ Total de registros: {count}\n")
                return True
            else:
                print(f"⚠️ Não foi possível contar registros\n")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}\n")
            return False
    
    def test_php_config_connection(self, db_password):
        """Testar se config.php pode conectar ao banco"""
        print("=" * 60)
        print("🔧 TESTE 5: Simulação de Conexão via PHP (config.php)")
        print("=" * 60)
        
        try:
            # Criar script PHP temporário para teste
            php_test = f"""<?php
try {{
    \\$dsn = "mysql:host=localhost;port=3306;dbname={self.connection_data['db_name']};charset=utf8mb4";
    \\$pdo = new PDO(\\$dsn, '{self.connection_data['db_user']}', '{db_password}', [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false
    ]);
    
    // Testar consulta
    \\$stmt = \\$pdo->query("SELECT COUNT(*) as total FROM usuarios");
    \\$result = \\$stmt->fetch();
    
    echo "SUCCESS: Conexao OK - Usuarios: " . \\$result['total'];
}} catch (PDOException \\$e) {{
    echo "ERROR: " . \\$e->getMessage();
}}
?>"""
            
            # Enviar script para servidor
            sftp = self.ssh_client.open_sftp()
            temp_file = '/tmp/test_db_connection.php'
            
            with sftp.open(temp_file, 'w') as f:
                f.write(php_test)
            
            # Executar script PHP
            cmd = f"php {temp_file}"
            stdin, stdout, stderr = self.ssh_client.exec_command(cmd)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            # Remover arquivo temporário
            sftp.remove(temp_file)
            sftp.close()
            
            if "SUCCESS" in output:
                print(f"✅ {output}\n")
                print("✅ O config.php conseguirá conectar ao banco de dados!")
                return True
            elif "ERROR" in output:
                print(f"❌ {output}\n")
                print("❌ O config.php NÃO conseguirá conectar")
                print("\nPossíveis soluções:")
                print("  1. Verifique as credenciais no config/database.php")
                print("  2. Garanta que o usuário MySQL tem permissões")
                print("  3. Execute: GRANT ALL PRIVILEGES ON adv.* TO 'srodrigo'@'localhost';")
                return False
            else:
                print(f"⚠️ Resposta inesperada:\n{output}")
                if error:
                    print(f"Erro PHP: {error}")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}\n")
            return False
    
    def run_all_tests(self, ssh_password, db_password):
        """Executar todos os testes"""
        print("\n" + "=" * 60)
        print("🚀 INICIANDO TESTES DE DEPLOY")
        print("=" * 60 + "\n")
        
        results = {}
        
        # Teste 1: Conexão SSH
        if not self.connect_ssh(ssh_password):
            print("\n❌ Falha na conexão SSH. Testes abortados.")
            return
        
        # Teste 2: Conexão MySQL
        results['mysql_connection'] = self.test_database_connection(db_password)
        
        if not results['mysql_connection']:
            print("\n❌ Não foi possível conectar ao MySQL. Verifique as credenciais.")
            self.close()
            return
        
        # Teste 3: Listar tabelas
        results['list_tables'] = self.list_tables(db_password)
        
        # Teste 4: Estrutura de tabela
        results['table_structure'] = self.test_table_structure(db_password, 'usuarios')
        
        # Teste 5: Contar registros
        results['count_records'] = self.count_records(db_password, 'usuarios')
        
        # Teste 6: Teste de conexão PHP
        results['php_connection'] = self.test_php_config_connection(db_password)
        
        # Resumo
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for v in results.values() if v)
        
        for test_name, passed in results.items():
            status = "✅ PASSOU" if passed else "❌ FALHOU"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nTotal: {passed_tests}/{total_tests} testes passaram")
        
        if passed_tests == total_tests:
            print("\n🎉 TODOS OS TESTES PASSARAM! Deploy OK!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} teste(s) falharam. Verifique os erros acima.")
        
        self.close()
    
    def close(self):
        """Fechar conexão SSH"""
        if self.ssh_client:
            self.ssh_client.close()
            print("\n🔌 Conexão SSH encerrada")


def main():
    """Função principal"""
    print("=" * 60)
    print("🔬 SCRIPT DE TESTE - DEPLOY WIZARD")
    print("=" * 60)
    print("\nEste script testa se o deploy foi bem-sucedido")
    print("e se o banco de dados está acessível.\n")
    
    tester = DatabaseTester()
    
    print(f"Servidor: {tester.connection_data['host']}")
    print(f"Usuário SSH: {tester.connection_data['username']}")
    print(f"Banco de dados: {tester.connection_data['db_name']}\n")
    
    # Solicitar senhas
    ssh_password = getpass("Digite a senha SSH: ")
    db_password = getpass("Digite a senha do MySQL: ")
    
    # Executar testes
    tester.run_all_tests(ssh_password, db_password)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Testes cancelados pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro crítico: {e}")
        sys.exit(1)
