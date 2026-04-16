"""
Database encryption and decryption utilities using Fernet symmetric encryption.

Provides helper functions to encrypt and decrypt the SQLite database file
at application startup and shutdown.
"""

import logging
import os
import tempfile

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


def get_cipher():
    """
    Build and return a Fernet cipher instance using the FERNET_KEY environment variable.

    Returns:
        Fernet: A ready-to-use cipher object.

    Raises:
        RuntimeError: If the FERNET_KEY environment variable is not set.
    """
    key = os.getenv("FERNET_KEY")
    if not key:
        raise RuntimeError("Missing FERNET_KEY environment variable")
    return Fernet(key.encode())


def encrypt_file(input_path, output_path=None):
    """
    Encrypt a file using Fernet symmetric encryption.

    Args:
        input_path (str): Path to the plaintext file to encrypt.
        output_path (str, optional): Destination path for the encrypted file.
            Defaults to ``input_path + '.enc'`` if not provided.

    Raises:
        TypeError: If either path argument is not a string.

    Notes:
        Silently skips encryption if the input file does not exist or is empty.
    """
    if not isinstance(input_path, str):
        raise TypeError("input_path must be a string")

    if output_path is not None and not isinstance(output_path, str):
        raise TypeError("output_path must be a string")

    if not os.path.exists(input_path):
        return

    if os.path.getsize(input_path) == 0:
        logger.debug("DB is empty. Skipping encryption.")
        return

    cipher = get_cipher()

    if output_path is None:
        output_path = input_path + ".enc"

    with open(input_path, "rb") as f:
        data = f.read()
    encrypted = cipher.encrypt(data)

    # Write to a temporary file in the same directory, then atomically
    # replace the destination.  os.replace() is atomic on POSIX (same
    # filesystem), so a crash mid-write never leaves a corrupt .enc file.
    enc_dir = os.path.dirname(output_path) or "."
    with tempfile.NamedTemporaryFile(dir=enc_dir, delete=False, suffix=".tmp") as tmp:
        tmp.write(encrypted)
        tmp_path = tmp.name
    os.replace(tmp_path, output_path)

    logger.debug("Encrypted file created: %s", output_path)


def decrypt_file(input_path, output_path=None):
    """
    Decrypt a Fernet-encrypted file.

    Args:
        input_path (str): Path to the encrypted ``.enc`` file.
        output_path (str, optional): Destination path for the decrypted file.
            If omitted, the ``.enc`` suffix is stripped from ``input_path``.

    Raises:
        TypeError: If either path argument is not a string.
        ValueError: If ``input_path`` does not end with ``.enc`` and no
            ``output_path`` is provided.

    Notes:
        Silently skips decryption if the input file does not exist or is empty,
        to handle first-run and corruption edge cases gracefully.
    """
    cipher = get_cipher()

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

    with open(input_path, "rb") as f:
        encrypted_bytes = f.read()

    # Safety: empty .enc file → skip (likely corruption or first run)
    if len(encrypted_bytes) == 0:
        logger.warning("Encrypted file is empty — skipping decryption.")
        return

    decrypted = cipher.decrypt(encrypted_bytes)

    with open(output_path, "wb") as f:
        f.write(decrypted)

    logger.debug("Decrypted file created: %s", output_path)
