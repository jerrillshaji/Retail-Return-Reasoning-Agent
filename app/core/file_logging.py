"""Write logs to files  ->  app/core/file_logging.py

logs/app.log   everything the application logs (INFO and above), including server errors
logs/chat.log  only the chat: who asked what, which tools ran, how long it took, errors
Files are limited to about 1 MB each; the 3 previous versions are kept (app.log.1, ...).
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"      # <project root>/logs
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def _attach(logger_name: str, filename: str) -> None:
	logger = logging.getLogger(logger_name)
	path = str(LOG_DIR / filename)
	if any(getattr(handler, "baseFilename", None) == path for handler in logger.handlers):
		return                                                         # already set up
	handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
	handler.setLevel(logging.INFO)
	handler.setFormatter(logging.Formatter(FORMAT))
	logger.addHandler(handler)


def setup_file_logging() -> None:
	LOG_DIR.mkdir(exist_ok=True)
	logging.getLogger("app").setLevel(logging.INFO)          # our own code logs INFO and above
	_attach("", "app.log")                                    # root: our code and library warnings
	_attach("uvicorn.error", "app.log")                       # server errors and tracebacks
	_attach("uvicorn.access", "app.log")                      # one line per request with its status
	_attach("app.chat", "chat.log")                           # chat activity only


ALLOWED_LOGS = {"chat": "chat.log", "app": "app.log"}


def read_log_tail(source: str = "chat", max_lines: int = 100) -> list[str]:
	"""The last lines of a log file. Only the two known log files can be read."""
	filename = ALLOWED_LOGS.get(source)
	path = LOG_DIR / filename if filename else None
	if path is None or not path.exists():
		return []
	with path.open(encoding="utf-8", errors="replace") as handle:
		return [line.rstrip("\n") for line in handle.readlines()[-max_lines:]]
