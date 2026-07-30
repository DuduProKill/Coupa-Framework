import shutil
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication, QTableWidgetItem

from modules.ui_renomeador import RenomeadorWidget


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance() or QApplication([])
    return app


def test_renomear_usa_coluna_de_status_correta(tmp_path, qt_app, monkeypatch):
    widget = RenomeadorWidget(parent_framework=None)
    widget.pasta = str(tmp_path)

    arquivo = tmp_path / "arquivo.pdf"
    arquivo.write_bytes(b"pdf")

    # Tabela agora tem 6 colunas (0: Arquivo, 1: ID Coupa, 2: Fornecedor, 3: Unid. Entrega, 4: Novo Nome, 5: Status)
    widget.table.setRowCount(1)
    widget.table.setItem(0, 0, QTableWidgetItem("arquivo.pdf"))
    widget.table.setItem(0, 4, QTableWidgetItem("novo.pdf"))
    widget.table.setItem(0, 5, QTableWidgetItem("\u2705 Pronto"))

    monkeypatch.setattr(widget, "salvar_historico", lambda *args, **kwargs: None)

    widget.renomear()

    assert widget.table.item(0, 5).text() == "\u2705 Renomeado"
    assert (tmp_path / "novo.pdf").exists()
