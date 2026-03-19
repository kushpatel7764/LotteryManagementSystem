import os
from cryptography.fernet import Fernet


def get_cipher():
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError("Missing FERNET_KEY environment variable")
    return Fernet(key.encode())


def encrypt_file(input_path, output_path=None):
    if not isinstance(input_path, str):
        raise TypeError("input_path must be a string")

    if output_path is not None and not isinstance(output_path, str):
        raise TypeError("output_path must be a string")

    if not os.path.exists(input_path):
        return

    if os.path.getsize(input_path) == 0:
        print("DB is empty. Skipping encryption.")
        return

    cipher = get_cipher()

    if output_path is None:
        output_path = input_path + ".enc"

    with open(input_path, "rb") as f:
        data = f.read()
    encrypted = cipher.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted)

    print("Encrypted file created:", os.path.exists(output_path))


def decrypt_file(input_path, output_path=None):
    cipher = get_cipher()

    # --- input validation ---
    if not isinstance(input_path, str):
        raise TypeError("input_path must be a string")

    if not os.path.exists(input_path):
        return  # allow silent exit if user launches app first time

    if output_path is not None and not isinstance(output_path, str):
        raise TypeError("output_path must be a string")

    if output_path is None:
        if not input_path.endswith(".enc"):
            raise ValueError(
                "Encrypted file must end with .enc or output_path must be provided"
            )
        output_path = input_path[:-4]  # strip ".enc"
    # --- end input validation ---

    # --- decrypt ---
    with open(input_path, "rb") as f:
        encrypted_bytes = f.read()

    # Safety: empty .enc file → skip (likely corruption or first run)
    if len(encrypted_bytes) == 0:
        print("Encrypted file is empty — skipping decryption.")
        return

    decrypted = cipher.decrypt(encrypted_bytes)

    with open(output_path, "wb") as f:
        f.write(decrypted)

    print("Decrypted file created:", os.path.exists(output_path))
