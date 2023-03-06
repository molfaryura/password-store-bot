import secrets

import hashlib

from dotenv import set_key

hash = hashlib.sha256()
hash.update(secrets.token_hex(64).encode('utf8'))
hash = hash.hexdigest()

set_key('.env', 'SECRET_KEY', hash) 
