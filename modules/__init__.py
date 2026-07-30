"""Módulo do framework de automação Coupa.

Exporta todas as classes públicas para imports simplificados.
Use: from modules import CoupaExtractorWidget, OrcamentoDownloaderWidget, ...
"""

# Widgets de Interface
from modules.ui_coupa import CoupaExtractorWidget
from modules.ui_downloader import OrcamentoDownloaderWidget
from modules.ui_pdf_generator import PedidoPdfGeneratorWidget
from modules.ui_renomeador import RenomeadorWidget
from modules.ui_organizador import OrganizadorWidget
from modules.ui_email_sender import EmailSenderWidget
from modules.ui_profile_manager import ProfileManagerWidget

# Workers
from modules.coupa_scraper import CoupaScraper, AutomationWorker
from modules.download_scraper import DownloadScraper, DownloadWorker
from modules.email_sender import EmailWorker
from modules.pdf_generator import PdfGeneratorWorker

# Lógica de Negócio
from modules.organizador import Organizador
from modules.config import ProfileManager

# Fluxo Automático
from modules.fluxo_orquestrador import AutomaticFlowRunner, ModoAutomatico

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
