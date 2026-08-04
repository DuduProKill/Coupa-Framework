import subprocess
import sys
import tempfile
from pathlib import Path

import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QStatusBar,
    QLabel, QVBoxLayout, QWidget, QMessageBox, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from modules import (
    CoupaExtractorWidget, OrcamentoDownloaderWidget,
    PedidoPdfGeneratorWidget, RenomeadorWidget, OrganizadorWidget,
    EmailSenderWidget, ProfileManagerWidget
)
from modules.styles import APP_STYLESHEET
from modules.playwright_pool import cleanup_playwright_pool
from modules.updater import UpdateManager
from modules.feature_selection import is_module_enabled


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
    def __init__(self, parent, module_key: str, module_label: str):
        super().__init__(parent)
        self.module_key = module_key
        self.module_label = module_label

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        icon_label = QLabel("🔒")
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"Módulo indisponível")
        title.setStyleSheet("font-size: 20px; font-weight: 700;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            f"O módulo <b>{module_label}</b> não está instalado neste cliente."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description, alignment=Qt.AlignmentFlag.AlignCenter)

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
        self.tab_coupa = CoupaExtractorWidget(self) if is_module_enabled("extrator") else None
        self.tab_downloader = OrcamentoDownloaderWidget(self) if is_module_enabled("downloader") else None
        self.tab_pdf_generator = PedidoPdfGeneratorWidget(self) if is_module_enabled("pdf") else None
        self.tab_renomeador = RenomeadorWidget(self) if is_module_enabled("renomeador") else None
        self.tab_organizador = OrganizadorWidget(self) if is_module_enabled("organizador") else None
        self.tab_email_sender = EmailSenderWidget(self) if is_module_enabled("email") else None
        self.tab_manage_profiles = ProfileManagerWidget(self) if is_module_enabled("perfis") else None

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

    def _add_locked_tab(self, module_key: str, label: str):
        widget = LockedModuleWidget(self, module_key, label)
        self.locked_tabs.append((module_key, widget))
        self.tab_widget.addTab(widget, build_tab_title(module_key, False))

    def _on_tab_changed(self, index: int):
        tab_text = self.tab_widget.tabText(index).strip()
        self.lbl_status.setText(f"Aba ativa: {tab_text}")

    def _on_locked_tab_selected(self, index: int):
        for module_key, widget in self.locked_tabs:
            if self.tab_widget.widget(index) is widget:
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
