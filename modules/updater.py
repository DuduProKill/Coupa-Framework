import subprocess
import tempfile
import requests
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QApplication
from PyQt6.QtCore import Qt

GITHUB_REPO = "DuduProKill/Coupa-Framework"
CURRENT_VERSION = "1.1.1"


class _CheckThread(QThread):
    update_found = pyqtSignal(str, str)  # (latest_tag, asset_url)

    def run(self):
        try:
            r = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                timeout=5,
                headers={"Accept": "application/vnd.github+json"},
            )
            if r.status_code != 200:
                return
            data = r.json()
            tag = data.get("tag_name", "").lstrip("v")
            if not tag or tag == CURRENT_VERSION:
                return
            asset_url = next(
                (a["browser_download_url"] for a in data.get("assets", []) if a["name"].endswith(".exe")),
                None,
            )
            if asset_url:
                self.update_found.emit(tag, asset_url)
        except Exception:
            pass


class _DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
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


class UpdateManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent_widget = parent
        self._check_thread = _CheckThread()
        self._check_thread.update_found.connect(self._on_update_found)
        self._download_thread = None

    def start(self):
        self._check_thread.start()

    def _on_update_found(self, latest_tag: str, asset_url: str):
        msg = QMessageBox(self._parent_widget)
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

        self._progress_dlg = QProgressDialog("Baixando atualização...", None, 0, 100, self._parent_widget)
        self._progress_dlg.setWindowTitle("Atualizando")
        self._progress_dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        self._progress_dlg.setCancelButton(None)
        self._progress_dlg.show()

        self._download_thread = _DownloadThread(asset_url)
        self._download_thread.progress.connect(self._progress_dlg.setValue)
        self._download_thread.finished.connect(self._on_downloaded)
        self._download_thread.error.connect(self._on_error)
        self._download_thread.start()

    def _on_downloaded(self, path: str):
        self._progress_dlg.close()
        subprocess.Popen(
            [path, "/SILENT", "/CLOSEAPPLICATIONS"],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        QApplication.quit()

    def _on_error(self, err: str):
        self._progress_dlg.close()
        QMessageBox.critical(self._parent_widget, "Erro na atualização", f"Falha ao baixar: {err}")
