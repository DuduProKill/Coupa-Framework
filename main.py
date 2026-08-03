import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QStatusBar,
    QLabel, QVBoxLayout, QWidget
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
        self.tab_coupa = CoupaExtractorWidget(self)
        self.tab_downloader = OrcamentoDownloaderWidget(self)
        self.tab_pdf_generator = PedidoPdfGeneratorWidget(self)
        self.tab_renomeador = RenomeadorWidget(self)
        self.tab_organizador = OrganizadorWidget(self)
        self.tab_email_sender = EmailSenderWidget(self)
        self.tab_manage_profiles = ProfileManagerWidget(self)

        # Adiciona os módulos ao Framework
        self.tab_widget.addTab(self.tab_coupa, "\U0001f4e6  Extrator Inteligente")
        self.tab_widget.addTab(self.tab_downloader, "\U0001f4e5  Baixador de Or\u00e7amentos")
        self.tab_widget.addTab(self.tab_pdf_generator, "\U0001f4c4  Gerador de PDF de Pedidos")
        self.tab_widget.addTab(self.tab_renomeador, "\U0001f4dd  Renomeador")
        self.tab_widget.addTab(self.tab_organizador, "\U0001f5c2\u200d\ufe0f  Organizador")
        self.tab_widget.addTab(self.tab_email_sender, "\U0001f4e7  Disparo de E-mails")
        self.tab_widget.addTab(self.tab_manage_profiles, "\U0001f465  Gerenciar Perfis")

        # Conectar troca de aba para atualizar status
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Sincronizar perfis entre abas
        self.tab_manage_profiles.profiles_changed.connect(self.tab_coupa.refresh_profiles)
        self.tab_manage_profiles.profiles_changed.connect(self.tab_email_sender.refresh_profiles)

        # Verifica atualizações em background via QThread (UI sempre na thread principal)
        self._update_manager = UpdateManager(self)
        self._update_manager.start()

    def _on_tab_changed(self, index: int):
        tab_text = self.tab_widget.tabText(index).strip()
        self.lbl_status.setText(f"Aba ativa: {tab_text}")

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
