import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

import cv2
import numpy as np

from utils.image_utils import crop_face, draw_detection
from utils.helpers import date_now, timestamp_now, minutes_between
from services.log_service import LogService

logger = logging.getLogger("sistema_reconocimiento.services.recognition")


@dataclass
class RecognitionEvent:
    person_type: str  # "active", "inactive", "unknown"
    code: Optional[str] = None
    names: Optional[str] = None
    last_names: Optional[str] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    photo_path: Optional[str] = None
    face_image: Optional[np.ndarray] = None
    bbox: Optional[np.ndarray] = None
    frame: Optional[np.ndarray] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = timestamp_now()

    @property
    def full_name(self) -> str:
        if self.names and self.last_names:
            return f"{self.names} {self.last_names}"
        return self.names or "Desconocido"


class RecognitionService:
    def __init__(self, detector, recognizer, database, log_service, settings,
                 camera=None):
        self._detector = detector
        self._recognizer = recognizer
        self._db = database
        self._log_service = log_service
        self._settings = settings
        self._camera = camera

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_queue = queue.Queue(maxsize=10)
        self._gallery = []
        self._gallery_lock = threading.Lock()
        self._last_decision_time = {}
        self._decision_callbacks = {}

    @property
    def event_queue(self) -> queue.Queue:
        return self._event_queue

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def camera(self):
        return self._camera

    def set_camera(self, camera):
        self._camera = camera

    def reload_gallery(self):
        with self._gallery_lock:
            self._gallery = self._db.get_all_embeddings()
            logger.info(f"Gallery reloaded: {len(self._gallery)} embeddings")

    def start(self) -> bool:
        if self._running:
            return True
        if self._camera is None:
            logger.error("No camera set for recognition")
            return False

        self._camera.start()
        if not self._camera.is_running:
            return False

        self.reload_gallery()
        self._running = True
        self._thread = threading.Thread(
            target=self._recognition_loop,
            daemon=True,
            name="RecognitionThread",
        )
        self._thread.start()
        logger.info("Recognition service started")
        return True

    def stop(self):
        self._running = False
        if self._camera:
            self._camera.stop()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Recognition service stopped")

    def _recognition_loop(self):
        frame_count = 0
        process_every_n = 2

        while self._running:
            frame = self._camera.get_frame(timeout=0.5)
            if frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            if frame_count % process_every_n != 0:
                continue

            try:
                self._process_frame(frame)
            except Exception as e:
                logger.error(f"Recognition error: {e}", exc_info=True)

    def _process_frame(self, frame: np.ndarray):
        display = frame.copy()
        faces = self._detector.detect(frame)

        if not faces:
            try:
                self._event_queue.put_nowait(
                    RecognitionEvent(person_type="none", frame=display))
            except queue.Full:
                pass
            return

        with self._gallery_lock:
            gallery = list(self._gallery)

        for face in faces:
            bbox = face["bbox"]
            embedding = face["embedding"]
            face_crop = crop_face(frame, bbox)

            match = self._recognizer.match(embedding, gallery)

            if match:
                user = self._db.get_user(user_id=match["user_id"])
                event = RecognitionEvent(
                    person_type="active" if user and user["status"] == "Activo"
                    else "inactive",
                    code=match["code"],
                    names=match["names"],
                    last_names=match["last_names"],
                    status=match["status"],
                    confidence=match["confidence"],
                    photo_path=match["photo_path"],
                    face_image=face_crop,
                    bbox=bbox,
                    frame=display,
                )
                color = (0, 255, 0) if event.person_type == "active" else (0, 255, 255)
                draw_detection(display, bbox, event.code,
                               event.confidence, color)
            else:
                event = RecognitionEvent(
                    person_type="unknown",
                    face_image=face_crop,
                    bbox=bbox,
                    frame=display,
                )
                draw_detection(display, bbox, "Desconocido", None, (0, 0, 255))

            try:
                self._event_queue.put_nowait(event)
            except queue.Full:
                pass

    def handle_decision(self, event: RecognitionEvent,
                        decision: str) -> Optional[dict]:
        person_type_map = {
            "active": LogService.PERSON_TYPES["active"],
            "inactive": LogService.PERSON_TYPES["inactive"],
            "unknown": LogService.PERSON_TYPES["unknown"],
        }
        log_entry = self._log_service.register_event(
            code=event.code,
            name=event.full_name if event.code else None,
            person_type=person_type_map.get(
                event.person_type, event.person_type),
            status=event.status,
            decision=decision,
            confidence=event.confidence,
            face_image=event.face_image,
            force=(event.person_type != "active"),
        )
        return log_entry

    def _get_current_decision(self, code: str, cooldown_seconds: float = 5.0) -> bool:
        now = time.time()
        last_time = self._last_decision_time.get(code, 0)
        if now - last_time < cooldown_seconds:
            return True
        return False

    def set_decision(self, code: str):
        self._last_decision_time[code] = time.time()
