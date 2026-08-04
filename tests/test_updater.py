from modules.updater import _format_version_label, _is_newer_version


def test_older_release_is_not_considered_update():
    assert not _is_newer_version("1.1.0", "1.1.1")


def test_newer_release_is_considered_update():
    assert _is_newer_version("1.2.0", "1.1.1")


def test_v_prefix_is_supported():
    assert _is_newer_version("v1.1.2", "1.1.1")


def test_display_version_adds_v_prefix_when_missing():
    assert _format_version_label("1.2.0") == "v1.2.0"


def test_display_version_preserves_existing_v_prefix():
    assert _format_version_label("v1.2.0") == "v1.2.0"
