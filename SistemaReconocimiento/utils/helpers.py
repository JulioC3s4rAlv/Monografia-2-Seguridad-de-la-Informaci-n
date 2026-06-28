from datetime import datetime
from typing import Optional

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norm = b / (np.linalg.norm(b) + 1e-10)
    return float(np.dot(a_norm, b_norm))


def normalize_vector(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def timestamp_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def date_now() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def time_now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def minutes_between(t1: str, t2: str) -> float:
    fmt = "%Y-%m-%d %H:%M:%S"
    dt1 = datetime.strptime(t1, fmt)
    dt2 = datetime.strptime(t2, fmt)
    return abs((dt2 - dt1).total_seconds()) / 60.0
