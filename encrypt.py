import base64

import hashlib

from Crypto import Random
from Crypto.Cipher import AES

from key import hash

import os

from dotenv import load_dotenv

secret_key = os.environ.get('SECRET_KEY')

load_dotenv()

def encrypt(key, plaintext):

    plaintext = plaintext + b"\0" * (AES.block_size - len(plaintext) % AES.block_size)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(plaintext))


def decrypt(key, ciphertext):

    ciphertext = base64.b64decode(ciphertext)
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.decrypt(ciphertext[AES.block_size:]).rstrip(b"\0")

key = hashlib.sha256(f"{secret_key}".encode()).digest()

#encrypted_text = encrypt(key, b"Hello, World!")

#decrypted_text = decrypt(key, encrypted_text).decode('utf8')
