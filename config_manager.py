"""
Gerenciador de configurações do Deploy Wizard
Salva e carrega configurações em JSON
"""
import json
import os
from datetime import datetime


class ConfigManager:
    """Gerenciar salvamento e carregamento de configurações"""
    
    def __init__(self, config_file='config/last_config.json'):
        self.config_file = config_file
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Garantir que diretório config existe"""
        config_dir = os.path.dirname(self.config_file)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
    def save_config(self, data):
        """Salvar configuração em arquivo JSON"""
        try:
            # Remover senha por segurança
            safe_data = data.copy()
            safe_data['password'] = ''  # Não salvar senha
            safe_data['last_saved'] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(safe_data, f, indent=4, ensure_ascii=False)
            
            return True, "Configuração salva"
        except Exception as e:
            return False, f"Erro ao salvar: {str(e)}"
    
    def load_config(self):
        """Carregar última configuração"""
        try:
            if not os.path.exists(self.config_file):
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            return None
    
    def save_log(self, log_data):
        """Salvar log de deploy"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"logs/deploy_{timestamp}.log"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Deploy Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n\n")
                f.write(log_data)
            
            return True, log_file
        except Exception as e:
            return False, f"Erro ao salvar log: {str(e)}"
