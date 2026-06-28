import logging
import sys
from pathlib import Path


_loggers = {}


def setup_logger(name: str = "sistema_reconocimiento",
                 log_file: str = None,
                 level: int = logging.INFO,
                 console: bool = True) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    _loggers[name] = logger
    return logger


def get_logger(name: str = "sistema_reconocimiento") -> logging.Logger:
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)
