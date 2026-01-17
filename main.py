"""
Deploy Wizard - Interface Gráfica Principal (customtkinter)
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox, END
import os
import threading
from validators import Validators
from deploy import DeployManager
from config_manager import ConfigManager


class DeployWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("Deploy V-4")
        # reduzir altura inicial para evitar corte em telas baixas
        self.root.geometry("700x720")
        # permitir redimensionamento
        try:
            self.root.minsize(640, 480)
            self.root.resizable(True, True)
        except Exception:
            pass
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.current_step = 0
        self.config_manager = ConfigManager()
        self.deploy_manager = DeployManager()
        self.validators = Validators()

        # Flags de controle
        self.backup_files_done = False
        self.backup_db_done = False

        # Variáveis para armazenar dados
        self.data = {
            'local_path': r'C:\xampp\htdocs\www\v2\juridico-php',
            'backup_local_path': r'C:\backups\deploy_wizard',
            'host': '77.37.126.7',
            'port': '22',
            'username': 'srodrigo',
            'password': '@dV#sRnAt98!',
            'remote_path': '/var/www/adv.precifex.com/',
            'db_name': 'adv',
            'db_user': 'srodrigo',
            'db_pass': '@dV#sRnAt98!',
            'sql_file': 'scripts/criar_new_db.sql',
            'import_sql': 'Sim'
        }

        # storage for indeterminate progress tasks
        self._progress_tasks = {}
        self._closing = False

        # iniciar colapsado para evitar corte vertical
        self.dir_expanded = False
        # iniciar servidor colapsado
        self.server_expanded = False

        self.setup_ui()
        self.load_last_config()

    # --- Progress helpers ---
    def _start_progress(self, widget):
        wid = id(widget)
        self._progress_tasks[wid] = True

        if not hasattr(widget, "_value"):
            widget._value = 0.0

        def step():
            if not self._progress_tasks.get(wid) or self._closing:
                return
            widget._value = (widget._value + 0.02) % 1.0
            try:
                widget.set(widget._value)
            except Exception:
                pass
            self.safe_after(80, step)

        step()

    def _stop_progress(self, widget):
        wid = id(widget)
        self._progress_tasks[wid] = False
        try:
            widget.set(0.0)
            widget._value = 0.0
        except Exception:
            pass

    def safe_after(self, ms, func):
        """Schedule `func` with `after` only if app isn't closing."""
        if getattr(self, '_closing', False):
            return
        try:
            self.root.after(ms, func)
        except Exception:
            pass

    # --- UI ---
    def setup_ui(self):
        # Header
        self.header = ctk.CTkFrame(self.root)
        self.header.pack(fill="x", padx=0, pady=0)

        # cabeçalho simples sem imagem/título grande
        self.subtitle_label = ctk.CTkLabel(self.header, text="4 passos: Conexao e Backup → Upload → Verificação → Import SQL", font=("Segoe UI", 12, "bold"))
        self.subtitle_label.pack(pady=(12, 12))

        # Container para páginas (rolável se disponível)
        try:
            self.pages_container = ctk.CTkScrollableFrame(self.root)
        except Exception:
            self.pages_container = ctk.CTkFrame(self.root)
        self.pages_container.pack(fill="both", expand=True, padx=16, pady=8)

        # Footer
        self.footer = ctk.CTkFrame(self.root)
        self.footer.pack(side="bottom", fill="x", padx=16, pady=12)

        self.btn_back = ctk.CTkButton(self.footer, text="← Voltar", command=self.previous_step, width=120)
        self.btn_back.pack(side="left")

        self.btn_save_config = ctk.CTkButton(self.footer, text="💾 Salvar Config", command=self.save_current_config, width=120)
        self.btn_save_config.pack(side="left", padx=(10, 0))

        self.btn_next = ctk.CTkButton(self.footer, text="Próximo →", command=self.next_step, width=120)
        self.btn_next.pack(side="right")

        self.create_pages()
        self.show_page(0)

    def create_pages(self):
        self.pages = []
        self.pages.append(self.create_page_config())
        self.pages.append(self.create_page_backup())
        self.pages.append(self.create_page_upload())
        self.pages.append(self.create_page_verification())
        self.pages.append(self.create_page_import())

    def create_page_config(self):
        page = ctk.CTkFrame(self.pages_container)

        ctk.CTkLabel(page, text="⚙️ Backup, Upload e Deploy", font=("Segoe UI", 16, "bold"), text_color="#8B5CF6").pack(pady=(0, 18))

        container = ctk.CTkFrame(page)
        container.pack(fill="both", expand=True, padx=20, pady=6)

        form = ctk.CTkFrame(container)
        form.pack(fill="x")

        # Diretórios colapsável
        self.dir_toggle = ctk.CTkButton(form, text="📂 Diretórios ▾", command=self.toggle_directories)
        self.dir_toggle.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.directories_frame = ctk.CTkFrame(form)
        self.directories_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        ctk.CTkLabel(self.directories_frame, text="Local Path:", font=("Segoe UI", 10)).pack(anchor="w", pady=6, padx=(10, 15))
        path_frame = ctk.CTkFrame(self.directories_frame)
        path_frame.pack(fill="x", pady=4, padx=(10, 0))
        self.entry_local_path = ctk.CTkEntry(path_frame, font=("Segoe UI", 9))
        self.entry_local_path.pack(side="left", fill="x", expand=True)
        self.entry_local_path.insert(0, self.data['local_path'])
        ctk.CTkButton(path_frame, text="📁", command=self.browse_folder, width=32).pack(side="left", padx=(6, 0))

        ctk.CTkLabel(self.directories_frame, text="Backup Path:", font=("Segoe UI", 10)).pack(anchor="w", pady=6, padx=(10, 15))
        backup_frame = ctk.CTkFrame(self.directories_frame)
        backup_frame.pack(fill="x", pady=4, padx=(10, 0))
        self.entry_backup_path = ctk.CTkEntry(backup_frame, font=("Segoe UI", 9))
        self.entry_backup_path.pack(side="left", fill="x", expand=True)
        self.entry_backup_path.insert(0, self.data['backup_local_path'])
        ctk.CTkButton(backup_frame, text="💾", command=self.browse_backup_folder, width=32).pack(side="left", padx=(6, 0))

        # esconder diretórios se iniciado colapsado
        if not self.dir_expanded:
            try:
                self.directories_frame.grid_remove()
            except Exception:
                try:
                    self.directories_frame.pack_forget()
                except Exception:
                    pass
            try:
                self.dir_toggle.configure(text="📂 Diretórios ▸")
            except Exception:
                pass

        sep = ctk.CTkFrame(form, height=2, fg_color="#444444")
        sep.grid(row=2, column=0, columnspan=2, sticky="ew", pady=14)

        # Conexão (colapsável)
        self.server_toggle = ctk.CTkButton(form, text="🌐 Servidor ▾", command=self.toggle_server)
        self.server_toggle.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 8))

        # Frame interno para campos do servidor
        self.server_frame = ctk.CTkFrame(form)
        self.server_frame.grid(row=4, column=0, columnspan=2, sticky="ew")

        ctk.CTkLabel(self.server_frame, text="Conexão:", font=("Segoe UI", 10)).pack(anchor="w", pady=6, padx=(10, 15))
        host_port_frame = ctk.CTkFrame(self.server_frame)
        host_port_frame.pack(fill="x", pady=4, padx=(10, 0))
        self.entry_host = ctk.CTkEntry(host_port_frame, font=("Segoe UI", 9))
        self.entry_host.pack(side="left", fill="x", expand=True)
        self.entry_host.insert(0, self.data['host'])
        ctk.CTkLabel(host_port_frame, text=":", font=("Segoe UI", 10, "bold")).pack(side="left", padx=6)
        self.entry_port = ctk.CTkEntry(host_port_frame, width=80, font=("Segoe UI", 9))
        self.entry_port.pack(side="left")
        self.entry_port.insert(0, self.data['port'])

        ctk.CTkLabel(self.server_frame, text="Credenciais:", font=("Segoe UI", 10)).pack(anchor="w", pady=6, padx=(10, 15))
        user_pass_frame = ctk.CTkFrame(self.server_frame)
        user_pass_frame.pack(fill="x", pady=4, padx=(10, 0))
        self.entry_username = ctk.CTkEntry(user_pass_frame, font=("Segoe UI", 9))
        self.entry_username.pack(side="left", fill="x", expand=True)
        self.entry_username.insert(0, self.data['username'])
        ctk.CTkLabel(user_pass_frame, text="@", font=("Segoe UI", 10, "bold")).pack(side="left", padx=6)
        password_inner_frame = ctk.CTkFrame(user_pass_frame)
        password_inner_frame.pack(side="left", fill="x", expand=True)
        self.entry_password = ctk.CTkEntry(password_inner_frame, show="•", font=("Segoe UI", 9))
        self.entry_password.pack(side="left", fill="x", expand=True)
        self.entry_password.insert(0, self.data['password'])
        ctk.CTkButton(password_inner_frame, text="👁", command=self.toggle_password_visibility, width=32).pack(side="left", padx=(6, 0))

        # esconder servidor se iniciado colapsado
        if not getattr(self, 'server_expanded', False):
            try:
                self.server_frame.grid_remove()
            except Exception:
                try:
                    self.server_frame.pack_forget()
                except Exception:
                    pass
            try:
                self.server_toggle.configure(text="🌐 Servidor ▸")
            except Exception:
                pass

        sep2 = ctk.CTkFrame(form, height=2, fg_color="#444444")
        sep2.grid(row=6, column=0, columnspan=2, sticky="ew", pady=14)

        # Deploy
        ctk.CTkLabel(form, text="🚀 Deploy", font=("Segoe UI", 11, "bold"), text_color="#8B5CF6").grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ctk.CTkLabel(form, text="Destino:", font=("Segoe UI", 10)).grid(row=8, column=0, sticky="w", pady=8, padx=(10, 15))
        remote_db_frame = ctk.CTkFrame(form)
        remote_db_frame.grid(row=8, column=1, sticky="ew", pady=8)
        self.entry_remote_path = ctk.CTkEntry(remote_db_frame, font=("Segoe UI", 9))
        self.entry_remote_path.pack(side="left", fill="x", expand=True)
        self.entry_remote_path.insert(0, self.data['remote_path'])
        ctk.CTkLabel(remote_db_frame, text="DB:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=8)
        self.entry_db_name = ctk.CTkEntry(remote_db_frame, width=120, font=("Segoe UI", 9))
        self.entry_db_name.pack(side="left")
        self.entry_db_name.insert(0, self.data['db_name'])

        # Opção de SQL Opcional (Radio Buttons)
        ctk.CTkLabel(form, text="Importar Banco?", font=("Segoe UI", 10, "bold")).grid(row=9, column=0, sticky="w", pady=8, padx=(10, 15))
        sql_radio_frame = ctk.CTkFrame(form, fg_color="transparent")
        sql_radio_frame.grid(row=9, column=1, sticky="w", pady=8)
        
        self.sql_var = ctk.StringVar(value=self.data.get('import_sql', 'Sim'))
        self.rb_sql_yes = ctk.CTkRadioButton(sql_radio_frame, text="Sim", variable=self.sql_var, value="Sim", command=self.toggle_sql_entry)
        self.rb_sql_yes.pack(side="left", padx=(0, 20))
        self.rb_sql_no = ctk.CTkRadioButton(sql_radio_frame, text="Não", variable=self.sql_var, value="Não", command=self.toggle_sql_entry)
        self.rb_sql_no.pack(side="left")

        self.label_sql_file = ctk.CTkLabel(form, text="SQL File:", font=("Segoe UI", 10))
        self.label_sql_file.grid(row=10, column=0, sticky="w", pady=8, padx=(10, 15))
        self.sql_entry_frame = ctk.CTkFrame(form)
        self.sql_entry_frame.grid(row=10, column=1, sticky="ew", pady=8)
        self.entry_sql_file = ctk.CTkEntry(self.sql_entry_frame, font=("Segoe UI", 9))
        self.entry_sql_file.pack(side="left", fill="x", expand=True)
        self.entry_sql_file.insert(0, self.data['sql_file'])
        self.btn_browse_sql = ctk.CTkButton(self.sql_entry_frame, text="📄", command=self.browse_sql_file, width=32)
        self.btn_browse_sql.pack(side="left", padx=(6, 0))

        # Chamar toggle no início para garantir estado correto
        self.toggle_sql_entry()

        form.columnconfigure(1, weight=1)

        self.status_config = ctk.CTkLabel(page, text="✅ Configure os parâmetros e avance para o backup", font=("Segoe UI", 10))
        self.status_config.pack(pady=12)

        return page

    def toggle_sql_entry(self):
        """Habilitar/Desabilitar campos SQL com base na escolha do RadioButton"""
        try:
            if self.sql_var.get() == "Não":
                self.entry_sql_file.configure(state="disabled")
                self.btn_browse_sql.configure(state="disabled")
                self.entry_sql_file.configure(text_color="gray")
            else:
                self.entry_sql_file.configure(state="normal")
                self.btn_browse_sql.configure(state="normal")
                self.entry_sql_file.configure(text_color="white")
        except Exception:
            pass

    def create_page_backup(self):
        page = ctk.CTkFrame(self.pages_container)
        ctk.CTkLabel(page, text="💾 Backup Automático", font=("Segoe UI", 16, "bold"), text_color="#FFA500").pack(pady=(0, 16))

        desc = ctk.CTkLabel(page, text="Antes de fazer o deploy, vamos criar backup de segurança:\n• Arquivos PHP atuais do servidor\n• Banco de dados atual", font=("Segoe UI", 10), justify="center")
        desc.pack(pady=10)

        buttons_frame = ctk.CTkFrame(page)
        buttons_frame.pack(pady=12)

        self.btn_backup_files = ctk.CTkButton(buttons_frame, text="📦 Backup Arquivos PHP", command=self.execute_backup_files, width=250)
        self.btn_backup_files.pack(pady=8)

        self.status_backup_files = ctk.CTkLabel(buttons_frame, text="⏳ Aguardando...", font=("Segoe UI", 10))
        self.status_backup_files.pack(pady=6)

        self.btn_backup_db = ctk.CTkButton(buttons_frame, text="🗄️ Backup Banco de Dados", command=self.execute_backup_database, width=250)
        self.btn_backup_db.pack(pady=8)

        self.status_backup_db = ctk.CTkLabel(buttons_frame, text="⏳ Aguardando...", font=("Segoe UI", 10))
        self.status_backup_db.pack(pady=6)

        ctk.CTkFrame(page, height=2, fg_color="#444444").pack(fill="x", pady=12)

        ctk.CTkLabel(page, text="📋 Log de Backup:", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 6))

        log_frame = ctk.CTkFrame(page)
        log_frame.pack(fill="both", expand=True, pady=6)
        self.backup_log_text = ctk.CTkTextbox(log_frame, width=600, height=200)
        self.backup_log_text.pack(fill="both", expand=True)

        self.backup_progress = ctk.CTkProgressBar(page)
        self.backup_progress.pack(fill="x", pady=10)

        return page

    def create_page_upload(self):
        page = ctk.CTkFrame(self.pages_container)
        ctk.CTkLabel(page, text="📤 Upload de Arquivos", font=("Segoe UI", 16, "bold"), text_color="#8B5CF6").pack(pady=(0, 16))

        desc = ctk.CTkLabel(page, text="Os arquivos serão enviados para o servidor via PSCP", font=("Segoe UI", 10))
        desc.pack(pady=8)

        info_frame = ctk.CTkFrame(page)
        info_frame.pack(fill="x", padx=12, pady=12)
        ctk.CTkLabel(info_frame, text=f"• Local: {self.data['local_path']}\n• Servidor: {self.data['host']}:{self.data['port']}\n• Destino: {self.data['remote_path']}", font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=8)

        self.status_upload = ctk.CTkLabel(page, text="⏳ Clique em 'Próximo' para iniciar o upload", font=("Segoe UI", 11, "bold"))
        self.status_upload.pack(pady=10)

        ctk.CTkLabel(page, text="📋 Log de Upload:", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(10, 6))
        log_frame = ctk.CTkFrame(page)
        log_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.upload_log_text = ctk.CTkTextbox(log_frame, width=700, height=300)
        self.upload_log_text.pack(fill="both", expand=True)

        self.upload_progress = ctk.CTkProgressBar(page)
        self.upload_progress.pack(fill="x", padx=12, pady=10)

        return page

    def create_page_verification(self):
        page = ctk.CTkFrame(self.pages_container)
        ctk.CTkLabel(page, text="🔍 Verificar Arquivos no Servidor", font=("Segoe UI", 16, "bold"), text_color="#8B5CF6").pack(pady=(0, 16))

        text_frame = ctk.CTkFrame(page)
        text_frame.pack(fill="both", expand=True, padx=12)
        self.files_text = ctk.CTkTextbox(text_frame, width=700, height=400)
        self.files_text.pack(fill="both", expand=True)

        ctk.CTkFrame(page, height=2, fg_color="#444444").pack(fill="x", pady=12)

        self.status_verification = ctk.CTkLabel(page, text="⏳ Execute o upload primeiro...", font=("Segoe UI", 10))
        self.status_verification.pack(pady=8)

        return page

    def create_page_import(self):
        page = ctk.CTkFrame(self.pages_container)
        ctk.CTkLabel(page, text="🗄️ Importar Banco de Dados", font=("Segoe UI", 16, "bold"), text_color="#8B5CF6").pack(pady=(0, 16))

        ctk.CTkLabel(page, text="Importar arquivo SQL para o banco de dados", font=("Segoe UI", 10)).pack(pady=8)

        form_frame = ctk.CTkFrame(page)
        form_frame.pack(fill="x", padx=12, pady=(0, 12))
        form = ctk.CTkFrame(form_frame)
        form.pack(fill="x")

        ctk.CTkLabel(form, text="Database:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        self.entry_db_name_import = ctk.CTkEntry(form, width=400)
        self.entry_db_name_import.grid(row=0, column=1, sticky="ew", pady=8)
        self.entry_db_name_import.insert(0, self.data['db_name'])

        ctk.CTkLabel(form, text="SQL File:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=8, padx=(0, 10))
        self.entry_sql_file_import = ctk.CTkEntry(form, width=400)
        self.entry_sql_file_import.grid(row=1, column=1, sticky="ew", pady=8)
        self.entry_sql_file_import.insert(0, self.data['sql_file'])

        form.columnconfigure(1, weight=1)

        self.progress = ctk.CTkProgressBar(page)
        self.progress.pack(fill="x", padx=12, pady=(0, 12))

        log_frame = ctk.CTkFrame(page)
        log_frame.pack(fill="both", expand=True, padx=12)
        self.log_text = ctk.CTkTextbox(log_frame, width=700, height=300)
        self.log_text.pack(fill="both", expand=True)

        ctk.CTkFrame(page, height=2, fg_color="#444444").pack(fill="x", pady=12)

        self.status_import = ctk.CTkLabel(page, text="⏳ Clique em 'Finalizar' para importar o SQL", font=("Segoe UI", 10))
        self.status_import.pack(pady=8)

        return page

    # --- Navigation / Actions ---
    def show_page(self, page_index):
        for page in self.pages:
            page.pack_forget()

        if 0 <= page_index < len(self.pages):
            self.pages[page_index].pack(fill="both", expand=True)
            self.current_step = page_index

        if page_index == 4:
            # Sincronizar dados para a página final
            try:
                self.entry_db_name_import.delete(0, END)
                self.entry_db_name_import.insert(0, self.data['db_name'])
                self.entry_sql_file_import.delete(0, END)
                self.entry_sql_file_import.insert(0, self.data['sql_file'])
                
                if self.sql_var.get() == "Não":
                    self.entry_db_name_import.configure(state="disabled")
                    self.entry_sql_file_import.configure(state="disabled")
                    self.status_import.configure(text="🚫 Importação de SQL desativada nas configurações.")
                else:
                    self.entry_db_name_import.configure(state="normal")
                    self.entry_sql_file_import.configure(state="normal")
                    self.status_import.configure(text="⏳ Clique em 'Finalizar' para importar o SQL")
            except Exception:
                pass

        self.update_buttons()

    def update_buttons(self):
        if self.current_step == 0:
            self.btn_back.configure(state="disabled")
        else:
            self.btn_back.configure(state="normal")

        if self.current_step == len(self.pages) - 1:
            self.btn_next.configure(text="Finalizar 🎉")
        else:
            self.btn_next.configure(text="Próximo →")

    def next_step(self):
        if self.current_step == 0:
            if self.validate_config():
                self.show_page(self.current_step + 1)
        elif self.current_step == 1:
            if not (self.backup_files_done or self.backup_db_done):
                response = messagebox.askyesno("Aviso - Backup não realizado", "⚠️ Você não fez nenhum backup!\n\nDeseja continuar sem backup?", icon='warning')
                if not response:
                    return
            self.show_page(self.current_step + 1)
        elif self.current_step == 2:
            if self.validate_upload():
                self.execute_upload_async()
        elif self.current_step == 3:
            if self.sql_var.get() == "Não":
                # Se não for importar SQL, pula para msg de sucesso direto ou vai para página 4 e finaliza
                self.show_page(self.current_step + 1)
                self.status_import.configure(text="✅ Arquivos enviados! SQL ignorado conforme configurado.")
                self.btn_next.configure(text="Finalizar 🎉")
            else:
                self.show_page(self.current_step + 1)
        elif self.current_step == 4:
            if self.sql_var.get() == "Sim":
                self.execute_import_async()
            else:
                self.finish_deploy_no_sql()

    def previous_step(self):
        if self.current_step > 0:
            self.show_page(self.current_step - 1)

    def validate_config(self):
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

        self.data['local_path'] = local_path
        self.data['backup_local_path'] = backup_path
        self.data['host'] = host
        self.data['port'] = port
        self.data['username'] = username
        self.data['password'] = password
        self.data['remote_path'] = remote_path
        self.data['db_name'] = db_name
        self.data['sql_file'] = self.entry_sql_file.get()
        self.data['import_sql'] = self.sql_var.get()

        return True

    def validate_upload(self):
        self.data['local_path'] = self.entry_local_path.get()
        self.data['host'] = self.entry_host.get()
        self.data['port'] = self.entry_port.get()
        self.data['username'] = self.entry_username.get()
        self.data['password'] = self.entry_password.get()
        self.data['remote_path'] = self.entry_remote_path.get()
        return True

    def execute_upload_async(self):
        self.status_upload.configure(text="⏳ Preparando upload...")
        self._start_progress(self.upload_progress)
        self.btn_next.configure(state="disabled")
        self.btn_back.configure(state="disabled")

        def upload_thread():
            success, message = self.deploy_manager.upload_files(self.data)
            self.safe_after(0, lambda: self.on_upload_complete(success, message))

        thread = threading.Thread(target=upload_thread, daemon=True)
        thread.start()

    def on_upload_complete(self, success, message):
        self._stop_progress(self.upload_progress)
        try:
            self.upload_log_text.delete(1.0, END)
            self.upload_log_text.insert(END, message)
        except Exception:
            pass

        if success:
            self.status_upload.configure(text="✅ Upload concluído! Arquivos enviados com sucesso")
            self.show_page(self.current_step + 1)
            self.execute_verification_async()
        else:
            self.status_upload.configure(text="❌ Erro no upload")

        self.btn_next.configure(state="normal")
        self.btn_back.configure(state="normal")

    def execute_verification_async(self):
        self.status_verification.configure(text="⏳ Conectando e verificando arquivos...")

        def verify_thread():
            success, files = self.deploy_manager.list_remote_files(self.data)
            self.safe_after(0, lambda: self.on_verification_complete(success, files))

        thread = threading.Thread(target=verify_thread, daemon=True)
        thread.start()

    def on_verification_complete(self, success, files):
        try:
            self.files_text.delete(1.0, END)
        except Exception:
            pass

        if success:
            try:
                self.files_text.insert(END, files)
            except Exception:
                pass
            self.status_verification.configure(text="✅ Verificação completa! Arquivos listados acima.")
        else:
            try:
                self.files_text.insert(END, f"❌ Erro na verificação:\n\n{files}")
            except Exception:
                pass
            self.status_verification.configure(text="❌ Erro na verificação")

    def execute_import_async(self):
        self.status_import.configure(text="⏳ Importando SQL...")
        self._start_progress(self.progress)
        self.btn_next.configure(state="disabled")
        self.btn_back.configure(state="disabled")

        self.data['db_name'] = self.entry_db_name_import.get()
        self.data['sql_file'] = self.entry_sql_file_import.get()

        def import_thread():
            success, log = self.deploy_manager.import_sql(self.data)
            self.config_manager.save_log(log)
            self.safe_after(0, lambda: self.on_import_complete(success, log))

        thread = threading.Thread(target=import_thread, daemon=True)
        thread.start()

    def on_import_complete(self, success, log):
        self._stop_progress(self.progress)
        try:
            self.log_text.delete(1.0, END)
            self.log_text.insert(END, log)
        except Exception:
            pass

        if success:
            self.status_import.configure(text="✅ Deploy concluído com sucesso! 🎉")
            success_message = (
                "🎉 Deploy Concluído com Sucesso!\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "📍 Acesse o Sistema:\n"
                "   https://adv.precifex.com/\n\n"
                "📧 Email de Acesso:\n"
                "   rodrigoexer2@gmail.com\n\n"
                "🔑 Senha Padrão:\n"
                "   123123\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "✨ O sistema está pronto para uso!"
            )
            messagebox.showinfo("Deploy Finalizado", success_message)
        else:
            self.status_import.configure(text="❌ Erro no import SQL")
            messagebox.showerror("Erro", "Erro ao importar SQL. Verifique o log acima.")

        self.btn_next.configure(state="normal")
        self.btn_back.configure(state="normal")

    def finish_deploy_no_sql(self):
        """Finalizar deploy sem importar banco de dados"""
        success_message = (
            "🎉 Upload de Arquivos Concluído!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ O banco de dados NÃO foi atualizado (opção ignorar SQL selecionada).\n\n"
            "📍 Acesse o Sistema:\n"
            "   https://adv.precifex.com/\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✨ O deploy dos arquivos foi realizado com sucesso!"
        )
        messagebox.showinfo("Deploy Finalizado", success_message)
        self.root.destroy()

    # --- Browsers and backups ---
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta do projeto", initialdir=self.entry_local_path.get())
        if folder:
            try:
                self.entry_local_path.delete(0, END)
                self.entry_local_path.insert(0, folder)
            except Exception:
                pass

    def browse_backup_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta para backups", initialdir=self.entry_backup_path.get())
        if folder:
            try:
                self.entry_backup_path.delete(0, END)
                self.entry_backup_path.insert(0, folder)
            except Exception:
                pass

    def browse_sql_file(self):
        file = filedialog.askopenfilename(title="Selecione o arquivo SQL", initialdir=self.entry_local_path.get(), filetypes=[("SQL Files", "*.sql"), ("All Files", "*.*")])
        if file:
            local_path = self.entry_local_path.get()
            if file.startswith(local_path):
                file = os.path.relpath(file, local_path)
            try:
                self.entry_sql_file.delete(0, END)
                self.entry_sql_file.insert(0, file)
            except Exception:
                pass

    def execute_backup_files(self):
        self._start_progress(self.backup_progress)
        self.btn_backup_files.configure(state="disabled")
        self.status_backup_files.configure(text="🔄 Fazendo backup...")

        backup_path = self.entry_backup_path.get()
        os.makedirs(backup_path, exist_ok=True)

        def backup_thread():
            self.data['backup_local_path'] = backup_path
            self.data['remote_path'] = self.entry_remote_path.get()
            self.data['host'] = self.entry_host.get()
            self.data['port'] = self.entry_port.get()
            self.data['username'] = self.entry_username.get()
            self.data['password'] = self.entry_password.get()
            success, log = self.deploy_manager.backup_files(self.data)
            self.safe_after(0, lambda: self.on_backup_files_complete(success, log))

        thread = threading.Thread(target=backup_thread, daemon=True)
        thread.start()

    def on_backup_files_complete(self, success, log):
        self._stop_progress(self.backup_progress)
        try:
            self.backup_log_text.insert(END, log + "\n\n")
            self.backup_log_text.see(END)
        except Exception:
            pass

        if success:
            self.backup_files_done = True
            self.status_backup_files.configure(text="✅ Backup concluído!")
            messagebox.showinfo("Backup Concluído", f"🎉 Backup dos arquivos PHP foi gerado com segurança!\n\n📁 Localização: {self.data['backup_local_path']}")
        else:
            self.status_backup_files.configure(text="❌ Erro no backup")
            messagebox.showerror("Erro", "Falha ao fazer backup dos arquivos.")

        self.btn_backup_files.configure(state="normal")

    def execute_backup_database(self):
        self._start_progress(self.backup_progress)
        self.btn_backup_db.configure(state="disabled")
        self.status_backup_db.configure(text="🔄 Fazendo backup...")

        backup_path = self.entry_backup_path.get()
        os.makedirs(backup_path, exist_ok=True)

        def backup_thread():
            self.data['backup_local_path'] = backup_path
            self.data['db_name'] = self.entry_db_name.get()
            self.data['host'] = self.entry_host.get()
            self.data['port'] = self.entry_port.get()
            self.data['username'] = self.entry_username.get()
            self.data['password'] = self.entry_password.get()
            success, log = self.deploy_manager.backup_database(self.data)
            self.safe_after(0, lambda: self.on_backup_database_complete(success, log))

        thread = threading.Thread(target=backup_thread, daemon=True)
        thread.start()

    def on_backup_database_complete(self, success, log):
        self._stop_progress(self.backup_progress)
        try:
            self.backup_log_text.insert(END, log + "\n\n")
            self.backup_log_text.see(END)
        except Exception:
            pass

        if success:
            self.backup_db_done = True
            self.status_backup_db.configure(text="✅ Backup concluído!")
            messagebox.showinfo("Backup Concluído", f"🎉 Backup do banco de dados foi gerado com segurança!\n\n📁 Localização: {self.data['backup_local_path']}")
        else:
            self.status_backup_db.configure(text="❌ Erro no backup")
            messagebox.showerror("Erro", "Falha ao fazer backup do banco.")

        self.btn_backup_db.configure(state="normal")

    def load_last_config(self):
        config = self.config_manager.load_config()
        if config:
            try:
                if 'local_path' in config and config['local_path']:
                    self.entry_local_path.delete(0, END)
                    self.entry_local_path.insert(0, config['local_path'])
                    self.data['local_path'] = config['local_path']
                if 'host' in config and config['host']:
                    self.entry_host.delete(0, END)
                    self.entry_host.insert(0, config['host'])
                    self.data['host'] = config['host']
                if 'port' in config and config['port']:
                    self.entry_port.delete(0, END)
                    self.entry_port.insert(0, config['port'])
                    self.data['port'] = config['port']
                if 'username' in config and config['username']:
                    self.entry_username.delete(0, END)
                    self.entry_username.insert(0, config['username'])
                    self.data['username'] = config['username']
                if 'remote_path' in config and config['remote_path']:
                    self.entry_remote_path.delete(0, END)
                    self.entry_remote_path.insert(0, config['remote_path'])
                    self.data['remote_path'] = config['remote_path']
                if 'db_name' in config and config['db_name']:
                    self.data['db_name'] = config['db_name']
                if 'sql_file' in config and config['sql_file']:
                    self.data['sql_file'] = config['sql_file']
                if 'import_sql' in config and config['import_sql']:
                    self.data['import_sql'] = config['import_sql']
                    self.sql_var.set(config['import_sql'])
                    self.toggle_sql_entry()
                self.status_upload.configure(text="✅ Configuração anterior carregada")
            except Exception:
                pass

    def toggle_password_visibility(self):
        try:
            if self.entry_password.cget('show') == '•':
                self.entry_password.configure(show='')
            else:
                self.entry_password.configure(show='•')
        except Exception:
            pass

    def toggle_directories(self):
        try:
            if getattr(self, 'dir_expanded', False):
                try:
                    self.directories_frame.grid_remove()
                except Exception:
                    self.directories_frame.pack_forget()
                try:
                    self.dir_toggle.configure(text="📂 Diretórios ▸")
                except Exception:
                    pass
                self.dir_expanded = False
            else:
                try:
                    self.directories_frame.grid()
                except Exception:
                    try:
                        self.directories_frame.pack()
                    except Exception:
                        pass
                try:
                    self.dir_toggle.configure(text="📂 Diretórios ▾")
                except Exception:
                    pass
                self.dir_expanded = True
        except Exception:
            pass

    def toggle_server(self):
        """Mostrar/ocultar o bloco de servidor"""
        try:
            if getattr(self, 'server_expanded', False):
                try:
                    self.server_frame.grid_remove()
                except Exception:
                    self.server_frame.pack_forget()
                try:
                    self.server_toggle.configure(text="🌐 Servidor ▸")
                except Exception:
                    pass
                self.server_expanded = False
            else:
                try:
                    self.server_frame.grid()
                except Exception:
                    try:
                        self.server_frame.pack()
                    except Exception:
                        pass
                try:
                    self.server_toggle.configure(text="🌐 Servidor ▾")
                except Exception:
                    pass
                self.server_expanded = True
        except Exception:
            pass

    def save_current_config(self):
        self.data['local_path'] = self.entry_local_path.get()
        self.data['host'] = self.entry_host.get()
        self.data['port'] = self.entry_port.get()
        self.data['username'] = self.entry_username.get()
        self.data['remote_path'] = self.entry_remote_path.get()
        self.data['db_name'] = self.entry_db_name.get()
        self.data['sql_file'] = self.entry_sql_file.get()
        self.data['import_sql'] = self.sql_var.get()
        success, msg = self.config_manager.save_config(self.data)
        if success:
            messagebox.showinfo("Configuração Salva", "Configuração salva com sucesso!")
        else:
            messagebox.showerror("Erro", msg)

    def on_closing(self):
        self._closing = True
        for wid in list(self._progress_tasks.keys()):
            self._progress_tasks[wid] = False
        try:
            self.deploy_manager.close()
        except Exception:
            pass
        try:
            self.root.after(100, self.root.destroy)
        except Exception:
            try:
                self.root.destroy()
            except Exception:
                pass


def main():
    root = ctk.CTk()
    # posicionar janela no topo central da tela para evitar corte
    initial_w, initial_h = 700, 720
    try:
        screen_w = root.winfo_screenwidth()
        x = max(0, (screen_w - initial_w) // 2)
        y = 0
        root.geometry(f"{initial_w}x{initial_h}+{x}+{y}")
    except Exception:
        pass

    app = DeployWizard(root)
    # reforçar posição após criação dos widgets
    try:
        root.update_idletasks()
        root.geometry(f"+{x}+{y}")
    except Exception:
        pass

    root.mainloop()


if __name__ == "__main__":
    main()


