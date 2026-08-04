from modules.updater import _is_newer_version


def test_older_release_is_not_considered_update():
    assert not _is_newer_version("1.1.0", "1.1.1")


def test_newer_release_is_considered_update():
    assert _is_newer_version("1.2.0", "1.1.1")


def test_v_prefix_is_supported():
    assert _is_newer_version("v1.1.2", "1.1.1")
