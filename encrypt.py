"""Encryption and decryption text data based on AES"""

import base64

import hashlib

import os

from Crypto import Random
from Crypto.Cipher import AES

from dotenv import load_dotenv

secret_key = os.environ.get('SECRET_KEY')

load_dotenv()

def hash_secret_word(message):
    """Hashes string using sha256

    param message: string

    returns(str): hash of the given string.
    """

    result = hashlib.sha256(message.encode()).hexdigest()
    return result

def encrypt(key, plaintext):
    """A function that encrypts the given plaintext using AES CBC encryption with the given key

    param key: a bytes object representing the encryption key.
    param plaintext: a bytes object representing the text to be encrypted.

    returns: The encrypted text as a bytes object, encoded in base64.
    """

    plaintext = plaintext + b"\0" * (AES.block_size - len(plaintext) % AES.block_size)
    initialization_vector = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    return base64.b64encode(initialization_vector + cipher.encrypt(plaintext))


def decrypt(key, ciphertext):
    """Decrypts the given ciphertext using AES CBC decryption with the given key

    param key: a bytes object representing the decryption key.
    param ciphertext: a bytes object representing the encrypted text to be decrypted.

    returns: The decrypted text as a bytes object, with any trailing null bytes (b"\0") removed.
    """

    ciphertext = base64.b64decode(ciphertext)
    initialization_vector = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, initialization_vector)
    return cipher.decrypt(ciphertext[AES.block_size:]).rstrip(b"\0")

KEY = hashlib.sha256(f"{secret_key}".encode()).digest()
