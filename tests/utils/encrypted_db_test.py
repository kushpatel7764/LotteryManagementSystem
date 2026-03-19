import pytest
from cryptography.fernet import Fernet
from unittest.mock import Mock

import lottery_app.utils.encrypted_db as crypto_utils


# Helper: fake cipher
@pytest.fixture
def fake_cipher():
    cipher = Mock()
    cipher.encrypt.return_value = b"encrypted-data"
    return cipher


@pytest.fixture
def fake_cipher_decrypt():
    cipher = Mock()
    cipher.decrypt.return_value = b"decrypted-data"
    return cipher


# Test for missing FERNET_KEY environment variable
def test_get_cipher_missing_env(monkeypatch):
    monkeypatch.delenv("FERNET_KEY", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        crypto_utils.get_cipher()

    assert "Missing FERNET_KEY environment variable" in str(excinfo.value)


# Test: raises error when env var is missing
def test_get_cipher_missing_env(monkeypatch):
    monkeypatch.delenv("FERNET_KEY", raising=False)

    with pytest.raises(RuntimeError) as excinfo:
        crypto_utils.get_cipher()

    assert "Missing FERNET_KEY environment variable" in str(excinfo.value)


# Test: raises error when env var is empty string
def test_get_cipher_empty_env(monkeypatch):
    monkeypatch.setenv("FERNET_KEY", "")

    with pytest.raises(RuntimeError):
        crypto_utils.get_cipher()


# Test: returns Fernet instance when key exists
def test_get_cipher_returns_fernet(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("FERNET_KEY", key)

    cipher = crypto_utils.get_cipher()

    assert isinstance(cipher, Fernet)


# This ensures the key was actually used, not just any Fernet instance.
def test_get_cipher_uses_correct_key(monkeypatch):
    key = Fernet.generate_key()
    monkeypatch.setenv("FERNET_KEY", key.decode())

    cipher = crypto_utils.get_cipher()

    token = cipher.encrypt(b"secret-data")
    decrypted = Fernet(key).decrypt(token)

    assert decrypted == b"secret-data"


# Test: successful encryption (default output path)
def test_encrypt_file_success_default_output(tmp_path, monkeypatch, fake_cipher):
    input_file = tmp_path / "test.db"
    input_file.write_bytes(b"secret")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher)

    crypto_utils.encrypt_file(str(input_file))

    output_file = tmp_path / "test.db.enc"

    assert output_file.exists()
    assert output_file.read_bytes() == b"encrypted-data"
    fake_cipher.encrypt.assert_called_once_with(b"secret")


# Test: successful encryption with custom output path
def test_encrypt_file_success_custom_output(tmp_path, monkeypatch, fake_cipher):
    input_file = tmp_path / "input.db"
    output_file = tmp_path / "output.enc"
    input_file.write_bytes(b"data")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher)

    crypto_utils.encrypt_file(str(input_file), str(output_file))

    assert output_file.exists()
    assert output_file.read_bytes() == b"encrypted-data"


# Test: input file does not exist → returns silently
def test_encrypt_file_input_not_exists(monkeypatch):
    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    # Should not raise
    crypto_utils.encrypt_file("does_not_exist.db")


# Test: empty input file → skip encryption
def test_encrypt_file_empty_file(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "empty.db"
    input_file.write_bytes(b"")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    crypto_utils.encrypt_file(str(input_file))

    captured = capsys.readouterr()
    assert "DB is empty. Skipping encryption." in captured.out


# Test: input_path not a string
def test_encrypt_file_input_path_not_string(monkeypatch):
    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    with pytest.raises(TypeError):
        crypto_utils.encrypt_file(123)


# Test: output_path not a string
def test_encrypt_file_output_path_not_string(tmp_path, monkeypatch):
    input_file = tmp_path / "data.db"
    input_file.write_bytes(b"data")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    with pytest.raises(TypeError):
        crypto_utils.encrypt_file(str(input_file), 123)


# Test: get_cipher is called
def test_encrypt_file_calls_get_cipher(tmp_path, monkeypatch):
    input_file = tmp_path / "data.db"
    input_file.write_bytes(b"data")

    mock_get_cipher = Mock()
    mock_get_cipher.return_value = Mock(encrypt=lambda x: b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", mock_get_cipher)

    crypto_utils.encrypt_file(str(input_file))

    mock_get_cipher.assert_called_once()


# Test: successful decrypt (default output path)
def test_decrypt_file_success_default_output(
    tmp_path, monkeypatch, fake_cipher_decrypt
):
    enc_file = tmp_path / "data.db.enc"
    enc_file.write_bytes(b"encrypted-bytes")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher_decrypt)

    crypto_utils.decrypt_file(str(enc_file))

    output_file = tmp_path / "data.db"

    assert output_file.exists()
    assert output_file.read_bytes() == b"decrypted-data"
    fake_cipher_decrypt.decrypt.assert_called_once_with(b"encrypted-bytes")


# Test: successful decrypt with custom output path
def test_decrypt_file_success_custom_output(tmp_path, monkeypatch, fake_cipher_decrypt):
    enc_file = tmp_path / "input.enc"
    output_file = tmp_path / "output.db"
    enc_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: fake_cipher_decrypt)

    crypto_utils.decrypt_file(str(enc_file), str(output_file))

    assert output_file.exists()
    assert output_file.read_bytes() == b"decrypted-data"


# Test: input file does not exist → silent return
def test_decrypt_file_input_not_exists(monkeypatch):
    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    # Should not raise
    crypto_utils.decrypt_file("missing.enc")


# Test: input_path not a string
def test_decrypt_file_input_path_not_string(monkeypatch):
    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    with pytest.raises(TypeError):
        crypto_utils.decrypt_file(123)


# Test: output_path not a string
def test_decrypt_file_output_path_not_string(tmp_path, monkeypatch):
    enc_file = tmp_path / "file.enc"
    enc_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    with pytest.raises(TypeError):
        crypto_utils.decrypt_file(str(enc_file), 456)


# Test: missing .enc extension and no output_path
def test_decrypt_file_missing_enc_extension(tmp_path, monkeypatch):
    bad_file = tmp_path / "data.db"
    bad_file.write_bytes(b"encrypted")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    with pytest.raises(ValueError):
        crypto_utils.decrypt_file(str(bad_file))


# Test: empty encrypted file → skip decryption
def test_decrypt_file_empty_encrypted_file(tmp_path, monkeypatch, capsys):
    enc_file = tmp_path / "empty.enc"
    enc_file.write_bytes(b"")

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: Mock())

    crypto_utils.decrypt_file(str(enc_file))

    captured = capsys.readouterr()
    assert "Encrypted file is empty — skipping decryption." in captured.out


# Test: get_cipher is called
def test_decrypt_file_calls_get_cipher(tmp_path, monkeypatch):
    enc_file = tmp_path / "data.enc"
    enc_file.write_bytes(b"encrypted")

    mock_cipher = Mock()
    mock_cipher.decrypt.return_value = b"ok"

    mock_get_cipher = Mock(return_value=mock_cipher)
    monkeypatch.setattr(crypto_utils, "get_cipher", mock_get_cipher)

    crypto_utils.decrypt_file(str(enc_file))

    mock_get_cipher.assert_called_once()


# Test: decrypt is called with exact bytes
def test_decrypt_file_passes_correct_bytes(tmp_path, monkeypatch):
    enc_file = tmp_path / "file.enc"
    enc_file.write_bytes(b"abc123")

    mock_cipher = Mock()
    mock_cipher.decrypt.return_value = b"decoded"

    monkeypatch.setattr(crypto_utils, "get_cipher", lambda: mock_cipher)

    crypto_utils.decrypt_file(str(enc_file))

    mock_cipher.decrypt.assert_called_once_with(b"abc123")
