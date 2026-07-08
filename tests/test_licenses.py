from scripts.check_licenses import forbidden_packages


def test_flags_banned_packages():
    installed = ["docling", "pymupdf4llm", "semhash", "pyiqa", "pymupdf"]
    assert set(forbidden_packages(installed)) == {"pymupdf4llm", "pyiqa", "pymupdf"}


def test_clean_env_returns_empty():
    assert forbidden_packages(["docling", "semhash", "openpyxl"]) == []
