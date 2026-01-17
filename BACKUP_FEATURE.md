# 🔄 Implementação de Backup Automático

## 📋 Visão Geral

Adicionar funcionalidade de backup automático antes do deploy, incluindo:
- **Backup dos arquivos PHP** do servidor
- **Backup do banco de dados** (dump SQL)
- **Download automático** dos backups
- **Feedback visual** durante todo o processo
- **Novo fluxo**: Backup → Download → Upload → Import

---

## 🎯 Nova Estrutura do Wizard

### Antes (3 passos):
1. 📤 Upload de Arquivos
2. ✅ Verificação
3. 🗄️ Import SQL

### Depois (5 passos):
1. ⚙️ **Configuração** (dados de conexão)
2. 💾 **Backup** (PHP + SQL)
3. 📤 **Upload** de Arquivos
4. ✅ **Verificação**
5. 🗄️ **Import SQL**

---

## 🛠️ Passo a Passo de Implementação

### 📁 Etapa 1: Atualizar `deploy.py`

Adicionar novos métodos para backup:

```python
def backup_files(self, data: dict) -> tuple[bool, str]:
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
        ssh = self.connect_ssh(data['host'], data['port'], data['username'], data['password'])
        
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


def backup_database(self, data: dict) -> tuple[bool, str]:
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
        ssh = self.connect_ssh(data['host'], data['port'], data['username'], data['password'])
        
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
```

---

### 📄 Etapa 2: Atualizar `main.py`

#### 2.1 Adicionar novo campo no `__init__`:

```python
self.data = {
    'local_path': r'C:\xampp\htdocs\www\v2\juridico-php',
    'backup_local_path': r'C:\backups\deploy_wizard',  # NOVO
    'host': '77.37.126.7',
    'port': '22',
    'username': 'srodrigo',
    'password': '@dV#sRnAt98!',
    'remote_path': '/var/www/adv/',
    'db_name': 'adv',
    'db_user': 'srodrigo',  # NOVO
    'db_pass': '@dV#sRnAt98!',  # NOVO
    'sql_file': 'scripts/criar_new_db.sql'
}
```

#### 2.2 Atualizar `create_pages()`:

```python
def create_pages(self):
    """Criar todas as páginas do wizard"""
    self.pages = []
    self.pages.append(self.create_page_config())      # Passo 1: Configuração
    self.pages.append(self.create_page_backup())      # Passo 2: Backup (NOVO)
    self.pages.append(self.create_page_upload())      # Passo 3: Upload
    self.pages.append(self.create_page_verification()) # Passo 4: Verificação
    self.pages.append(self.create_page_import())      # Passo 5: Import
    
    # Mostrar primeira página
    self.show_page(0)
```

#### 2.3 Criar página de configuração (`create_page_config`):

```python
def create_page_config(self):
    """Página 1: Configuração"""
    page = ttk.Frame(self.pages_container)
    
    # Título
    ttk.Label(
        page,
        text="⚙️ Configuração do Deploy",
        font=("Segoe UI", 16, "bold"),
        bootstyle="info"
    ).pack(pady=(0, 20))
    
    # Frame do formulário
    form = ttk.Frame(page)
    form.pack(fill=BOTH, expand=True)
    
    # Local Path (pasta do projeto)
    ttk.Label(form, text="📁 Local Path:", font=("Segoe UI", 10, "bold")).grid(
        row=0, column=0, sticky=W, pady=8, padx=(0, 10)
    )
    path_frame = ttk.Frame(form)
    path_frame.grid(row=0, column=1, sticky=EW, pady=8)
    
    self.entry_local_path = ttk.Entry(path_frame, width=50)
    self.entry_local_path.pack(side=LEFT, fill=X, expand=True)
    self.entry_local_path.insert(0, self.data['local_path'])
    
    ttk.Button(
        path_frame,
        text="Browse...",
        command=self.browse_folder,
        bootstyle="info-outline",
        width=12
    ).pack(side=LEFT, padx=(5, 0))
    
    # Backup Path (onde salvar backups)
    ttk.Label(form, text="💾 Backup Path:", font=("Segoe UI", 10, "bold")).grid(
        row=1, column=0, sticky=W, pady=8, padx=(0, 10)
    )
    backup_frame = ttk.Frame(form)
    backup_frame.grid(row=1, column=1, sticky=EW, pady=8)
    
    self.entry_backup_path = ttk.Entry(backup_frame, width=50)
    self.entry_backup_path.pack(side=LEFT, fill=X, expand=True)
    self.entry_backup_path.insert(0, self.data['backup_local_path'])
    
    ttk.Button(
        backup_frame,
        text="Browse...",
        command=self.browse_backup_folder,
        bootstyle="info-outline",
        width=12
    ).pack(side=LEFT, padx=(5, 0))
    
    # Host e Port
    host_port_frame = ttk.Frame(form)
    host_port_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=8)
    
    ttk.Label(host_port_frame, text="Host:", font=("Segoe UI", 10, "bold")).pack(
        side=LEFT, padx=(0, 10)
    )
    self.entry_host = ttk.Entry(host_port_frame, width=30)
    self.entry_host.pack(side=LEFT, fill=X, expand=True)
    self.entry_host.insert(0, self.data['host'])
    
    ttk.Label(host_port_frame, text="Port:", font=("Segoe UI", 10, "bold")).pack(
        side=LEFT, padx=(20, 10)
    )
    self.entry_port = ttk.Entry(host_port_frame, width=10)
    self.entry_port.pack(side=LEFT)
    self.entry_port.insert(0, self.data['port'])
    
    # Username e Password
    user_pass_frame = ttk.Frame(form)
    user_pass_frame.grid(row=3, column=0, columnspan=2, sticky=EW, pady=8)
    
    ttk.Label(user_pass_frame, text="Username:", font=("Segoe UI", 10, "bold")).pack(
        side=LEFT, padx=(0, 10)
    )
    self.entry_username = ttk.Entry(user_pass_frame, width=20)
    self.entry_username.pack(side=LEFT, fill=X, expand=True)
    self.entry_username.insert(0, self.data['username'])
    
    ttk.Label(user_pass_frame, text="Password:", font=("Segoe UI", 10, "bold")).pack(
        side=LEFT, padx=(20, 10)
    )
    
    password_inner_frame = ttk.Frame(user_pass_frame)
    password_inner_frame.pack(side=LEFT, fill=X, expand=True)
    
    self.entry_password = ttk.Entry(password_inner_frame, show="•")
    self.entry_password.pack(side=LEFT, fill=X, expand=True)
    self.entry_password.insert(0, self.data['password'])
    
    ttk.Button(
        password_inner_frame,
        text="👁️",
        command=self.toggle_password_visibility,
        bootstyle="info-outline",
        width=3
    ).pack(side=LEFT, padx=(5, 0))
    
    # Remote Path
    ttk.Label(form, text="Remote Path:", font=("Segoe UI", 10, "bold")).grid(
        row=4, column=0, sticky=W, pady=8, padx=(0, 10)
    )
    self.entry_remote_path = ttk.Entry(form, width=50)
    self.entry_remote_path.grid(row=4, column=1, sticky=EW, pady=8)
    self.entry_remote_path.insert(0, self.data['remote_path'])
    
    # Database Name
    ttk.Label(form, text="Database:", font=("Segoe UI", 10, "bold")).grid(
        row=5, column=0, sticky=W, pady=8, padx=(0, 10)
    )
    self.entry_db_name = ttk.Entry(form, width=50)
    self.entry_db_name.grid(row=5, column=1, sticky=EW, pady=8)
    self.entry_db_name.insert(0, self.data['db_name'])
    
    form.columnconfigure(1, weight=1)
    
    # Status
    self.status_config = ttk.Label(
        page,
        text="✅ Configuração carregada",
        font=("Segoe UI", 10),
        bootstyle="success"
    )
    self.status_config.pack(pady=20)
    
    return page
```

#### 2.4 Criar página de backup (`create_page_backup`):

```python
def create_page_backup(self):
    """Página 2: Backup"""
    page = ttk.Frame(self.pages_container)
    
    # Título
    ttk.Label(
        page,
        text="💾 Backup Automático",
        font=("Segoe UI", 16, "bold"),
        bootstyle="warning"
    ).pack(pady=(0, 20))
    
    # Descrição
    desc = ttk.Label(
        page,
        text="Antes de fazer o deploy, vamos criar backup de segurança:\n"
             "• Arquivos PHP atuais do servidor\n"
             "• Banco de dados atual",
        font=("Segoe UI", 10),
        bootstyle="inverse-secondary",
        justify="center"
    )
    desc.pack(pady=10)
    
    # Frame para botões de backup
    buttons_frame = ttk.Frame(page)
    buttons_frame.pack(pady=30)
    
    # Botão: Backup Arquivos
    self.btn_backup_files = ttk.Button(
        buttons_frame,
        text="📦 Backup Arquivos PHP",
        command=self.execute_backup_files,
        bootstyle="warning",
        width=25
    )
    self.btn_backup_files.pack(pady=10)
    
    # Status backup arquivos
    self.status_backup_files = ttk.Label(
        buttons_frame,
        text="⏳ Aguardando...",
        font=("Segoe UI", 10)
    )
    self.status_backup_files.pack(pady=5)
    
    # Botão: Backup Database
    self.btn_backup_db = ttk.Button(
        buttons_frame,
        text="🗄️ Backup Banco de Dados",
        command=self.execute_backup_database,
        bootstyle="warning",
        width=25
    )
    self.btn_backup_db.pack(pady=10)
    
    # Status backup database
    self.status_backup_db = ttk.Label(
        buttons_frame,
        text="⏳ Aguardando...",
        font=("Segoe UI", 10)
    )
    self.status_backup_db.pack(pady=5)
    
    # Separador
    ttk.Separator(page, orient=HORIZONTAL).pack(fill=X, pady=20)
    
    # Log de backup
    ttk.Label(
        page,
        text="📋 Log de Backup:",
        font=("Segoe UI", 11, "bold")
    ).pack(anchor=W, pady=(10, 5))
    
    log_frame = ttk.Frame(page)
    log_frame.pack(fill=BOTH, expand=True, pady=10)
    
    scrollbar = ttk.Scrollbar(log_frame)
    scrollbar.pack(side=RIGHT, fill=Y)
    
    self.backup_log_text = tk.Text(
        log_frame,
        height=10,
        wrap=WORD,
        yscrollcommand=scrollbar.set,
        font=("Consolas", 9),
        bg="#1a1a1a",
        fg="#00ff00"
    )
    self.backup_log_text.pack(side=LEFT, fill=BOTH, expand=True)
    scrollbar.config(command=self.backup_log_text.yview)
    
    # Progress bar
    self.backup_progress = ttk.Progressbar(
        page,
        mode='indeterminate',
        bootstyle="warning-striped"
    )
    self.backup_progress.pack(fill=X, pady=10)
    
    return page
```

#### 2.5 Adicionar métodos de execução de backup:

```python
def execute_backup_files(self):
    """Executar backup de arquivos"""
    self.backup_progress.start()
    self.btn_backup_files.config(state="disabled")
    self.status_backup_files.config(text="🔄 Fazendo backup...", bootstyle="warning")
    
    # Criar pasta de backup se não existir
    backup_path = self.entry_backup_path.get()
    os.makedirs(backup_path, exist_ok=True)
    
    def backup_thread():
        self.data['backup_local_path'] = backup_path
        success, log = self.deploy_manager.backup_files(self.data)
        self.root.after(0, lambda: self.on_backup_files_complete(success, log))
    
    thread = threading.Thread(target=backup_thread, daemon=True)
    thread.start()

def on_backup_files_complete(self, success, log):
    """Callback quando backup de arquivos termina"""
    self.backup_progress.stop()
    self.backup_log_text.insert(END, log + "\n\n")
    self.backup_log_text.see(END)
    
    if success:
        self.status_backup_files.config(
            text="✅ Backup concluído!",
            bootstyle="success"
        )
        messagebox.showinfo(
            "Backup Concluído",
            "🎉 Backup dos arquivos PHP foi gerado com segurança!\n\n"
            f"📁 Localização: {self.data['backup_local_path']}\n\n"
            "Agora você pode continuar com o deploy."
        )
    else:
        self.status_backup_files.config(text="❌ Erro no backup", bootstyle="danger")
        messagebox.showerror("Erro", "Falha ao fazer backup dos arquivos.")
    
    self.btn_backup_files.config(state="normal")

def execute_backup_database(self):
    """Executar backup do banco"""
    self.backup_progress.start()
    self.btn_backup_db.config(state="disabled")
    self.status_backup_db.config(text="🔄 Fazendo backup...", bootstyle="warning")
    
    # Criar pasta de backup se não existir
    backup_path = self.entry_backup_path.get()
    os.makedirs(backup_path, exist_ok=True)
    
    def backup_thread():
        self.data['backup_local_path'] = backup_path
        self.data['db_name'] = self.entry_db_name.get()
        success, log = self.deploy_manager.backup_database(self.data)
        self.root.after(0, lambda: self.on_backup_database_complete(success, log))
    
    thread = threading.Thread(target=backup_thread, daemon=True)
    thread.start()

def on_backup_database_complete(self, success, log):
    """Callback quando backup do banco termina"""
    self.backup_progress.stop()
    self.backup_log_text.insert(END, log + "\n\n")
    self.backup_log_text.see(END)
    
    if success:
        self.status_backup_db.config(
            text="✅ Backup concluído!",
            bootstyle="success"
        )
        messagebox.showinfo(
            "Backup Concluído",
            "🎉 Backup do banco de dados foi gerado com segurança!\n\n"
            f"📁 Localização: {self.data['backup_local_path']}\n\n"
            "✨ Agora vamos subir as atualizações!"
        )
    else:
        self.status_backup_db.config(text="❌ Erro no backup", bootstyle="danger")
        messagebox.showerror("Erro", "Falha ao fazer backup do banco.")
    
    self.btn_backup_db.config(state="normal")

def browse_backup_folder(self):
    """Selecionar pasta para backups"""
    folder = filedialog.askdirectory(
        title="Selecione a pasta para backups",
        initialdir=self.entry_backup_path.get()
    )
    if folder:
        self.entry_backup_path.delete(0, END)
        self.entry_backup_path.insert(0, folder)
```

#### 2.6 Atualizar navegação de passos:

```python
def validate_config(self):
    """Validar configurações antes de prosseguir"""
    local_path = self.entry_local_path.get()
    backup_path = self.entry_backup_path.get()
    host = self.entry_host.get()
    port = self.entry_port.get()
    username = self.entry_username.get()
    password = self.entry_password.get()
    remote_path = self.entry_remote_path.get()
    db_name = self.entry_db_name.get()
    
    if not local_path or not os.path.exists(local_path):
        messagebox.showerror("Erro", "Pasta local não existe!")
        return False
    
    if not backup_path:
        messagebox.showerror("Erro", "Pasta de backup não definida!")
        return False
    
    if not host or not port or not username or not password:
        messagebox.showerror("Erro", "Preencha todos os campos de conexão!")
        return False
    
    if not remote_path or not db_name:
        messagebox.showerror("Erro", "Preencha Remote Path e Database!")
        return False
    
    # Salvar dados
    self.data['local_path'] = local_path
    self.data['backup_local_path'] = backup_path
    self.data['host'] = host
    self.data['port'] = port
    self.data['username'] = username
    self.data['password'] = password
    self.data['remote_path'] = remote_path
    self.data['db_name'] = db_name
    
    return True

def next_step(self):
    """Ir para próximo passo"""
    # Validações específicas por passo
    if self.current_step == 0:  # Configuração
        if not self.validate_config():
            return
    elif self.current_step == 2:  # Upload
        if not self.validate_upload():
            return
    
    # Avançar
    if self.current_step < len(self.pages) - 1:
        self.current_step += 1
        self.show_page(self.current_step)
```

---

### 🔄 Etapa 3: Adicionar import datetime no `deploy.py`

```python
from datetime import datetime
```

---

### 📝 Etapa 4: Atualizar validações

Remover as validações repetidas da página de upload, já que agora temos uma página de configuração dedicada.

---

### ✅ Etapa 5: Testar o Fluxo Completo

1. **Executar aplicação**: `python main.py`
2. **Passo 1 - Configuração**: Preencher dados e avançar
3. **Passo 2 - Backup**: 
   - Clicar "Backup Arquivos PHP"
   - Ver mensagem de sucesso
   - Clicar "Backup Banco de Dados"
   - Ver mensagem de sucesso
   - Avançar para upload
4. **Passo 3 - Upload**: Fazer upload normal
5. **Passo 4 - Verificação**: Verificar arquivos
6. **Passo 5 - Import**: Importar banco

---

## 🎨 Feedback Visual Implementado

### Mensagens de Sucesso:

**Após backup de arquivos:**
```
🎉 Backup dos arquivos PHP foi gerado com segurança!

📁 Localização: C:\backups\deploy_wizard

Agora você pode continuar com o deploy.
```

**Após backup do banco:**
```
🎉 Backup do banco de dados foi gerado com segurança!

📁 Localização: C:\backups\deploy_wizard

✨ Agora vamos subir as atualizações!
```

### Logs em tempo real:
- 🔄 Iniciando backup...
- 📦 Compactando arquivos...
- ⬇️ Baixando para disco local...
- ✅ Backup concluído com sucesso!

---

## 📦 Estrutura de Arquivos de Backup

Os backups são salvos com timestamp:

```
C:\backups\deploy_wizard\
├── backup_php_20260112_143052.tar.gz    (arquivos PHP)
├── backup_db_20260112_143125.sql        (dump do banco)
├── backup_php_20260112_151430.tar.gz
└── backup_db_20260112_151502.sql
```

---

## 🚀 Benefícios da Implementação

1. ✅ **Segurança**: Backup automático antes de qualquer alteração
2. ✅ **Rastreabilidade**: Backups com timestamp para histórico
3. ✅ **Reversão rápida**: Arquivos prontos para restauração
4. ✅ **Feedback claro**: Usuário sabe exatamente o que está acontecendo
5. ✅ **Separação de responsabilidades**: Backup PHP e SQL independentes
6. ✅ **Download local**: Backups salvos localmente para segurança extra

---

## 🎯 Melhorias Futuras (Opcionais)

1. **Auto-restore**: Botão para restaurar backup anterior
2. **Limpeza automática**: Remover backups com mais de X dias
3. **Compressão SQL**: Comprimir dump SQL com gzip
4. **Backup incremental**: Apenas arquivos modificados
5. **Histórico visual**: Lista de todos os backups com botão de restaurar
6. **Validação de backup**: Testar integridade dos arquivos baixados

---

## 📋 Checklist de Implementação

- [ ] Atualizar `deploy.py` com métodos `backup_files()` e `backup_database()`
- [ ] Adicionar campo `backup_local_path` no `__init__` do `main.py`
- [ ] Criar método `create_page_config()` no `main.py`
- [ ] Criar método `create_page_backup()` no `main.py`
- [ ] Adicionar métodos `execute_backup_files()` e `execute_backup_database()`
- [ ] Adicionar callbacks `on_backup_files_complete()` e `on_backup_database_complete()`
- [ ] Adicionar método `browse_backup_folder()`
- [ ] Atualizar método `create_pages()` para incluir as 5 páginas
- [ ] Adicionar validação `validate_config()`
- [ ] Atualizar `next_step()` para validar cada passo
- [ ] Adicionar `from datetime import datetime` no `deploy.py`
- [ ] Testar fluxo completo
- [ ] Documentar no README.md

---

## 🎉 Resultado Final

Aplicação com fluxo completo e seguro:
1. ⚙️ Configurar conexão e caminhos
2. 💾 Fazer backup de segurança (PHP + SQL)
3. 📤 Upload dos arquivos atualizados
4. ✅ Verificar integridade
5. 🗄️ Importar novo banco de dados

**Tudo com feedback visual top e backups salvos localmente!** 🚀
