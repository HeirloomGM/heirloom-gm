from cryptography.fernet import Fernet
import base64
from pathlib import Path

try:
    import keyring
except ModuleNotFoundError:
    keyring = None


SERVICE_NAME = 'heirloom-gm'
KEY_NAME = 'encryption-key'
FALLBACK_KEY_FILE = Path('~/.config/heirloom/encryption.key').expanduser()


def _store_key_file(key):
    FALLBACK_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_KEY_FILE.write_text(base64.b64encode(key).decode('utf-8'))
    FALLBACK_KEY_FILE.chmod(0o600)


def _read_key_file():
    if FALLBACK_KEY_FILE.is_file():
        return base64.b64decode(FALLBACK_KEY_FILE.read_text().strip().encode('utf-8'))
    return None


def set_encryption_key():
    key = Fernet.generate_key()
    try:
        if keyring is None:
            raise RuntimeError('keyring is not available')
        keyring.set_password(SERVICE_NAME, KEY_NAME, base64.b64encode(key).decode('utf-8'))
    except Exception:
        _store_key_file(key)


def get_encryption_key():
    try:
        if keyring is None:
            raise RuntimeError('keyring is not available')
        key = keyring.get_password(SERVICE_NAME, KEY_NAME)
    except Exception:
        key = None
    if key:
        return base64.b64decode(key.encode('utf-8'))
    return _read_key_file()


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
