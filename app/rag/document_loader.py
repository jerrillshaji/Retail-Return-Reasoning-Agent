"""Read plain-text and Markdown knowledge files."""

from pathlib import Path


def load_text_file(path: Path) -> str:
	if path.suffix.lower() not in {".txt", ".md"}:
		raise ValueError("Only .txt and .md files are supported")
	return path.read_text(encoding="utf-8")
