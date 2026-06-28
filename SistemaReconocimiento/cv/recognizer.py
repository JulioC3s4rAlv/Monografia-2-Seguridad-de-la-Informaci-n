import logging
from typing import List, Optional, Tuple

import numpy as np

from utils.helpers import cosine_similarity

logger = logging.getLogger("sistema_reconocimiento.cv.recognizer")


class FaceRecognizer:
    def __init__(self, confidence_threshold: float = 0.4):
        self._threshold = confidence_threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float):
        self._threshold = value

    def match(self, query_embedding: np.ndarray,
              gallery: List[dict]) -> Optional[dict]:
        if not gallery or query_embedding is None:
            return None

        best_score = -1.0
        best_match = None

        for entry in gallery:
            stored_emb = entry.get("embedding")
            if stored_emb is None:
                continue
            score = cosine_similarity(query_embedding, stored_emb)
            if score > best_score:
                best_score = score
                best_match = entry

        if best_match and best_score >= self._threshold:
            return {
                "user_id": best_match["id"],
                "code": best_match["code"],
                "names": best_match["names"],
                "last_names": best_match["last_names"],
                "status": best_match.get("status", "Activo"),
                "photo_path": best_match.get("photo_path"),
                "confidence": best_score,
                "embedding": best_match["embedding"],
            }
        return None

    def compare(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        return cosine_similarity(emb1, emb2)
