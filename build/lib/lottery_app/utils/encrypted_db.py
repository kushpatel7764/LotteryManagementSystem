"""Database encryption/decryption utilities using Fernet symmetric encryption."""
import os

from cryptography.fernet import Fernet


def get_cipher():
    """Return a Fernet cipher using the FERNET_KEY environment variable."""
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError("Missing FERNET_KEY environment variable")
    return Fernet(key.encode())


def encrypt_file(input_path, output_path=None):
    """Encrypt a file in-place using the configured Fernet key."""
    cipher = get_cipher()
    if output_path is None:
        output_path = input_path + ".enc"

    if not os.path.exists(input_path):
        return

    with open(input_path, "rb") as f:
        data = f.read()
    encrypted = cipher.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    print("Encrypted file created:", os.path.exists("app.db.enc"))


def decrypt_file(input_path, output_path=None):
    """Decrypt a Fernet-encrypted file."""
    cipher = get_cipher()
    if output_path is None:
        output_path = input_path.replace(".enc", "")

    if not os.path.exists(input_path):
        return

    with open(input_path, "rb") as f:
        data = f.read()
    decrypted = cipher.decrypt(data)

    with open(output_path, "wb") as f:
        f.write(decrypted)
