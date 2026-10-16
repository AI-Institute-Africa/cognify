import os
import base64
from cryptography.fernet import Fernet
from django.conf import settings

# In a real production system, this key should be in environment variables
# For this implementation, we ensure it's generated once if missing
CIPHER_KEY = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
if not CIPHER_KEY:
    CIPHER_KEY = Fernet.generate_key().decode()
    # Note: In production, we'd save this to a secure vault or .env
    
cipher_suite = Fernet(CIPHER_KEY.encode())

class EncryptionService:
    @staticmethod
    def encrypt(text):
        if not text:
            return ""
        if isinstance(text, str):
            text = text.encode()
        return cipher_suite.encrypt(text).decode()

    @staticmethod
    def decrypt(encrypted_text):
        if not encrypted_text:
            return ""
        try:
            return cipher_suite.decrypt(encrypted_text.encode()).decode()
        except Exception:
            # If decryption fails (e.g. data wasn't encrypted), return as is
            return encrypted_text
