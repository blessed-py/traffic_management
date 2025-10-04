import random
import hashlib
from cryptography.fernet import Fernet
import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC




class Cryptography():
    def __init__(self):
        self.strings = 'abcdefNOPQRSTUVWXYZ1ghijklmnopqr34567stuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz'
    
    def generate_unique_id(self, key_size=10):
        """Generate a random unique ID (for non-password uses)"""
        return ''.join(random.sample(self.strings, key_size))

    def generate_key(self, password, salt=b'salt_'):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        return key
    

    def hash_this(self, data):  
        hash_object = hashlib.sha256(data.encode())
        return hash_object.hexdigest()

    
