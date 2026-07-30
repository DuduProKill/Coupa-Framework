import json
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

try:
    from dotenv import load_dotenv
    load_dotenv()  # lê o .env da raiz do projeto, se existir (não versionado)
except ImportError:
    pass  # python-dotenv não instalado - segue usando só variáveis de ambiente do sistema

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = PROJECT_ROOT / "coupa_profiles.json"
# Defina COUPA_BASE_URL no ambiente (ou num .env local, nunca commitado) com a
# URL real da sua instância Coupa. Sem isso, cai num placeholder que não aponta pra lugar nenhum.
COUPA_BASE_URL = os.environ.get("COUPA_BASE_URL", "https://sua-instancia.coupahost.com")
MAP_FORNECEDORES = Path(os.environ.get("MAP_FORNECEDORES", str(PROJECT_ROOT / "mapeamento_fornecedores.xlsx")))
MAP_UNIDADES = Path(os.environ.get("MAP_UNIDADES", str(PROJECT_ROOT / "mapeamento_unidades.xlsx")))

# Configurações do Gerador de Pedidos em PDF (Aba 3)
PASTA_SAIDA_PADRAO_PDF = PROJECT_ROOT / "saida_pedidos_pdf"
PERFIL_EDGE_PDF = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "GeradorPedidosCoupaFW" / "PerfilEdgeAutomacao"
URL_TESTE_LOGIN = f"{COUPA_BASE_URL}/"
URL_BASE_IMPRESSAO_PDF = COUPA_BASE_URL + "/order_headers/show_custom/{pedido}?version=1"
TEXTOS_SEM_DOCUMENTO = ["AGUARDE, EM PROCESSAMENTO!"]
MARGENS_IMPRESSAO = {"top": "0.4in", "bottom": "0.4in", "left": "0.4in", "right": "0.4in"}

MAX_TENTATIVAS = 1
ESPERA_ENTRE_TENTATIVAS = 1

PALAVRAS_CHAVE = ["orçamento", "orcamento", "proposta", "cotação", "cotacao", "quotation", "budget"]


def resolve_edge_executable() -> str | None:
    candidates = [
        os.environ.get("EDGE_EXECUTABLE_PATH"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(Path(candidate))
    return None


DEFAULT_COUPA_PROFILE_DIR = Path.home() / "Coupa_Bot_Profile"

# ---- Crypto helpers for ProfileManager ----

def _derive_key(salt: bytes) -> bytes:
    """Deriva uma chave AES a partir de um salt fixo + identificador da máquina."""
    machine_id = os.environ.get("COMPUTERNAME", "DEFAULT-MACHINE").encode("utf-8")
    # Defina COUPA_FW_SECRET no ambiente pra não depender do fallback abaixo.
    secret = os.environ.get("COUPA_FW_SECRET", "troque-este-valor-no-ambiente").encode("utf-8")
    # amazonq-ignore-next-line
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt + machine_id,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret))


def _get_fernet() -> Fernet:
    salt_file = CONFIG_FILE.with_suffix(".salt")
    if salt_file.exists():
        salt = salt_file.read_bytes()
    else:
        salt = os.urandom(16)
        salt_file.write_bytes(salt)
    return Fernet(_derive_key(salt))


SENSITIVE_FIELDS = ["comprador_email", "template", "sender", "password"]


def encrypt_value(plaintext: str) -> str:
    """Criptografa um valor sensível."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Descriptografa um valor sensível."""
    if not ciphertext:
        return ciphertext
    # Valores em texto plano não começam com o prefixo Fernet - retorna sem tentar descriptografar
    if not ciphertext.startswith("gAAAA"):
        return ciphertext
    try:
        f = _get_fernet()
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("decrypt_value falhou: %s", e)
        return ciphertext


def encrypt_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Percorre o config e criptografa campos sensíveis."""
    encrypted = dict(config)
    for field in SENSITIVE_FIELDS:
        if field in encrypted and encrypted[field]:
            encrypted[field] = encrypt_value(str(encrypted[field]))
    return encrypted

# amazonq-ignore-next-line

def decrypt_sensitive_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Percorre o config e descriptografa campos sensíveis."""
    decrypted = dict(config)
    for field in SENSITIVE_FIELDS:
        if field in decrypted and decrypted[field]:
            decrypted[field] = decrypt_value(str(decrypted[field]))
    return decrypted


class ProfileManager:
    @staticmethod
    def load_profiles() -> Dict[str, Any]:
        """Carrega perfis do arquivo JSON com descriptografia de campos sensíveis."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    raw_profiles = json.load(f)
                # Descriptografa os configs sensíveis de cada perfil
                for profile_name, profile_data in raw_profiles.items():
                    if "config" in profile_data:
                        profile_data["config"] = decrypt_sensitive_config(profile_data["config"])
                return raw_profiles
            except (json.JSONDecodeError, OSError, KeyError) as e:
                import logging
                logging.getLogger(__name__).error("Erro ao carregar perfis: %s", e)
                return {}
        return {}

    @staticmethod
    def save_profiles(profiles: Dict[str, Any]):
        """Salva perfis no arquivo JSON com criptografia de campos sensíveis."""
        # Criptografa os configs sensíveis de cada perfil antes de salvar
        encrypted_profiles = {}
        for profile_name, profile_data in profiles.items():
            encrypted_data = dict(profile_data)
            if "config" in encrypted_data:
                encrypted_data["config"] = encrypt_sensitive_config(encrypted_data["config"])
            encrypted_profiles[profile_name] = encrypted_data

        temp_path = CONFIG_FILE.with_suffix(CONFIG_FILE.suffix + ".tmp")
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(encrypted_profiles, f, indent=4, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Usa os.replace() que é atômico no Windows e sobrescreve sem PermissionError
        os.replace(str(temp_path), str(CONFIG_FILE))

