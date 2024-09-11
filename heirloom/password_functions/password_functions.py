from cryptography.fernet import Fernet
import keyring
import base64


def set_encryption_key():
    key = Fernet.generate_key()
    keyring.set_password('system', 'heirloom-encryption-key', base64.b64encode(key).decode('utf-8'))


def get_encryption_key():
    key = keyring.get_password('system', 'heirloom-encryption-key')
    if key:
        return base64.b64decode(key.encode('utf-8'))
    else:
        return None


def encrypt_password(password):
    key = get_encryption_key()
    f = Fernet(key)
    token = f.encrypt(password.encode('utf-8'))
    return token


def decrypt_password(password):
    key = get_encryption_key()
    f = Fernet(key)
    token = f.decrypt(password.encode('utf-8'))
    return token