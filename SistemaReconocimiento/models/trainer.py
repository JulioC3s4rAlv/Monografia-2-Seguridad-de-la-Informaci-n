import logging
import shutil
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from cv.preprocessing import Preprocessor

logger = logging.getLogger("sistema_reconocimiento.models.trainer")


class Trainer:
    def __init__(self, detector, face_recognizer, database, settings):
        self._detector = detector
        self._recognizer = face_recognizer
        self._db = database
        self._settings = settings

    def train_user_from_video(self, user_id: int, video_path: str) -> Optional[np.ndarray]:
        logger.info(f"Training user {user_id} from video: {video_path}")
        frames = Preprocessor.extract_frames_from_video(
            video_path,
            max_frames=self._settings.max_frames_per_video,
            frame_interval=self._settings.training_frame_interval,
        )

        if not frames:
            logger.warning(f"No frames extracted from video: {video_path}")
            return None

        embeddings = []
        for frame in frames:
            face = self._detector.detect_best(frame)
            if face and face["det_score"] >= self._settings.face_detection_confidence:
                embeddings.append(face["embedding"])

        if not embeddings:
            logger.warning(f"No faces detected in video for user {user_id}")
            return None

        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / (np.linalg.norm(avg_embedding) + 1e-10)

        self._db.update_embedding(user_id, avg_embedding)
        logger.info(f"User {user_id} trained successfully "
                    f"(faces used: {len(embeddings)}, "
                    f"frames processed: {len(frames)})")
        return avg_embedding

    def train_new_users(self, progress_callback=None) -> dict:
        untrained = self._db.get_all_users(only_untrained=True)
        total = len(untrained)
        results = {"trained": 0, "failed": 0, "skipped": 0, "details": []}

        if total == 0:
            logger.info("No untrained users found")
            return results

        logger.info(f"Starting training for {total} users")

        for idx, user in enumerate(untrained):
            if progress_callback:
                progress_callback(idx + 1, total, user["names"])

            try:
                video_path = self._find_video(user["code"])
                if not video_path:
                    logger.warning(f"No video found for user {user['code']}")
                    results["skipped"] += 1
                    results["details"].append({
                        "code": user["code"],
                        "status": "skipped",
                        "reason": "No video found",
                    })
                    continue

                embedding = self.train_user_from_video(user["id"], str(video_path))
                if embedding is not None:
                    self._move_video_to_trained(video_path, user["code"])
                    results["trained"] += 1
                    results["details"].append({
                        "code": user["code"],
                        "status": "trained",
                    })
                else:
                    results["failed"] += 1
                    results["details"].append({
                        "code": user["code"],
                        "status": "failed",
                        "reason": "No face detected",
                    })

            except Exception as e:
                logger.error(f"Error training user {user['code']}: {e}")
                results["failed"] += 1
                results["details"].append({
                    "code": user["code"],
                    "status": "error",
                    "reason": str(e),
                })

        logger.info(f"Training complete: {results['trained']} trained, "
                    f"{results['failed']} failed, {results['skipped']} skipped")
        return results

    def _find_video(self, code: str) -> Optional[Path]:
        videos_dir = self._settings.new_videos_path
        if not videos_dir.exists():
            return None
        for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
            path = videos_dir / f"{code}{ext}"
            if path.exists():
                return path
        for ext in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
            for f in videos_dir.iterdir():
                if f.suffix.lower() == ext and f.stem == code:
                    return f
        return None

    def _move_video_to_trained(self, video_path: Path, code: str):
        dst_dir = self._settings.trained_videos_path
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / f"{code}{video_path.suffix}"
        shutil.move(str(video_path), str(dst))
        logger.debug(f"Moved video {video_path.name} to trained_videos")
