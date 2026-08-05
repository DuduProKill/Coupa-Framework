"""Módulo do framework de automação Coupa.

Exporta todas as classes públicas para imports simplificados.
Use: from modules import CoupaExtractorWidget, OrcamentoDownloaderWidget, ...
"""

import importlib
import logging
import os
import traceback
from pathlib import Path

# Registro dos erros reais de import, por nome de atributo (widget/worker).
# main.py consulta isso para saber POR QUE um módulo veio None, em vez de
# simplesmente tentar instanciar None e crashar.
IMPORT_ERRORS: dict[str, str] = {}


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("CoupaFramework.imports")
    if logger.handlers:
        return logger
    try:
        log_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "CoupaFramework" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_dir / "import_errors.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(logging.ERROR)
    except Exception:
        pass  # se nem o log conseguir ser criado, seguimos sem travar o app
    return logger


def _safe_import(attr_name: str, module_name: str):
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    except Exception:
        err_text = traceback.format_exc()
        IMPORT_ERRORS[attr_name] = err_text
        _get_logger().error("Falha ao importar '%s' de '%s':\n%s", attr_name, module_name, err_text)
        return None


# Widgets de Interface
CoupaExtractorWidget = _safe_import("CoupaExtractorWidget", "modules.ui_coupa")
OrcamentoDownloaderWidget = _safe_import("OrcamentoDownloaderWidget", "modules.ui_downloader")
PedidoPdfGeneratorWidget = _safe_import("PedidoPdfGeneratorWidget", "modules.ui_pdf_generator")
RenomeadorWidget = _safe_import("RenomeadorWidget", "modules.ui_renomeador")
OrganizadorWidget = _safe_import("OrganizadorWidget", "modules.ui_organizador")
EmailSenderWidget = _safe_import("EmailSenderWidget", "modules.ui_email_sender")
ProfileManagerWidget = _safe_import("ProfileManagerWidget", "modules.ui_profile_manager")

# Workers
CoupaScraper = _safe_import("CoupaScraper", "modules.coupa_scraper")
AutomationWorker = _safe_import("AutomationWorker", "modules.coupa_scraper")
DownloadScraper = _safe_import("DownloadScraper", "modules.download_scraper")
DownloadWorker = _safe_import("DownloadWorker", "modules.download_scraper")
EmailWorker = _safe_import("EmailWorker", "modules.email_sender")
PdfGeneratorWorker = _safe_import("PdfGeneratorWorker", "modules.pdf_generator")

# Lógica de Negócio
Organizador = _safe_import("Organizador", "modules.organizador")
ProfileManager = _safe_import("ProfileManager", "modules.config")

# Fluxo Automático
AutomaticFlowRunner = _safe_import("AutomaticFlowRunner", "modules.fluxo_orquestrador")
ModoAutomatico = _safe_import("ModoAutomatico", "modules.fluxo_orquestrador")

__all__ = [
    # Widgets
    "CoupaExtractorWidget",
    "OrcamentoDownloaderWidget",
    "PedidoPdfGeneratorWidget",
    "RenomeadorWidget",
    "OrganizadorWidget",
    "EmailSenderWidget",
    "ProfileManagerWidget",
    # Workers
    "CoupaScraper",
    "AutomationWorker",
    "DownloadScraper",
    "DownloadWorker",
    "EmailWorker",
    "PdfGeneratorWorker",
    # Lógica
    "Organizador",
    "ProfileManager",
    # Fluxo
    "AutomaticFlowRunner",
    "ModoAutomatico",
]
