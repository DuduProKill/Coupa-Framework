import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QStatusBar,
    QLabel, QVBoxLayout, QWidget, QMessageBox, QPushButton, QHBoxLayout,
    QTextEdit
)
from PyQt6.QtCore import Qt
from modules import (
    CoupaExtractorWidget, OrcamentoDownloaderWidget,
    PedidoPdfGeneratorWidget, RenomeadorWidget, OrganizadorWidget,
    EmailSenderWidget, ProfileManagerWidget, IMPORT_ERRORS
)
from modules.styles import APP_STYLESHEET
from modules.playwright_pool import cleanup_playwright_pool
from modules.updater import UpdateManager
from modules.feature_selection import is_module_enabled


# Mapeia a chave do módulo (usada em feature_selection) para o nome da classe
# widget correspondente (usada como chave em modules.IMPORT_ERRORS).
MODULE_KEY_TO_WIDGET_CLASS = {
    "extrator": "CoupaExtractorWidget",
    "downloader": "OrcamentoDownloaderWidget",
    "pdf": "PedidoPdfGeneratorWidget",
    "renomeador": "RenomeadorWidget",
    "organizador": "OrganizadorWidget",
    "email": "EmailSenderWidget",
    "perfis": "ProfileManagerWidget",
}


def build_tab_title(module_key: str, enabled: bool) -> str:
    titles = {
        "extrator": "📦 Extrator Inteligente",
        "downloader": "📥 Baixador de Orçamentos",
        "pdf": "📄 Gerador de PDF de Pedidos",
        "renomeador": "📝 Renomeador",
        "organizador": "🗂️ Organizador",
        "email": "📧 Disparo de E-mails",
        "perfis": "👥 Gerenciar Perfis",
    }
    base_title = titles.get(module_key, module_key)
    return f"🔒 {base_title}" if not enabled else base_title


class LockedModuleWidget(QWidget):
    def __init__(self, parent, module_key: str, module_label: str, error_detail: str | None = None):
        super().__init__(parent)
        self.module_key = module_key
        self.module_label = module_label
        self.error_detail = error_detail

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        icon_label = QLabel("🔒")
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"Módulo indisponível")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        if error_detail:
            # Módulo deveria estar disponível, mas falhou ao carregar (dependência
            # ausente, erro de import, etc). Mostra o motivo real em vez de
            # apenas dizer "não instalado" — isso ajuda a diagnosticar no cliente.
            description = QLabel(
                f"O módulo <b>{module_label}</b> não pôde ser carregado neste PC "
                f"devido a um erro interno (veja detalhes abaixo)."
            )
        else:
            description = QLabel(
                f"O módulo <b>{module_label}</b> não está instalado neste cliente."
            )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description, alignment=Qt.AlignmentFlag.AlignCenter)

        if error_detail:
            error_box = QTextEdit()
            error_box.setReadOnly(True)
            error_box.setPlainText(error_detail)
            error_box.setFixedHeight(160)
            error_box.setStyleSheet(
                "font-family: Consolas, monospace; font-size: 11px; color: #ff7b72;"
            )
            layout.addWidget(error_box)

        if not error_detail:
            # Só faz sentido oferecer "baixar módulo" quando o módulo de fato não
            # está instalado — não quando ele falhou ao carregar por um erro interno.
            button_row = QWidget()
            button_row_layout = QHBoxLayout(button_row)
            button_row_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button_row_layout.addStretch()

            self.download_button = QPushButton("Baixar este módulo")
            self.download_button.clicked.connect(self._on_download_requested)
            button_row_layout.addWidget(self.download_button)
            button_row_layout.addStretch()
            layout.addWidget(button_row)
        layout.addStretch()

    def _on_download_requested(self):
        self.parent().request_module_install(self.module_key)


class FrameworkApp(QMainWindow):
    def __init__(self):
        super(FrameworkApp, self).__init__()
        self.setWindowTitle("Coupa Framework - Automação de Suprimentos")
        self.setGeometry(100, 100, 1400, 920)
        self.setMinimumSize(1024, 720)

        # --- Header / Top Bar ---
        header = QWidget()
        header.setObjectName("appHeader")
        header.setFixedHeight(56)
        header.setStyleSheet("""
            QWidget#appHeader {
                background: #161b22;
                border-bottom: 2px solid #1f6feb;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)

        self.lbl_header_title = QLabel("\U0001f310 Coupa Framework - Automação de Suprimentos")
        self.lbl_header_title.setStyleSheet("""
            color: #f0f6fc;
            font-size: 17px;
            font-weight: 700;
        """)
        header_layout.addWidget(self.lbl_header_title)

        # --- Tab Widget ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Central widget wrapping header + tabs
        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(header)
        central_layout.addWidget(self.tab_widget, 1)
        self.setCentralWidget(central)

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background: #161b22;
                color: #8b949e;
                font-size: 13px;
                padding: 4px 16px;
                border-top: 1px solid #30363d;
            }
            QStatusBar::item { border: none; }
        """)
        self.lbl_status = QLabel("Pronto")
        self.status_bar.addWidget(self.lbl_status)
        self.setStatusBar(self.status_bar)

        # Instanciação das Abas
        # Importante: só instanciamos se a classe realmente importou (não é None).
        # Se um widget falhou ao importar (dependência ausente no PC, por ex.),
        # ele cai automaticamente na aba bloqueada em vez de derrubar o app inteiro.
        self.tab_coupa = self._safe_instantiate(CoupaExtractorWidget, "extrator")
        self.tab_downloader = self._safe_instantiate(OrcamentoDownloaderWidget, "downloader")
        self.tab_pdf_generator = self._safe_instantiate(PedidoPdfGeneratorWidget, "pdf")
        self.tab_renomeador = self._safe_instantiate(RenomeadorWidget, "renomeador")
        self.tab_organizador = self._safe_instantiate(OrganizadorWidget, "organizador")
        self.tab_email_sender = self._safe_instantiate(EmailSenderWidget, "email")
        self.tab_manage_profiles = self._safe_instantiate(ProfileManagerWidget, "perfis")

        self.locked_tabs = []

        # Adiciona os módulos ao Framework
        if self.tab_coupa is not None:
            self.tab_widget.addTab(self.tab_coupa, "📦  Extrator Inteligente")
        else:
            self._add_locked_tab("extrator", "📦 Extrator Inteligente")
        if self.tab_downloader is not None:
            self.tab_widget.addTab(self.tab_downloader, "📥  Baixador de Orçamentos")
        else:
            self._add_locked_tab("downloader", "📥 Baixador de Orçamentos")
        if self.tab_pdf_generator is not None:
            self.tab_widget.addTab(self.tab_pdf_generator, "📄  Gerador de PDF de Pedidos")
        else:
            self._add_locked_tab("pdf", "📄 Gerador de PDF de Pedidos")
        if self.tab_renomeador is not None:
            self.tab_widget.addTab(self.tab_renomeador, "📝  Renomeador")
        else:
            self._add_locked_tab("renomeador", "📝 Renomeador")
        if self.tab_organizador is not None:
            self.tab_widget.addTab(self.tab_organizador, "🗂️  Organizador")
        else:
            self._add_locked_tab("organizador", "🗂️ Organizador")
        if self.tab_email_sender is not None:
            self.tab_widget.addTab(self.tab_email_sender, "📧  Disparo de E-mails")
        else:
            self._add_locked_tab("email", "📧 Disparo de E-mails")
        if self.tab_manage_profiles is not None:
            self.tab_widget.addTab(self.tab_manage_profiles, "👥  Gerenciar Perfis")
        else:
            self._add_locked_tab("perfis", "👥 Gerenciar Perfis")

        # Conectar troca de aba para atualizar status
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.currentChanged.connect(self._on_locked_tab_selected)

        # Sincronizar perfis entre abas quando os módulos estiverem disponíveis
        if self.tab_manage_profiles is not None and self.tab_coupa is not None:
            self.tab_manage_profiles.profiles_changed.connect(self.tab_coupa.refresh_profiles)
        if self.tab_manage_profiles is not None and self.tab_email_sender is not None:
            self.tab_manage_profiles.profiles_changed.connect(self.tab_email_sender.refresh_profiles)

        # Verifica atualizações em background via QThread (UI sempre na thread principal)
        self._update_manager = UpdateManager(self)
        self._update_manager.start()

    def _safe_instantiate(self, widget_class, module_key: str):
        """Instancia o widget somente se a classe carregou de verdade (não é None)
        e o módulo está habilitado. Nunca chama None(...), que é o que causava o
        'NoneType' object is not callable ao rodar em outra máquina."""
        if widget_class is None:
            return None
        if not is_module_enabled(module_key):
            return None
        try:
            return widget_class(self)
        except Exception:
            error_text = traceback.format_exc()
            IMPORT_ERRORS[module_key] = error_text
            print(f"[ERRO] Falha ao inicializar o módulo '{module_key}':\n{error_text}")
            return None

    def _add_locked_tab(self, module_key: str, label: str):
        widget_class_name = MODULE_KEY_TO_WIDGET_CLASS.get(module_key, module_key)
        error_detail = IMPORT_ERRORS.get(widget_class_name) or IMPORT_ERRORS.get(module_key)
        widget = LockedModuleWidget(self, module_key, label, error_detail=error_detail)
        self.locked_tabs.append((module_key, widget))
        self.tab_widget.addTab(widget, build_tab_title(module_key, False))

    def _on_tab_changed(self, index: int):
        tab_text = self.tab_widget.tabText(index).strip()
        self.lbl_status.setText(f"Aba ativa: {tab_text}")

    def _on_locked_tab_selected(self, index: int):
        for module_key, widget in self.locked_tabs:
            if self.tab_widget.widget(index) is widget:
                if not getattr(widget, "error_detail", None):
                    self.request_module_install(module_key)
                break

    def request_module_install(self, module_key: str):
        try:
            installer_path = self._find_installer_for_module(module_key)
            if installer_path is None:
                QMessageBox.information(
                    self,
                    "Módulo indisponível",
                    f"O instalador para o módulo '{module_key}' não foi encontrado localmente."
                    "\nA instalação será iniciada assim que o pacote estiver disponível."
                )
                return

            subprocess.Popen(
                [installer_path, f"/MODULE={module_key}"],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
            )
            self.lbl_status.setText(f"Iniciando instalação do módulo: {module_key}")
            QMessageBox.information(
                self,
                "Instalação iniciada",
                "O instalador do módulo foi aberto. Complete a instalação para habilitar esta aba."
            )
        except OSError as exc:
            QMessageBox.critical(self, "Erro ao iniciar instalação", str(exc))

    def _find_installer_for_module(self, module_key: str) -> str | None:
        app_dir = Path(sys.executable).resolve().parent
        local_candidates = [
            app_dir / "CoupaFramework_Setup_v1.1.1.exe",
            app_dir / "installer.exe",
            app_dir.parent / "installer_output" / "CoupaFramework_Setup_v1.1.1.exe",
        ]
        for candidate in local_candidates:
            if candidate.exists():
                return str(candidate)

        try:
            response = requests.get(
                "https://api.github.com/repos/DuduProKill/Coupa-Framework/releases/latest",
                timeout=10,
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            data = response.json()
            asset = next(
                (
                    asset for asset in data.get("assets", [])
                    if isinstance(asset, dict) and asset.get("name", "").endswith(".exe")
                ),
                None,
            )
            if not asset:
                return None

            temp_path = Path(tempfile.gettempdir()) / asset["name"]
            download_response = requests.get(asset.get("browser_download_url"), timeout=60)
            download_response.raise_for_status()
            temp_path.write_bytes(download_response.content)
            return str(temp_path)
        except (requests.RequestException, OSError, ValueError):
            return None

    def set_status(self, message: str):
        self.lbl_status.setText(message)

    def closeEvent(self, event):
        """Item 3: Libera todos os contextos do PlaywrightPool ao fechar o app."""
        cleanup_playwright_pool()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLESHEET)
    window = FrameworkApp()
    window.show()
    sys.exit(app.exec())