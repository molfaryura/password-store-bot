"""Key for encryption and decryption"""

import secrets

import hashlib

from dotenv import set_key

HASH = hashlib.sha256()
HASH.update(secrets.token_hex(64).encode('utf8'))
HASH = hash.hexdigest()

set_key('.env', 'SECRET_KEY', HASH)
