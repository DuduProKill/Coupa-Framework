import sys

from modules.module_installer import ModuleInstallWorker


def test_find_installer_prefers_local_file_in_app_dir(tmp_path, monkeypatch):
    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir()
    monkeypatch.setattr(sys, "executable", str(fake_app_dir / "CoupaFramework.exe"))

    local_installer = fake_app_dir / "CoupaFramework_Setup_v1.1.2.exe"
    local_installer.write_bytes(b"fake installer")

    worker = ModuleInstallWorker("extrator")

    assert worker._find_installer() == str(local_installer)


def test_find_installer_checks_installer_output_folder(tmp_path, monkeypatch):
    fake_app_dir = tmp_path / "app"
    fake_app_dir.mkdir()
    monkeypatch.setattr(sys, "executable", str(fake_app_dir / "CoupaFramework.exe"))

    installer_output = tmp_path / "installer_output"
    installer_output.mkdir()
    local_installer = installer_output / "CoupaFramework_Setup_v1.1.2.exe"
    local_installer.write_bytes(b"fake installer")

    worker = ModuleInstallWorker("email")

    assert worker._find_installer() == str(local_installer)
