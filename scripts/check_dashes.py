"""Scan project text and generated report XML for forbidden dash characters."""

from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", ".venv", "venv", "node_modules", "logs", "__pycache__", "staticfiles"}
FORBIDDEN = {chr(0x2013), chr(0x2014)}


def scan():
    """Return paths and line numbers, including text in document containers."""
    hits = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or SKIP.intersection(path.relative_to(ROOT).parts):
            continue
        if path.name == "Project_Report_Format.docx":
            continue
        if path.suffix == ".docx":
            with ZipFile(path) as document:
                texts = [(name, document.read(name).decode("utf-8"))
                         for name in document.namelist() if name.endswith(".xml")]
        else:
            try:
                texts = [("", path.read_text(encoding="utf-8"))]
            except (UnicodeDecodeError, OSError):
                continue
        for member, text in texts:
            for number, line in enumerate(text.splitlines(), 1):
                if FORBIDDEN.intersection(line):
                    hits.append(f"{path.relative_to(ROOT)}:{member}:{number}")
    return hits


if __name__ == "__main__":
    problems = scan()
    print("\n".join(problems) if problems else "Zero forbidden dash hits.")
    raise SystemExit(bool(problems))
