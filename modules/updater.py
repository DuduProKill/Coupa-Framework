import os
import sys
import subprocess
import tempfile
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import Qt

GITHUB_REPO = "DuduProKill/Coupa-Framework"
CURRENT_VERSION = "1.1.0"


def _fetch_latest() -> tuple[str, str] | None:
    """Retorna (tag, url_asset_instalador) da última release, ou None se falhar."""
    try:
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            timeout=5,
            headers={"Accept": "application/vnd.github+json"},
        )
        if r.status_code != 200:
            return None
        data = r.json()
        tag = data.get("tag_name", "").lstrip("v")
        # Procura o asset .exe (instalador)
        asset_url = None
        for asset in data.get("assets", []):
            if asset["name"].endswith(".exe"):
                asset_url = asset["browser_download_url"]
                break
        if not asset_url:
            return None
        return tag, asset_url
    except Exception:
        return None


class _DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)   # caminho do arquivo baixado
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            r = requests.get(self._url, stream=True, timeout=60)
            total = int(r.headers.get("content-length", 0))
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
            downloaded = 0
            for chunk in r.iter_content(chunk_size=8192):
                tmp.write(chunk)
                downloaded += len(chunk)
                if total:
                    self.progress.emit(int(downloaded * 100 / total))
            tmp.close()
            self.finished.emit(tmp.name)
        except Exception as e:
            self.error.emit(str(e))


def check_for_updates(parent=None) -> None:
    """Verifica, baixa e instala atualização automaticamente."""
    result = _fetch_latest()
    if result is None:
        return

    latest_tag, asset_url = result
    if not latest_tag or latest_tag == CURRENT_VERSION:
        return

    # Pergunta se quer atualizar agora
    msg = QMessageBox(parent)
    msg.setWindowTitle("Atualização disponível")
    msg.setText(
        f"Nova versão disponível: <b>v{latest_tag}</b><br>"
        f"Versão atual: v{CURRENT_VERSION}<br><br>"
        "Deseja atualizar agora? O aplicativo será fechado automaticamente."
    )
    msg.setIcon(QMessageBox.Icon.Information)
    btn_sim = msg.addButton("Atualizar agora", QMessageBox.ButtonRole.AcceptRole)
    msg.addButton("Agora não", QMessageBox.ButtonRole.RejectRole)
    msg.exec()

    if msg.clickedButton() != btn_sim:
        return

    # Barra de progresso do download
    progress_dlg = QProgressDialog("Baixando atualização...", None, 0, 100, parent)
    progress_dlg.setWindowTitle("Atualizando")
    progress_dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress_dlg.setCancelButton(None)
    progress_dlg.show()
    QApplication.processEvents()

    thread = _DownloadThread(asset_url)
    thread.progress.connect(progress_dlg.setValue)

    installer_path: list[str] = []

    def on_finished(path: str):
        installer_path.append(path)
        progress_dlg.close()

    def on_error(err: str):
        progress_dlg.close()
        QMessageBox.critical(parent, "Erro na atualização", f"Falha ao baixar: {err}")

    thread.finished.connect(on_finished)
    thread.error.connect(on_error)
    thread.start()

    while thread.isRunning():
        QApplication.processEvents()

    if not installer_path:
        return

    # Executa o instalador e fecha o app
    subprocess.Popen(
        [installer_path[0], "/SILENT", "/CLOSEAPPLICATIONS"],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    QApplication.quit()
