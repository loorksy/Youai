"""
نظام تشفير مفاتيح API
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

# ثابت Salt (يجب أن يكون نفسه دائماً)
SALT = b'youai_encryption_salt_2025_secure'

def get_encryption_key():
    """توليد مفتاح التشفير من JWT_SECRET"""
    jwt_secret = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(jwt_secret.encode()))
    return Fernet(key)

def encrypt_api_key(api_key: str) -> str:
    """
    تشفير مفتاح API
    
    Args:
        api_key: المفتاح بنص صريح
    
    Returns:
        المفتاح المشفر
    """
    if not api_key:
        return ""
    
    try:
        f = get_encryption_key()
        encrypted = f.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        print(f"Error encrypting key: {str(e)}")
        return ""

def decrypt_api_key(encrypted_key: str) -> str:
    """
    فك تشفير مفتاح API
    
    Args:
        encrypted_key: المفتاح المشفر
    
    Returns:
        المفتاح بنص صريح
    """
    if not encrypted_key:
        return ""
    
    try:
        f = get_encryption_key()
        decrypted = f.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"Error decrypting key: {str(e)}")
        return ""

def encrypt_credentials(credentials: dict) -> dict:
    """
    تشفير جميع المفاتيح في dictionary
    يعمل بشكل recursive للـ nested dictionaries
    """
    encrypted = {}
    
    for key, value in credentials.items():
        if isinstance(value, str) and value:
            # تشفير القيم النصية فقط
            encrypted[key] = encrypt_api_key(value)
        elif isinstance(value, dict):
            # تشفير recursive للـ nested dicts
            encrypted[key] = encrypt_credentials(value)
        else:
            # الاحتفاظ بالقيم الأخرى كما هي
            encrypted[key] = value
    
    return encrypted

def decrypt_credentials(encrypted_creds: dict) -> dict:
    """
    فك تشفير جميع المفاتيح في dictionary
    """
    decrypted = {}
    
    for key, value in encrypted_creds.items():
        if isinstance(value, str) and value:
            # فك تشفير القيم النصية
            decrypted[key] = decrypt_api_key(value)
        elif isinstance(value, dict):
            # فك تشفير recursive
            decrypted[key] = decrypt_credentials(value)
        else:
            decrypted[key] = value
    
    return decrypted

def mask_api_key(api_key: str) -> str:
    """
    إخفاء المفتاح (عرض أول 4 وآخر 4 أحرف فقط)
    
    Args:
        api_key: المفتاح الكامل
    
    Returns:
        المفتاح المخفي (مثال: AIza••••••••••••3Abc)
    """
    if not api_key or len(api_key) <= 8:
        return '••••••••'
    
    return api_key[:4] + '•' * (len(api_key) - 8) + api_key[-4:]

def mask_credentials(credentials: dict) -> dict:
    """
    إخفاء جميع المفاتيح في dictionary
    """
    masked = {}
    
    for key, value in credentials.items():
        if isinstance(value, str) and value:
            masked[key] = mask_api_key(value)
        elif isinstance(value, dict):
            masked[key] = mask_credentials(value)
        else:
            masked[key] = value
    
    return masked
