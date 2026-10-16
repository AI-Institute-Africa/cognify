"""
OnlyOffice Document Server integration for in-browser editing.
Handles DOCX serving, token generation, and callback processing.
"""
import json
import hashlib
import hmac
import os
import requests
from datetime import datetime
from pathlib import Path
from django.conf import settings

# OnlyOffice Document Server configuration
ONLYOFFICE_DS_URL = getattr(settings, 'ONLYOFFICE_DS_URL', 'http://127.0.0.1:8080')
ONLYOFFICE_SECRET = getattr(settings, 'ONLYOFFICE_SECRET', 'your-secret-key-change-in-settings')


class OnlyOfficeService:
    """Service for OnlyOffice Document Server integration."""
    
    @staticmethod
    def generate_document_config(file_path, document_title, edit_mode=True, user_id=None, user_name=None):
        """
        Generate OnlyOffice document configuration for iframe.
        
        Args:
            file_path: Full path to DOCX file
            document_title: Display name for document
            edit_mode: Whether to allow editing (True) or view only (False)
            user_id: Optional user identifier for tracking
            user_name: Optional user display name
        
        Returns:
            dict: Configuration for OnlyOffice editor
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Generate document key (hash of file path + modification time)
        file_stat = os.stat(file_path)
        file_key = hashlib.md5(
            f"{file_path}{file_stat.st_mtime}".encode()
        ).hexdigest()
        
        config = {
            "type": "desktop",
            "documentType": "text",
            "document": {
                "title": document_title,
                "url": "",  # Will be set by view
                "fileType": "docx",
                "key": file_key,
            },
            "editorConfig": {
                "mode": "edit" if edit_mode else "view",
                "callbackUrl": "",  # Will be set by view
                "user": {
                    "id": str(user_id or "anonymous"),
                    "name": user_name or "User",
                }
            }
        }
        return config
    
    @staticmethod
    def sign_token(data, secret=None):
        """
        Generate HMAC-SHA256 signature for document config.
        
        Args:
            data: dict or JSON string to sign
            secret: HMAC secret key
        
        Returns:
            str: Base64-encoded signature (hex format)
        """
        if secret is None:
            secret = ONLYOFFICE_SECRET
        
        if isinstance(data, dict):
            data = json.dumps(data, separators=(',', ':'), sort_keys=True)
        elif not isinstance(data, str):
            data = str(data)
        
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    @staticmethod
    def verify_callback_signature(data, signature, secret=None):
        """
        Verify callback signature from OnlyOffice Document Server.
        
        Args:
            data: Request data dict
            signature: Signature from request header (Authorization: Bearer <signature>)
            secret: HMAC secret key
        
        Returns:
            bool: True if signature is valid
        """
        if secret is None:
            secret = ONLYOFFICE_SECRET
        
        # Create string to verify from status object
        if 'status' in data:
            # For callback: hash the 'status' field
            verification_string = str(data.get('status', ''))
        else:
            verification_string = json.dumps(data, separators=(',', ':'), sort_keys=True)
        
        expected_signature = hmac.new(
            secret.encode(),
            verification_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    @staticmethod
    def process_callback(callback_data):
        """
        Process OnlyOffice Document Server callback.
        
        Args:
            callback_data: dict with status, key, url, etc.
        
        Returns:
            dict: Response data for OnlyOffice
        """
        status = callback_data.get('status')
        
        if status == 1:  # Document is being edited
            return {"error": 0}
        
        elif status == 2:  # Document ready for saving
            download_url = callback_data.get('url')
            if download_url:
                return {
                    "error": 0,
                    "message": "Document received successfully"
                }
            return {"error": 1}
        
        elif status == 3:  # Error in document
            return {
                "error": 1,
                "message": f"Error: {callback_data.get('error', 'Unknown error')}"
            }
        
        elif status == 4:  # No document session
            return {
                "error": 1,
                "message": "No document session"
            }
        
        else:
            return {
                "error": 1,
                "message": f"Unknown status: {status}"
            }


def download_edited_document(download_url, output_path):
    """
    Download edited document from OnlyOffice Document Server.
    
    Args:
        download_url: URL to download edited document from
        output_path: Where to save downloaded file
    
    Returns:
        bool: True if successful
    """
    try:
        response = requests.get(download_url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"Error downloading document: {e}")
        return False
