import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger("sistema_reconocimiento.cv.preprocessing")


class Preprocessor:
    @staticmethod
    def normalize_illumination(image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.shape[2] == 3 else image
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        equalized = clahe.apply(gray)
        if image.shape[2] == 3:
            return cv2.cvtColor(equalized, cv2.COLOR_GRAY2BGR)
        return equalized

    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        return cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

    @staticmethod
    def enhance(image: np.ndarray) -> np.ndarray:
        result = image.copy()
        result = Preprocessor.denoise(result)
        result = Preprocessor.normalize_illumination(result)
        return result

    @staticmethod
    def extract_frames_from_video(video_path: str, max_frames: int = 100,
                                  frame_interval: int = 5) -> list:
        frames = []
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {video_path}")
            return frames

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return frames

        step = max(1, frame_interval)
        count = 0
        while len(frames) < max_frames:
            ret = cap.grab()
            if not ret:
                break
            if count % step == 0:
                ret, frame = cap.retrieve()
                if ret and frame is not None:
                    frames.append(frame)
            count += 1

        cap.release()
        logger.info(f"Extracted {len(frames)} frames from {video_path}")
        return frames

    @staticmethod
    def crop_and_align(image: np.ndarray, landmarks: np.ndarray,
                       size: tuple = (160, 160)) -> Optional[np.ndarray]:
        if landmarks is None or len(landmarks) < 5:
            return cv2.resize(image, size)

        left_eye = landmarks[0]
        right_eye = landmarks[1]

        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        angle = np.degrees(np.arctan2(dy, dx))

        center = tuple((left_eye + right_eye) / 2.0)
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        h, w = image.shape[:2]
        aligned = cv2.warpAffine(image, rot_matrix, (w, h),
                                 flags=cv2.INTER_CUBIC)
        return cv2.resize(aligned, size)
