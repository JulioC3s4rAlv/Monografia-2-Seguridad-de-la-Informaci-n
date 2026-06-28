import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from utils.file_utils import ensure_dir, unique_filename
from utils.helpers import date_now, time_now, minutes_between, timestamp_now

logger = logging.getLogger("sistema_reconocimiento.services.log")


class LogService:
    PERSON_TYPES = {
        "active": "Personal activo",
        "inactive": "Personal inactivo",
        "unknown": "Desconocido",
    }

    def __init__(self, database, settings):
        self._db = database
        self._settings = settings

    def register_event(self, code: str = None, name: str = None,
                       person_type: str = None, status: str = None,
                       decision: str = None, confidence: float = None,
                       face_image: np.ndarray = None,
                       force: bool = False) -> Optional[dict]:

        if not force and person_type == self.PERSON_TYPES["active"]:
            if self._is_duplicate(code):
                logger.debug(f"Duplicate log suppressed for {code}")
                return None

        image_path = None
        if face_image is not None and self._settings.get("log", "image_enabled", default=True):
            save_image = False
            if person_type == self.PERSON_TYPES["active"]:
                save_image = True
            elif person_type == self.PERSON_TYPES["inactive"] and force:
                save_image = True
            elif person_type == self.PERSON_TYPES["unknown"] and force:
                save_image = True

            if save_image:
                image_path = self._save_face_image(face_image, code or "unknown")

        log_entry = {
            "date": date_now(),
            "time": time_now(),
            "code": code,
            "name": name,
            "person_type": person_type,
            "status": status,
            "decision": decision,
            "confidence": confidence,
            "image_path": image_path,
        }

        log_id = self._db.add_log(**log_entry)
        log_entry["id"] = log_id
        conf_str = f"{confidence:.3f}" if confidence is not None else "N/A"
        logger.info(f"Log saved: {person_type} | {code or 'N/A'} | "
                    f"{decision or 'auto'} | conf={conf_str}")
        return log_entry

    def _is_duplicate(self, code: str) -> bool:
        if not code:
            return False
        last_log = self._db.get_last_log(code)
        if not last_log:
            return False

        last_datetime = f"{last_log['date']} {last_log['time']}"
        now = timestamp_now()
        minutes = minutes_between(last_datetime, now)
        return minutes < self._settings.min_log_interval_minutes

    def _save_face_image(self, face_image: np.ndarray,
                         identifier: str) -> str:
        images_dir = self._settings.log_images_path
        ensure_dir(images_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{identifier}_{timestamp}.jpg"
        path = images_dir / filename
        cv2.imwrite(str(path), face_image)
        return str(path)

    def get_logs(self, limit: int = 100, offset: int = 0,
                 person_type: str = None,
                 date_from: str = None, date_to: str = None) -> list:
        return self._db.get_logs(
            limit=limit, offset=offset,
            person_type=person_type,
            date_from=date_from, date_to=date_to,
        )

    def count_logs(self, person_type: str = None) -> int:
        return self._db.count_logs(person_type=person_type)
