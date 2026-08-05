import json
import os
import base64
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class FrameworkSettings:
    """Configuração centralizada do framework com defaults seguros e tipados."""

    project_root: Path = PROJECT_ROOT
    config_file: Path = CONFIG_FILE
    coupa_base_url: str = os.environ.get("COUPA_BASE_URL", "https://sua-instancia.coupahost.com")
    map_fornecedores: Path = field(default_factory=lambda: Path(os.environ.get("MAP_FORNECEDORES", str(PROJECT_ROOT / "mapeamento_fornecedores.xlsx"))))
    map_unidades: Path = field(default_factory=lambda: Path(os.environ.get("MAP_UNIDADES", str(PROJECT_ROOT / "mapeamento_unidades.xlsx"))))
    pasta_saida_padrao_pdf: Path = field(default_factory=lambda: PROJECT_ROOT / "saida_pedidos_pdf")
    perfil_edge_download: Path = field(default_factory=lambda: Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "CoupaFramework" / "PerfilEdgeDownload")
    historico_renomeador: Path = field(default_factory=lambda: Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "CoupaFramework" / "historico_renomeador.csv")
    url_teste_login: str = ""
    url_base_impressao_pdf: str = ""
    textos_sem_documento: tuple[str, ...] = ("AGUARDE, EM PROCESSAMENTO!",)
    margens_impressao: Dict[str, str] = field(default_factory=lambda: {"top": "0.4in", "bottom": "0.4in", "left": "0.4in", "right": "0.4in"})
    max_tentativas: int = 3
    espera_entre_tentativas: int = 1
    palavras_chave: tuple[str, ...] = ("orçamento", "orcamento", "proposta", "cotação", "cotacao", "quotation", "budget")

    def __post_init__(self) -> None:
        object.__setattr__(self, "url_teste_login", f"{self.coupa_base_url.rstrip('/')}/")
        object.__setattr__(self, "url_base_impressao_pdf", f"{self.coupa_base_url.rstrip('/')}/order_headers/show_custom/{{pedido}}?version=1")


SETTINGS = FrameworkSettings()

COUPA_BASE_URL = SETTINGS.coupa_base_url
MAP_FORNECEDORES = SETTINGS.map_fornecedores
MAP_UNIDADES = SETTINGS.map_unidades
PASTA_SAIDA_PADRAO_PDF = SETTINGS.pasta_saida_padrao_pdf
PERFIL_EDGE_DOWNLOAD = SETTINGS.perfil_edge_download
HISTORICO_RENOMEADOR = SETTINGS.historico_renomeador
URL_TESTE_LOGIN = SETTINGS.url_teste_login
URL_BASE_IMPRESSAO_PDF = SETTINGS.url_base_impressao_pdf
TEXTOS_SEM_DOCUMENTO = SETTINGS.textos_sem_documento
MARGENS_IMPRESSAO = SETTINGS.margens_impressao
MAX_TENTATIVAS = SETTINGS.max_tentativas
ESPERA_ENTRE_TENTATIVAS = SETTINGS.espera_entre_tentativas
PALAVRAS_CHAVE = SETTINGS.palavras_chave


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


# ---- Crypto helpers for ProfileManager ----

def _get_secret() -> bytes:
    """Retorna o segredo usado na derivação da chave de criptografia.

    Melhoria 7: remove o fallback hardcoded "troque-este-valor-no-ambiente".
    Agora:
      1. Usa COUPA_FW_SECRET se definida no ambiente (recomendado).
      2. Caso contrário, gera/persiste uma chave aleatória por máquina no
         arquivo ``coupa_fw.secret`` (na raiz do projeto), evitando chave
         previsível e conhecida publicamente.
    """
    secret_env = os.environ.get("COUPA_FW_SECRET")
    if secret_env:
        return secret_env.encode("utf-8")

    secret_file = PROJECT_ROOT / "coupa_fw.secret"
    try:
        if secret_file.exists():
            return secret_file.read_bytes()
        secret = os.urandom(32)
        secret_file.write_bytes(secret)
        return secret
    except OSError:
        # Se não conseguir persistir, gera uma chave efêmera (perde acesso
        # aos dados criptografados anteriormente, mas não usa segredo fixo).
        return os.urandom(32)


def _derive_key(salt: bytes) -> bytes:
    """Deriva uma chave AES a partir de um salt fixo + identificador da máquina."""
    machine_id = os.environ.get("COMPUTERNAME", "DEFAULT-MACHINE").encode("utf-8")
    # Melhoria 7: usa COUPA_FW_SECRET ou chave aleatória persistente por máquina.
    secret = _get_secret()
    # amazonq-ignore-next-line
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt + machine_id,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret))


def _get_fernet() -> 'Fernet':
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

