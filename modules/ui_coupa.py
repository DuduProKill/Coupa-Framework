import re
import time
from typing import Dict, Any, List
from PyQt6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QCheckBox, QFileDialog,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import QTimer

from modules.config import ProfileManager
from modules.coupa_scraper import AutomationWorker
from modules.fluxo_orquestrador import AutomaticFlowRunner
from modules.services.export_service import export_to_excel_file
from modules.services.data_bus import DataBus
from modules.logger import UILogger
from modules.styles import set_status, scrollable


class CoupaExtractorWidget(QWidget):
    def __init__(self, parent_framework):
        super().__init__()
        self.parent_fw = parent_framework
        self.profiles = ProfileManager.load_profiles()
        self.worker = None
        self.last_results = []
        self._fluxo_em_andamento = False
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        left_container = QWidget()
        left_panel = QVBoxLayout(left_container)

        profile_group = QGroupBox("Perfis de Automa\u00e7\u00e3o")
        profile_layout = QVBoxLayout()
        select_layout = QHBoxLayout()
        self.combo_profiles = QComboBox()
        self.combo_profiles.addItems(self.profiles.keys())
        self.combo_profiles.currentTextChanged.connect(self.load_selected_profile)

        self.btn_manage_profiles = QPushButton("\U0001f465 Gerenciar Perfis")
        self.btn_manage_profiles.setObjectName("btnWarning")
        self.btn_manage_profiles.clicked.connect(self._open_profile_manager)

        select_layout.addWidget(QLabel("Selecionar Perfil:"))
        select_layout.addWidget(self.combo_profiles, 1)
        select_layout.addWidget(self.btn_manage_profiles)
        profile_layout.addLayout(select_layout)

        self.lbl_config_status = QLabel("Campos ativos: (Nenhum perfil carregado)")
        set_status(self.lbl_config_status, "muted")
        profile_layout.addWidget(self.lbl_config_status)
        profile_group.setLayout(profile_layout)
        left_panel.addWidget(profile_group)

        req_group = QGroupBox("Lista de Requisi\u00e7\u00f5es")
        req_layout = QVBoxLayout()
        self.txt_req_list = QTextEdit()
        self.txt_req_list.setPlaceholderText("Exemplo:\n647865\n649939")
        req_layout.addWidget(self.txt_req_list)
        req_group.setLayout(req_layout)
        left_panel.addWidget(req_group)

        self.btn_open_edge = QPushButton("1. Abrir Edge para Login")
        self.btn_open_edge.setObjectName("btnOpenEdge")
        self.btn_open_edge.clicked.connect(self.open_edge_for_login)
        left_panel.addWidget(self.btn_open_edge)

        self.btn_confirm_login = QPushButton("2. Confirmar Login e Iniciar Extra\u00e7\u00e3o")
        self.btn_confirm_login.setObjectName("btnConfirmLogin")
        self.btn_confirm_login.setEnabled(False)
        self.btn_confirm_login.clicked.connect(self.confirm_login_and_start_extraction)
        left_panel.addWidget(self.btn_confirm_login)

        self.btn_pause = QPushButton("\u23f8\ufe0f Pausar Extra\u00e7\u00e3o")
        self.btn_pause.setObjectName("btnWarning")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause_automation)
        left_panel.addWidget(self.btn_pause)

        # --- Grupo de Fluxo Autom\u00e1tico ---
        fluxo_group = QGroupBox("\U0001f501 Fluxo Autom\u00e1tico (Modo Cadeia)")
        fluxo_layout = QVBoxLayout()
        self.chk_aba2 = QCheckBox("\U0001f4e5 Aba 2 - Baixador de Or\u00e7amentos")
        self.chk_aba3 = QCheckBox("\U0001f4c4 Aba 3 - Gerador de PDF de Pedidos")
        self.chk_aba4 = QCheckBox("\U0001f4dd Aba 4 - Renomeador")
        self.chk_aba5 = QCheckBox("\U0001f5c2\ufe0f Aba 5 - Organizador")
        self.chk_aba6 = QCheckBox("\U0001f4e7 Aba 6 - Disparo de E-mails")
        self.chk_aba2.setChecked(True)
        self.chk_aba3.setChecked(True)
        self.lbl_fluxo_status = QLabel("Status: aguardando extra\u00e7\u00e3o...")
        set_status(self.lbl_fluxo_status, "muted")
        self.lbl_fluxo_status.setWordWrap(True)
        fluxo_layout.addWidget(QLabel("Selecione quais processos seguir\u00e3o automaticamente ap\u00f3s a extra\u00e7\u00e3o:"))
        fluxo_layout.addWidget(self.chk_aba2)
        fluxo_layout.addWidget(self.chk_aba3)
        fluxo_layout.addWidget(self.chk_aba4)
        fluxo_layout.addWidget(self.chk_aba5)
        fluxo_layout.addWidget(self.chk_aba6)
        fluxo_layout.addWidget(self.lbl_fluxo_status)
        fluxo_group.setLayout(fluxo_layout)
        left_panel.addWidget(fluxo_group)

        right_panel = QVBoxLayout()
        log_group = QGroupBox("Logs de Processamento")
        log_layout = QVBoxLayout()
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        log_layout.addWidget(self.txt_logs)
        log_group.setLayout(log_layout)

        # Item 21: Barra de progresso da extração
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        result_group = QGroupBox("Resultados da Extra\u00e7\u00e3o")
        result_layout = QVBoxLayout()
        self.tbl_results = QTableWidget(0, 6)
        self.tbl_results.setHorizontalHeaderLabels(["Req", "Pedido", "Fornecedor", "Criado Por", "Destino", "Status"])
        self.tbl_results.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tbl_results.setSortingEnabled(True)
        result_layout.addWidget(self.tbl_results)
        result_group.setLayout(result_layout)

        self.btn_excel = QPushButton("Exportar Resultados para Excel")
        self.btn_excel.setObjectName("btnSuccess")
        self.btn_excel.setEnabled(False)
        self.btn_excel.clicked.connect(self.export_to_excel)

        right_panel.addWidget(self.progress_bar)
        right_panel.addWidget(log_group, 1)
        right_panel.addWidget(result_group, 2)
        right_panel.addWidget(self.btn_excel)

        layout.addWidget(scrollable(left_container), 2)
        layout.addLayout(right_panel, 3)

        if self.profiles:
            self.load_selected_profile(self.combo_profiles.currentText())

    # --- Métodos públicos ---

    def refresh_profiles(self):
        """Sincroniza os perfis com a aba Gerenciar Perfis."""
        self.profiles = ProfileManager.load_profiles()
        self.combo_profiles.blockSignals(True)
        self.combo_profiles.clear()
        self.combo_profiles.addItems(self.profiles.keys())
        self.combo_profiles.blockSignals(False)
        if self.profiles:
            self.load_selected_profile(self.combo_profiles.currentText())

    def _open_profile_manager(self):
        """Navega para a aba de Gerenciar Perfis."""
        if hasattr(self.parent_fw, 'tab_widget') and hasattr(self.parent_fw, 'tab_manage_profiles'):
            self.parent_fw.tab_widget.setCurrentWidget(self.parent_fw.tab_manage_profiles)

    def log(self, msg: str):
        UILogger.auto(self.txt_logs, msg)
        if hasattr(self, 'parent_fw') and hasattr(self.parent_fw, 'set_status'):
            self.parent_fw.set_status(msg[:80])

    def load_selected_profile(self, name: str):
        if name in self.profiles:
            self.txt_req_list.clear()
            cfg = self.profiles[name].get("config", {"criado_por": True, "solicitado_por": True, "emails": False, "destino": False})
            campos = []
            if cfg.get("criado_por"): campos.append("Criado Por")
            if cfg.get("solicitado_por"): campos.append("Solicitado Por")
            if cfg.get("emails"): campos.append("E-mails")
            if cfg.get("destino"): campos.append("Destino")
            self.lbl_config_status.setText(f"Campos ativos: {', '.join(campos) if campos else 'Nenhum'}")

    def open_edge_for_login(self):
        name = self.combo_profiles.currentText()
        if not name:
            self.txt_logs.append("Erro: Selecione um perfil.")
            return
        req_text = self.txt_req_list.toPlainText()
        requisicoes = [line.strip() for line in req_text.split("\n") if line.strip()]
        if not requisicoes:
            self.txt_logs.append("Erro: Insira requisi\u00e7\u00f5es.")
            return

        abas_selecionadas = []
        if self.chk_aba2.isChecked(): abas_selecionadas.append(2)
        if self.chk_aba3.isChecked(): abas_selecionadas.append(3)
        if self.chk_aba4.isChecked(): abas_selecionadas.append(4)
        if self.chk_aba5.isChecked(): abas_selecionadas.append(5)
        if self.chk_aba6.isChecked(): abas_selecionadas.append(6)

        if abas_selecionadas:
            falhas = self.validar_requisitos_fluxo(abas_selecionadas, True, True)
            if falhas:
                msg = "\u274c Requisitos do fluxo autom\u00e1tico n\u00e3o atendidos!\n\n"
                msg += "Antes de iniciar a extra\u00e7\u00e3o, configure:\n\n"
                msg += "\n".join(falhas)
                msg += "\n\nAp\u00f3s configurar, tente novamente."
                self.log(msg)
                QMessageBox.warning(self, "Pr\u00e9-requisitos n\u00e3o atendidos", msg)
                return

        self.btn_open_edge.setEnabled(False)
        self.btn_confirm_login.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("\u23f8\ufe0f Pausar Extra\u00e7\u00e3o")
        self.btn_excel.setEnabled(False)
        self.btn_manage_profiles.setEnabled(False)
        self.combo_profiles.setEnabled(False)
        self.chk_aba2.setEnabled(False)
        self.chk_aba3.setEnabled(False)
        self.chk_aba4.setEnabled(False)
        self.chk_aba5.setEnabled(False)
        self.chk_aba6.setEnabled(False)
        self.tbl_results.setRowCount(0)

        self.worker = AutomationWorker(requisicoes, self.profiles[name].get("config", {}))
        self.worker.log_signal.connect(self.txt_logs.append)
        self.worker.edge_ready_signal.connect(self.edge_ready_for_login)
        self.worker.finished_signal.connect(self.automation_finished)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.progress_signal.connect(self._on_progress)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.worker.start()

    def _on_progress(self, value: int):
        """Atualiza visibilidade da barra de progresso."""
        self.progress_bar.setVisible(True)
        if value >= 100:
            # Mantém visível por um momento antes de ocultar
            QTimer.singleShot(1500, lambda: self.progress_bar.setVisible(False))

    def edge_ready_for_login(self):
        self.btn_confirm_login.setEnabled(True)
        self.txt_logs.append("\U0001f510 Edge aberto. Conclua o login no Coupa e confirme para iniciar a extra\u00e7\u00e3o.")

    def confirm_login_and_start_extraction(self):
        if not self.worker or not self.worker.isRunning():
            return
        self.worker.confirmar_login()
        self.btn_confirm_login.setEnabled(False)
        self.btn_pause.setEnabled(True)

    def toggle_pause_automation(self):
        if not self.worker or not self.worker.isRunning():
            return
        if self.worker.pause_event.is_set():
            self.worker.retomar()
            self.btn_pause.setText("\u23f8\ufe0f Pausar Extra\u00e7\u00e3o")
            self.txt_logs.append("\u25b6\ufe0f Retomada solicitada.")
        else:
            self.worker.pausar()
            self.btn_pause.setText("\u25b6\ufe0f Retomar Extra\u00e7\u00e3o")
            self.txt_logs.append("\u23f8\ufe0f Pausa solicitada; a extra\u00e7\u00e3o ser\u00e1 pausada ao concluir a requisi\u00e7\u00e3o atual.")

    def automation_finished(self, results: list):
        self.btn_open_edge.setEnabled(True)
        self.btn_confirm_login.setEnabled(False)
        self.btn_pause.setEnabled(False)
        self.btn_pause.setText("\u23f8\ufe0f Pausar Extra\u00e7\u00e3o")
        self.btn_manage_profiles.setEnabled(True)
        self.combo_profiles.setEnabled(True)
        self.chk_aba2.setEnabled(True)
        self.chk_aba3.setEnabled(True)
        self.chk_aba4.setEnabled(True)
        self.chk_aba5.setEnabled(True)
        self.chk_aba6.setEnabled(True)
        self.last_results = results
        DataBus.store_extraction_results(results)
        self.btn_excel.setEnabled(True)

        if not results:
            self.tbl_results.setRowCount(0)
            return

        self.tbl_results.setSortingEnabled(False)
        self.tbl_results.setRowCount(0)
        for item in results:
            row = self.tbl_results.rowCount()
            self.tbl_results.insertRow(row)
            status = "Erro" if "erro" in item else item.get("status", "-")
            self.tbl_results.setItem(row, 0, QTableWidgetItem(str(item.get("requisicao", "-"))))
            self.tbl_results.setItem(row, 1, QTableWidgetItem(str(item.get("pedido", "-"))))
            self.tbl_results.setItem(row, 2, QTableWidgetItem(str(item.get("fornecedor", "-"))))
            self.tbl_results.setItem(row, 3, QTableWidgetItem(str(item.get("criado_por", "-"))))
            self.tbl_results.setItem(row, 4, QTableWidgetItem(str(item.get("destino", item.get("localidade", "-")))))
            self.tbl_results.setItem(row, 5, QTableWidgetItem(status))
        self.tbl_results.setSortingEnabled(True)

        abas_selecionadas = []
        if self.chk_aba2.isChecked(): abas_selecionadas.append(2)
        if self.chk_aba3.isChecked(): abas_selecionadas.append(3)
        if self.chk_aba4.isChecked(): abas_selecionadas.append(4)
        if self.chk_aba5.isChecked(): abas_selecionadas.append(5)
        if self.chk_aba6.isChecked(): abas_selecionadas.append(6)

        if abas_selecionadas:
            self.iniciar_fluxo_automatico(results, abas_selecionadas)
        else:
            set_status(self.lbl_fluxo_status, "muted", "Status: fluxo autom\u00e1tico desabilitado. Nenhuma aba selecionada.")

    def validar_requisitos_fluxo(self, abas: List[int], tem_requisicoes: bool, tem_pedidos: bool) -> List[str]:
        aba_map = {
            2: self.parent_fw.tab_downloader,
            3: self.parent_fw.tab_pdf_generator,
            4: self.parent_fw.tab_renomeador,
            5: self.parent_fw.tab_organizador,
            6: self.parent_fw.tab_email_sender,
        }
        aba_names = {
            2: "Aba 2 - Baixador de Or\u00e7amentos",
            3: "Aba 3 - Gerador de PDF de Pedidos",
            4: "Aba 4 - Renomeador",
            5: "Aba 5 - Organizador",
            6: "Aba 6 - Disparo de E-mails",
        }
        tem_dados = {2: tem_requisicoes, 3: tem_pedidos, 4: True, 5: True, 6: True}
        falhas = []
        for aba_num in abas:
            if aba_num not in aba_map:
                continue
            if not tem_dados.get(aba_num, True):
                falhas.append(f"  \u2022 {aba_names.get(aba_num, f'Aba {aba_num}')}: sem dados da extra\u00e7\u00e3o (pulando)")
                continue
            widget = aba_map[aba_num]
            if hasattr(widget, 'check_prerequisites'):
                ok, msg = widget.check_prerequisites()
                if not ok:
                    falhas.append(f"  \u2022 {aba_names.get(aba_num, f'Aba {aba_num}')}: {msg}")
        return falhas

    def iniciar_fluxo_automatico(self, results: list, abas: List[int]):
        """Inicia o fluxo autom\u00e1tico usando o runner centralizado do fluxo_orquestrador."""
        if self._fluxo_em_andamento:
            self.log("\u26a0\ufe0f Fluxo autom\u00e1tico j\u00e1 em andamento. Ignorando nova solicita\u00e7\u00e3o.")
            return
        self._fluxo_em_andamento = True

        # Usa o AutomaticFlowRunner centralizado (fluxo_orquestrador.py)
        runner = AutomaticFlowRunner(self.parent_fw)
        runner.flow_finished.connect(self._fluxo_runner_finalizado)
        runner.start(results, abas, log_callback=self.log)

    def _fluxo_runner_finalizado(self, sucesso: bool, mensagem: str):
        """Callback quando o fluxo autom\u00e1tico finaliza (via runner centralizado)."""
        self._fluxo_em_andamento = False
        if sucesso:
            self.log("\U0001f3c1 " + mensagem)
            set_status(self.lbl_fluxo_status, "success", "Status: fluxo autom\u00e1tico conclu\u00eddo com sucesso! \u2705")
        else:
            self.log("\u274c " + mensagem)
            set_status(self.lbl_fluxo_status, "error", "Status: fluxo bloqueado - requisitos pendentes \u274c")
            QMessageBox.warning(self, "Pr\u00e9-requisitos n\u00e3o atendidos", mensagem)
        self.parent_fw.tab_widget.setCurrentWidget(self)

    def export_to_excel(self):
        if not self.last_results: return
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Relat\u00f3rio", "Relatorio_Coupa.xlsx", "Excel (*.xlsx)")
        if not file_path: return

        resultado = export_to_excel_file(self.last_results, file_path)
        if resultado and resultado.startswith("Erro"):
            self.log(f"\u274c {resultado}")
        else:
            self.log(f"\u2705 {resultado}")
