"""
Validadores para campos do Deploy Wizard
"""
import re
import os
import socket


class Validators:
    """Classe para validação de campos"""
    
    @staticmethod
    def validate_ip(ip):
        """Validar endereço IP ou hostname"""
        if not ip or not ip.strip():
            return False
            
        # Tentar validar como IP
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(pattern, ip):
            parts = ip.split('.')
            return all(0 <= int(part) <= 255 for part in parts)
        
        # Tentar validar como hostname
        try:
            socket.gethostbyname(ip)
            return True
        except:
            return False
    
    @staticmethod
    def validate_port(port):
        """Validar porta"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except:
            return False
    
    @staticmethod
    def validate_path(path):
        """Validar path local"""
        return os.path.exists(path)
    
    @staticmethod
    def validate_remote_path(path):
        """Validar formato de path remoto"""
        # Path Unix deve começar com /
        return path and path.startswith('/')
    
    @staticmethod
    def validate_not_empty(text):
        """Validar se texto não está vazio"""
        return text and text.strip() != ""
    
    @staticmethod
    def validate_username(username):
        """Validar username SSH"""
        if not username or not username.strip():
            return False
        # Username válido: letras, números, underscore, hífen
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_password(password):
        """Validar que senha não está vazia"""
        return password and len(password) > 0
