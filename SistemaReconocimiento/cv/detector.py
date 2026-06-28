import logging
from typing import List, Optional

import cv2
import numpy as np

logger = logging.getLogger("sistema_reconocimiento.cv.detector")


class FaceDetector:
    def __init__(self, insightface_app):
        self._app = insightface_app

    def detect(self, image: np.ndarray) -> List[dict]:
        if image is None or image.size == 0:
            return []
        try:
            faces = self._app.get(image)
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []

        results = []
        for face in faces:
            results.append({
                "bbox": face.bbox.astype(np.int32),
                "landmarks": face.kps.astype(np.int32) if face.kps is not None else None,
                "det_score": float(face.det_score),
                "embedding": face.embedding.astype(np.float32),
            })
        return results

    def detect_best(self, image: np.ndarray) -> Optional[dict]:
        faces = self.detect(image)
        if faces:
            return faces[0]
        return None
