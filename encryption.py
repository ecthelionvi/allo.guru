import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

class Encryptor:
    def __init__(self):
        self.key = os.getenv("ENCRYPTION_KEY").encode()
        self.fernet = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        return self.fernet.decrypt(data.encode()).decode()
