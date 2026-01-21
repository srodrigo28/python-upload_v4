import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import paramiko
import os
import stat
from datetime import datetime

# Configurações
HOST = '77.37.126.7'
PORT = 22
USERNAME = 'srodrigo'
PASSWORD = '@dV#sRnAt98!'
REMOTE_PATH = '/var/www/precifex.com/sistemas'

class RemoteFileManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador Remoto - Precifex")
        self.root.geometry("800x600")
        
        self.ssh = None
        self.sftp = None
        self.current_remote_path = REMOTE_PATH
        
        self.setup_ui()
        
        # Conectar automaticamente ao abrir
        self.root.after(100, self.connect_and_list)

    def setup_ui(self):
        # Frame Superior (Botoes)
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill='x')
        
        ttk.Button(top_frame, text="🔄 Atualizar", command=self.refresh_list).pack(side='left', padx=5)
        ttk.Button(top_frame, text="⬇️ Baixar", command=self.download_selected).pack(side='left', padx=5)
        ttk.Button(top_frame, text="⬆️ Upload", command=self.upload_file).pack(side='left', padx=5)
        
        # Search Bar
        ttk.Label(top_frame, text="🔎 Buscar:").pack(side='left', padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda name, index, mode, sv=self.search_var: self.filter_list())
        search_entry = ttk.Entry(top_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        
        # Label do Caminho
        self.lbl_path = ttk.Label(self.root, text=f"Caminho: {self.current_remote_path}", font=('Arial', 10, 'bold'))
        self.lbl_path.pack(fill='x', padx=10, pady=5)
        
        # Lista de Arquivos (Treeview)
        tree_frame = ttk.Frame(self.root, padding=10)
        tree_frame.pack(fill='both', expand=True)
        
        columns = ('nome', 'tamanho', 'modificacao', 'permissoes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        self.tree.heading('nome', text='Nome')
        self.tree.heading('tamanho', text='Tamanho')
        self.tree.heading('modificacao', text='Data Modificação')
        self.tree.heading('permissoes', text='Permissões')
        
        self.tree.column('nome', width=300)
        self.tree.column('tamanho', width=100)
        self.tree.column('modificacao', width=150)
        self.tree.column('permissoes', width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', padding=5)
        status_bar.pack(fill='x')

        self.cached_items = [] # Cache para filtragem

    def connect_and_list(self):
        self.status_var.set("Conectando ao servidor...")
        self.root.update()
        
        try:
            if not self.ssh:
                self.ssh = paramiko.SSHClient()
                self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.ssh.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=10)
                self.sftp = self.ssh.open_sftp()
            
            self.refresh_list()
            
        except Exception as e:
            messagebox.showerror("Erro de Conexão", str(e))
            self.status_var.set("Erro de conexão")

    def refresh_list(self):
        self.status_var.set(f"Listando: {self.current_remote_path}...")
        self.root.update()
        
        try:
            items = self.sftp.listdir_attr(self.current_remote_path)
            
            # Ordenar: Pastas primeiro, depois arquivos
            items.sort(key=lambda x: (not stat.S_ISDIR(x.st_mode), x.filename))
            
            self.cached_items = items
            self.filter_list()
            
            self.lbl_path.config(text=f"Caminho: {self.current_remote_path}")
            self.status_var.set(f"Listagem concluída. {len(items)} itens encontrados.")
            
        except Exception as e:
            messagebox.showerror("Erro ao Listar", str(e))
            self.status_var.set("Erro ao listar")

    def filter_list(self):
        search_term = self.search_var.get().lower()
        
        # Limpar lista atual
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        for item in self.cached_items:
            if search_term and search_term not in item.filename.lower():
                continue
                
            is_dir = stat.S_ISDIR(item.st_mode)
            icon = "📁 " if is_dir else "📄 "
            name = icon + item.filename
            
            size = f"{item.st_size / 1024:.1f} KB" if not is_dir else "-"
            mtime = datetime.fromtimestamp(item.st_mtime).strftime('%Y-%m-%d %H:%M')
            perms = stat.filemode(item.st_mode)
            
            self.tree.insert('', 'end', values=(name, size, mtime, perms), tags=('dir' if is_dir else 'file',))

    def download_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um arquivo para baixar")
            return
            
        item_values = self.tree.item(selected[0])['values']
        raw_name = item_values[0] # Vem com ícone
        filename = raw_name.replace("📁 ", "").replace("📄 ", "")
        
        if "📁" in raw_name:
            # Navegar para pasta (opcional, simples aqui só avisa)
            # Para simplificar: se for pasta, entra nela
            self.current_remote_path = f"{self.current_remote_path}/{filename}"
            self.refresh_list()
            return

        remote_file = f"{self.current_remote_path}/{filename}"
        
        save_path = filedialog.asksaveasfilename(initialfile=filename, title="Salvar arquivo como...")
        if not save_path:
            return
            
        try:
            self.status_var.set(f"Baixando {filename}...")
            self.root.update()
            
            self.sftp.get(remote_file, save_path)
            
            self.status_var.set("Download concluído!")
            messagebox.showinfo("Sucesso", f"Arquivo baixado com sucesso:\n{save_path}")
            
        except Exception as e:
            messagebox.showerror("Erro no Download", str(e))
            self.status_var.set("Erro no download")

    def upload_file(self):
        local_path = filedialog.askopenfilename(title="Selecione o arquivo para enviar")
        if not local_path:
            return
            
        filename = os.path.basename(local_path)
        remote_file = f"{self.current_remote_path}/{filename}"
        
        confirm = messagebox.askyesno("Confirmar Upload", 
                                      f"Enviar arquivo para:\n{remote_file}\n\nIsso substituirá o arquivo se ele já existir.")
        if not confirm:
            return
            
        try:
            self.status_var.set(f"Enviando {filename}...")
            self.root.update()
            
            self.sftp.put(local_path, remote_file)
            
            self.status_var.set("Upload concluído!")
            messagebox.showinfo("Sucesso", "Upload realizado com sucesso!")
            self.refresh_list()
            
        except Exception as e:
            messagebox.showerror("Erro no Upload", str(e))
            self.status_var.set("Erro no upload")

    def __del__(self):
        if self.sftp: self.sftp.close()
        if self.ssh: self.ssh.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteFileManager(root)
    root.mainloop()
