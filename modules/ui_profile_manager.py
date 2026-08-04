import os
from typing import Any, Dict
import logging

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QGroupBox, QFormLayout, QMessageBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import pyqtSignal

from modules.config import ProfileManager
from modules.styles import set_status, scrollable

logger = logging.getLogger(__name__)


class ProfileManagerWidget(QWidget):
    profiles_changed = pyqtSignal()
    def __init__(self, parent_framework=None):
        super().__init__()
        self.parent_fw = parent_framework
        self.profiles = {}
        self.current_profile = None
        self.init_ui()
        self.load_profiles()

    def init_ui(self):
        layout = QHBoxLayout(self)

        left_container = QWidget()
        left_panel = QVBoxLayout(left_container)
        profile_group = QGroupBox("Perfis de Automação")
        profile_layout = QVBoxLayout()

        combo_layout = QHBoxLayout()
        self.combo_profiles = QComboBox()
        self.combo_profiles.currentTextChanged.connect(self.load_selected_profile)
        self.btn_new_profile = QPushButton("Novo Perfil")
        self.btn_new_profile.clicked.connect(self.start_new_profile)
        combo_layout.addWidget(QLabel("Perfil:"))
        combo_layout.addWidget(self.combo_profiles, 1)
        combo_layout.addWidget(self.btn_new_profile)

        action_layout = QHBoxLayout()
        self.btn_save_profile = QPushButton("Salvar Perfil")
        self.btn_save_profile.setObjectName("btnSuccess")
        self.btn_save_profile.clicked.connect(self.save_profile)
        self.btn_delete_profile = QPushButton("Excluir Perfil")
        self.btn_delete_profile.setObjectName("btnDanger")
        self.btn_delete_profile.clicked.connect(self.delete_profile)
        self.btn_reload_profiles = QPushButton("Recarregar")
        self.btn_reload_profiles.setObjectName("btnWarning")
        self.btn_reload_profiles.clicked.connect(self.load_profiles)
        action_layout.addWidget(self.btn_save_profile)
        action_layout.addWidget(self.btn_delete_profile)
        action_layout.addWidget(self.btn_reload_profiles)

        profile_layout.addLayout(combo_layout)
        profile_layout.addLayout(action_layout)
        profile_group.setLayout(profile_layout)
        left_panel.addWidget(profile_group)

        config_group = QGroupBox("Configuração do Perfil")
        config_layout = QFormLayout()
        self.txt_profile_name = QLineEdit()
        self.txt_profile_name.setPlaceholderText("Digite o nome do perfil")
        config_layout.addRow(QLabel("Nome do perfil:"), self.txt_profile_name)

        self.chk_criado_por = QCheckBox("Criado Por")
        self.chk_solicitado_por = QCheckBox("Solicitado Por")
        self.chk_emails = QCheckBox("E-mails")
        self.chk_destino = QCheckBox("Destino")
        self.txt_comprador_email = QLineEdit()
        self.txt_comprador_email.setPlaceholderText("comprador1@empresa.com.br; comprador2@empresa.com.br")

        config_layout.addRow(self.chk_criado_por)
        config_layout.addRow(self.chk_solicitado_por)
        config_layout.addRow(self.chk_emails)
        config_layout.addRow(self.chk_destino)
        config_layout.addRow(QLabel("E-mails do Comprador (separados por ; ou ,):"), self.txt_comprador_email)
        config_group.setLayout(config_layout)
        left_panel.addWidget(config_group)

        template_group = QGroupBox("Modelo de E-mail (HTML)")
        template_layout = QVBoxLayout()
        self.txt_template = QTextEdit()
        self.txt_template.setPlaceholderText("Cole seu HTML aqui. Use {pedido}, {req}, {fornecedor} como variáveis.")
        template_layout.addWidget(self.txt_template)
        template_group.setLayout(template_layout)
        left_panel.addWidget(template_group, 1)

        self.lbl_status = QLabel("Nenhum perfil carregado.")
        set_status(self.lbl_status, "muted")
        left_panel.addWidget(self.lbl_status)

        layout.addWidget(scrollable(left_container), 3)

        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Instruções"))
        right_panel.addWidget(QLabel("1. Selecione um perfil existente ou crie um novo."))
        right_panel.addWidget(QLabel("2. Ajuste os campos desejados e pressione Salvar."))
        right_panel.addWidget(QLabel("3. Use o perfil na Aba de Extração ou de Envio de E-mail."))
        right_panel.addStretch(1)
        layout.addLayout(right_panel, 2)

    def load_profiles(self):
        self.profiles = ProfileManager.load_profiles() or {}
        self.current_profile = None

        self.combo_profiles.blockSignals(True)
        self.combo_profiles.clear()
        self.combo_profiles.addItems(self.profiles.keys())
        self.combo_profiles.blockSignals(False)

        if self.profiles:
            self.combo_profiles.setCurrentIndex(0)
            self.load_selected_profile(self.combo_profiles.currentText())
        else:
            self.clear_form()
            self.update_status("Nenhum perfil cadastrado. Cadastre um para começar.")

    def load_selected_profile(self, name: str):
        if not name or name not in self.profiles:
            self.clear_form()
            return

        self.current_profile = name
        profile = self.profiles[name].get("config", {})
        self.txt_profile_name.setText(name)
        self.txt_profile_name.setEnabled(False)
        self.chk_criado_por.setChecked(profile.get("criado_por", True))
        self.chk_solicitado_por.setChecked(profile.get("solicitado_por", True))
        self.chk_emails.setChecked(profile.get("emails", False))
        # amazonq-ignore-next-line
        self.chk_destino.setChecked(profile.get("destino", False))
        self.txt_comprador_email.setText(profile.get("comprador_email", ""))
        self.txt_template.setPlainText(profile.get("template", ""))
        self.update_status(f"Perfil '{name}' carregado. Revise os dados antes de salvar.")

    def clear_form(self):
        self.current_profile = None
        self.txt_profile_name.setText("")
        self.txt_profile_name.setEnabled(True)
        self.chk_criado_por.setChecked(True)
        self.chk_solicitado_por.setChecked(True)
        self.chk_emails.setChecked(False)
        self.chk_destino.setChecked(False)
        self.txt_comprador_email.setText("")
        self.txt_template.setPlainText("")

    def start_new_profile(self):
        self.combo_profiles.setCurrentText("")
        self.clear_form()
        self.txt_profile_name.setEnabled(True)
        self.update_status("Criando novo perfil.")

    def save_profile(self):
        name = self.txt_profile_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Digite um nome válido para o perfil.")
            return

        config = {
            "criado_por": self.chk_criado_por.isChecked(),
            "solicitado_por": self.chk_solicitado_por.isChecked(),
            "emails": self.chk_emails.isChecked(),
            "destino": self.chk_destino.isChecked(),
            "comprador_email": self.txt_comprador_email.text().strip(),
            "template": self.txt_template.toPlainText().strip(),
        }

        if self.txt_comprador_email.text().strip() and ";" not in self.txt_comprador_email.text().strip() and "," not in self.txt_comprador_email.text().strip():
            self.update_status("Use ; ou , para separar múltiplos e-mails do comprador.")
            return

        if self.current_profile and self.current_profile != name and name in self.profiles:
            QMessageBox.warning(self, "Aviso", "Já existe um perfil com esse nome.")
            return

        if self.current_profile and self.current_profile != name:
            del self.profiles[self.current_profile]

        self.profiles[name] = {"config": config}
        try:
            ProfileManager.save_profiles(self.profiles)
        except Exception as exc:
            logger.exception("Falha ao salvar perfil %s", name)
            QMessageBox.critical(self, "Erro", f"Não foi possível salvar o perfil: {exc}")
            return
        self.load_profiles()
        self.combo_profiles.setCurrentText(name)
        self.update_status(f"Perfil '{name}' salvo com sucesso.")
        self.profiles_changed.emit()

    def delete_profile(self):
        name = self.combo_profiles.currentText()
        if not name:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil para excluir.")
            return

        resposta = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente excluir o perfil '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return

        if name in self.profiles:
            del self.profiles[name]
            try:
                ProfileManager.save_profiles(self.profiles)
            except Exception as exc:
                logger.exception("Falha ao excluir perfil %s", name)
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir o perfil: {exc}")
                return
            self.load_profiles()
            self.update_status(f"Perfil '{name}' excluído.")
            self.profiles_changed.emit()

    def update_status(self, message: str):
        set_status(self.lbl_status, "accent", message)
