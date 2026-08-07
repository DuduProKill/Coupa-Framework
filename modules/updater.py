import logging
import subprocess
import tempfile
from typing import Optional

import requests
from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

logger = logging.getLogger(__name__)

GITHUB_REPO = "DuduProKill/Coupa-Framework"
CURRENT_VERSION = "1.1.3"


def _normalize_version(value: str) -> Optional[tuple[int, int, int]]:
    text = (value or "").strip().lstrip("vV")
    if not text:
        return None
    parts = text.split(".")
    if len(parts) != 3:
        return None
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def _format_version_label(version: str) -> str:
    normalized = (version or "").strip()
    if not normalized:
        return ""
    return normalized if normalized.startswith("v") else f"v{normalized}"


def _is_newer_version(latest_tag: str, current_version: str) -> bool:
    latest = _normalize_version(latest_tag)
    current = _normalize_version(current_version)
    if latest is None or current is None:
        return False
    return latest > current


class _CheckThread(QThread):
    update_found = pyqtSignal(str, str)  # (latest_tag, asset_url)

    def run(self):
        try:
            response = requests.get(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                timeout=5,
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            data = response.json()
            tag = data.get("tag_name", "")
            if not tag or not _is_newer_version(tag, CURRENT_VERSION):
                return
            asset_url = next(
                (
                    asset.get("browser_download_url")
                    for asset in data.get("assets", [])
                    if isinstance(asset, dict) and asset.get("name", "").endswith(".exe")
                ),
                None,
            )
            if asset_url:
                self.update_found.emit(tag, asset_url)
        except requests.RequestException as exc:
            logger.exception("Falha ao verificar atualização no GitHub: %s", exc)
        except ValueError as exc:
            logger.exception("Resposta inválida da API do GitHub: %s", exc)


class _DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            response = requests.get(self._url, stream=True, timeout=60)
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0) or 0)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".exe")
            try:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    tmp.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        self.progress.emit(int(downloaded * 100 / total))
                tmp.flush()
            finally:
                tmp.close()
            self.finished.emit(tmp.name)
        except requests.RequestException as exc:
            logger.exception("Falha ao baixar atualização: %s", exc)
            self.error.emit(str(exc))
        except OSError as exc:
            logger.exception("Falha ao gravar arquivo temporário da atualização: %s", exc)
            self.error.emit(str(exc))


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
        latest_label = _format_version_label(latest_tag)
        current_label = _format_version_label(CURRENT_VERSION)
        msg.setText(
            f"Nova versão disponível: <b>{latest_label}</b><br>"
            f"Versão atual: {current_label}<br><br>"
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
            [path, "/SILENT", "/CLOSEAPPLICATIONS", "/CURRENTUSER"],
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        QApplication.quit()

    def _on_error(self, err: str):
        self._progress_dlg.close()
        QMessageBox.critical(self._parent_widget, "Erro na atualização", f"Falha ao baixar: {err}")
