"""Módulo do framework de automação Coupa.

Exporta todas as classes públicas para imports simplificados.
Use: from modules import CoupaExtractorWidget, OrcamentoDownloaderWidget, ...
"""

import importlib


def _safe_import(attr_name: str, module_name: str):
    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr_name)
    except Exception:
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
