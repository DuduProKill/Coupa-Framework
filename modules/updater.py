import webbrowser
import requests
from PyQt6.QtWidgets import QMessageBox

GITHUB_REPO = "DuduProKill/Coupa-Framework"
CURRENT_VERSION = "1.1.0"


def _fetch_latest() -> tuple[str, str] | None:
    """Retorna (tag, url_download) da última release, ou None se falhar."""
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
        url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest")
        return tag, url
    except Exception:
        return None


def check_for_updates(parent=None) -> None:
    """Verifica atualizações e exibe popup se houver versão nova."""
    result = _fetch_latest()
    if result is None:
        return

    latest_tag, release_url = result
    if latest_tag and latest_tag != CURRENT_VERSION:
        msg = QMessageBox(parent)
        msg.setWindowTitle("Atualização disponível")
        msg.setText(
            f"Nova versão disponível: <b>v{latest_tag}</b><br>"
            f"Versão atual: v{CURRENT_VERSION}<br><br>"
            "Clique em <b>Baixar</b> para abrir a página de download."
        )
        msg.setIcon(QMessageBox.Icon.Information)
        btn_baixar = msg.addButton("Baixar", QMessageBox.ButtonRole.AcceptRole)
        msg.addButton("Agora não", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == btn_baixar:
            webbrowser.open(release_url)
