# pylint: disable=redefined-outer-name
"""Tests for the file encryption/decryption utilities in lottery_app.utils.encrypted_db."""
from unittest.mock import Mock

import pytest
from cryptography.fernet import Fernet

import lottery_app.utils.encrypted_db as crypto_utils


@pytest.fixture
def fake_cipher():
    """Return a mock cipher that always returns b'encrypted-data' from encrypt."""
    cipher = Mock()
    cipher.encrypt.return_value = b"encrypted-data"
    return cipher


@pytest.fixture
def fake_cipher_decrypt():
    """Return a mock cipher that always returns b'decrypted-data' from decrypt."""
    cipher = Mock()
    cipher.decrypt.return_value = b"decrypted-data"
    return cipher


def test_get_cipher_missing_env(monkeypatch):
    """get_cipher raises RuntimeError when FERNET_KEY is not set."""
    monkeypatch.delenv("FERNET_KEY", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        crypto_utils.get_cipher()

    assert "Missing FERNET_KEY environment variable" in str(excinfo.value)


def test_get_cipher_empty_env(monkeypatch):
    """get_cipher raises RuntimeError when FERNET_KEY is an empty string."""
    monkeypatch.setenv("FERNET_KEY", "")

    with pytest.raises(RuntimeError):
        crypto_utils.get_cipher()


def test_get_cipher_returns_fernet(monkeypatch):
    """get_cipher returns a Fernet instance when a valid key is set."""
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", key)

    cipher = crypto_utils.get_cipher()

    assert isinstance(cipher, Fernet)


def test_get_cipher_uses_correct_key(monkeypatch):
    """The cipher returned by get_cipher uses the key from the environment."""
    key = Fernet.generate_key()
    monkeypatch.setenv("FERNET_KEY", key.decode())

    cipher = crypto_utils.get_cipher()

    token = cipher.encrypt(b"secret-data")
    decrypted = Fernet(key).decrypt(token)

    assert decrypted == b"secret-data"


def test_encrypt_file_success_default_output(tmp_path, monkeypatch, fake_cipher):
    """encrypt_file writes encrypted bytes to <input>.enc by default."""
    input_file = tmp_path / "test.db"
    input_file.write_bytes(b"secret")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher)

    crypto_utils.encrypt_file(str(input_file))

    output_file = tmp_path / "test.db.enc"

    assert output_file.exists()
    assert output_file.read_bytes() == b"encrypted-data"
    fake_cipher.encrypt.assert_called_once_with(b"secret")


def test_encrypt_file_success_custom_output(tmp_path, monkeypatch, fake_cipher):
    """encrypt_file writes to the provided custom output path."""
    input_file = tmp_path / "input.db"
    output_file = tmp_path / "output.enc"
    input_file.write_bytes(b"data")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher)

    crypto_utils.encrypt_file(str(input_file), str(output_file))

    assert output_file.exists()
    assert output_file.read_bytes() == b"encrypted-data"


def test_encrypt_file_input_not_exists(monkeypatch):
    """encrypt_file returns silently when the input file does not exist."""
    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    crypto_utils.encrypt_file("does_not_exist.db")


def test_encrypt_file_empty_file(tmp_path, monkeypatch, capsys):
    """encrypt_file prints a skip message and does nothing for an empty file."""
    input_file = tmp_path / "empty.db"
    input_file.write_bytes(b"")

    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    crypto_utils.encrypt_file(str(input_file))

    captured = capsys.readouterr()
    assert "DB is empty. Skipping encryption." in captured.out


def test_encrypt_file_input_path_not_string(monkeypatch):
    """encrypt_file raises TypeError when input_path is not a string."""
    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    with pytest.raises(TypeError):
        crypto_utils.encrypt_file(123)


def test_encrypt_file_output_path_not_string(tmp_path, monkeypatch):
    """encrypt_file raises TypeError when output_path is not a string."""
    input_file = tmp_path / "data.db"
    input_file.write_bytes(b"data")

    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    with pytest.raises(TypeError):
        crypto_utils.encrypt_file(str(input_file), 123)


def test_encrypt_file_calls_get_cipher(tmp_path, monkeypatch):
    """encrypt_file calls get_cipher exactly once."""
    input_file = tmp_path / "data.db"
    input_file.write_bytes(b"data")

    mock_get_cipher = Mock()
    mock_get_cipher.return_value = Mock(encrypt=lambda x: b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", mock_get_cipher)

    crypto_utils.encrypt_file(str(input_file))

    mock_get_cipher.assert_called_once()


def test_decrypt_file_success_default_output(
    tmp_path, monkeypatch, fake_cipher_decrypt
):
    """decrypt_file writes decrypted bytes to <input minus .enc> by default."""
    enc_file = tmp_path / "data.db.enc"
    enc_file.write_bytes(b"encrypted-bytes")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher_decrypt)

    crypto_utils.decrypt_file(str(enc_file))

    output_file = tmp_path / "data.db"

    assert output_file.exists()
    assert output_file.read_bytes() == b"decrypted-data"
    fake_cipher_decrypt.decrypt.assert_called_once_with(b"encrypted-bytes")


def test_decrypt_file_success_custom_output(tmp_path, monkeypatch, fake_cipher_decrypt):
    """decrypt_file writes to the provided custom output path."""
    enc_file = tmp_path / "input.enc"
    output_file = tmp_path / "output.db"
    enc_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher_decrypt)

    crypto_utils.decrypt_file(str(enc_file), str(output_file))

    assert output_file.exists()
    assert output_file.read_bytes() == b"decrypted-data"


def test_decrypt_file_input_not_exists(monkeypatch):
    """decrypt_file returns silently when the encrypted file does not exist."""
    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    crypto_utils.decrypt_file("missing.enc")


def test_decrypt_file_input_path_not_string(monkeypatch):
    """decrypt_file raises TypeError when input_path is not a string."""
    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    with pytest.raises(TypeError):
        crypto_utils.decrypt_file(123)


def test_decrypt_file_output_path_not_string(tmp_path, monkeypatch):
    """decrypt_file raises TypeError when output_path is not a string."""
    enc_file = tmp_path / "file.enc"
    enc_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    with pytest.raises(TypeError):
        crypto_utils.decrypt_file(str(enc_file), 456)


def test_decrypt_file_missing_enc_extension(tmp_path, monkeypatch):
    """decrypt_file raises ValueError when input has no .enc extension and no output_path."""
    bad_file = tmp_path / "data.db"
    bad_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    with pytest.raises(ValueError):
        crypto_utils.decrypt_file(str(bad_file))


def test_decrypt_file_empty_encrypted_file(tmp_path, monkeypatch, capsys):
    """decrypt_file prints a skip message and does nothing for an empty .enc file."""
    enc_file = tmp_path / "empty.enc"
    enc_file.write_bytes(b"")

    monkeypatch.setattr(crypto_utils, "get_cipher", Mock)

    crypto_utils.decrypt_file(str(enc_file))

    captured = capsys.readouterr()
    assert "Encrypted file is empty — skipping decryption." in captured.out


def test_decrypt_file_calls_get_cipher(tmp_path, monkeypatch):
    """decrypt_file calls get_cipher exactly once."""
    enc_file = tmp_path / "data.enc"
    enc_file.write_bytes(b"encrypted")

    mock_cipher = Mock()
    mock_cipher.decrypt.return_value = b"ok"

    mock_get_cipher = Mock(return_value=mock_cipher)
    monkeypatch.setattr(crypto_utils, "get_cipher", mock_get_cipher)

    crypto_utils.decrypt_file(str(enc_file))

    mock_get_cipher.assert_called_once()


def test_decrypt_file_passes_correct_bytes(tmp_path, monkeypatch):
    """decrypt_file calls cipher.decrypt with the exact bytes read from the file."""
    enc_file = tmp_path / "file.enc"
    enc_file.write_bytes(b"abc123")

    mock_cipher = Mock()
    mock_cipher.decrypt.return_value = b"decoded"

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: mock_cipher)

    crypto_utils.decrypt_file(str(enc_file))

    mock_cipher.decrypt.assert_called_once_with(b"abc123")
