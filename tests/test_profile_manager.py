import json
import pytest
from pathlib import Path
from unittest.mock import patch

from modules.config import ProfileManager, encrypt_value, decrypt_value


def test_encrypt_decrypt_roundtrip():
    original = "senha_secreta"
    encrypted = encrypt_value(original)
    assert encrypted != original
    assert decrypt_value(encrypted) == original


def test_decrypt_plaintext_passthrough():
    # Valores sem prefixo Fernet devem ser retornados sem erro
    assert decrypt_value("texto_plano") == "texto_plano"


def test_save_and_load_profiles(tmp_path):
    config_path = tmp_path / "profiles.json"
    salt_path = tmp_path / "profiles.salt"

    profiles = {
        "Perfil Teste": {
            "config": {
                "sender": "user@example.com",
                "password": "secret123",
                "criado_por": True,
            }
        }
    }

    with patch("modules.config.CONFIG_FILE", config_path), \
         patch("modules.config.salt_file", salt_path, create=True):
        ProfileManager.save_profiles(profiles)
        loaded = ProfileManager.load_profiles()

    assert "Perfil Teste" in loaded
    assert loaded["Perfil Teste"]["config"]["sender"] == "user@example.com"
    assert loaded["Perfil Teste"]["config"]["password"] == "secret123"


def test_load_profiles_missing_file(tmp_path):
    with patch("modules.config.CONFIG_FILE", tmp_path / "nao_existe.json"):
        result = ProfileManager.load_profiles()
    assert result == {}
