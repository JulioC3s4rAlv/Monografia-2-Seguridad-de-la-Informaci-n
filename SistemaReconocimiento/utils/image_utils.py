from pathlib import Path
from typing import Tuple, Optional

import cv2
import numpy as np
from PIL import Image


def cv2_to_pil(cv_image: np.ndarray) -> Image.Image:
    rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)


def resize_image(image: np.ndarray, width: int = None,
                 height: int = None) -> np.ndarray:
    h, w = image.shape[:2]
    if width and height:
        return cv2.resize(image, (width, height))
    if width:
        ratio = width / w
        return cv2.resize(image, (width, int(h * ratio)))
    if height:
        ratio = height / h
        return cv2.resize(image, (int(w * ratio), height))
    return image


def save_image(image: np.ndarray, path: Path, quality: int = 95):
    path.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(path), image)
    return success


def crop_face(image: np.ndarray, bbox: np.ndarray,
              margin: float = 0.2) -> Optional[np.ndarray]:
    h, w = image.shape[:2]
    x1, y1, x2, y2 = map(int, bbox[:4])
    margin_x = int((x2 - x1) * margin)
    margin_y = int((y2 - y1) * margin)
    x1 = max(0, x1 - margin_x)
    y1 = max(0, y1 - margin_y)
    x2 = min(w, x2 + margin_x)
    y2 = min(h, y2 + margin_y)
    if x2 <= x1 or y2 <= y1:
        return None
    return image[y1:y2, x1:x2]


def draw_detection(image: np.ndarray, bbox: np.ndarray,
                   label: str = None, confidence: float = None,
                   color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
    x1, y1, x2, y2 = map(int, bbox[:4])
    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
    text_parts = []
    if label:
        text_parts.append(label)
    if confidence is not None:
        text_parts.append(f"{confidence:.2f}")
    if text_parts:
        text = " | ".join(text_parts)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(image, (x1, y1 - th - 8), (x1 + tw + 8, y1), color, -1)
        cv2.putText(image, text, (x1 + 4, y1 - 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    return image


def frame_to_tk(image: np.ndarray, width: int = 640) -> Image.Image:
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    if width:
        ratio = width / pil_img.width
        pil_img = pil_img.resize((width, int(pil_img.height * ratio)),
                                 Image.LANCZOS)
    return pil_img
