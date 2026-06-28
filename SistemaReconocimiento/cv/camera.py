import logging
import threading
import time
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger("sistema_reconocimiento.cv.camera")


class Camera:
    def __init__(self, device_id: int = 0,
                 frame_width: int = 640,
                 frame_height: int = 480):
        self._device_id = device_id
        self._frame_width = frame_width
        self._frame_height = frame_height
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_available = threading.Event()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> bool:
        if self._running:
            return True
        try:
            self._cap = cv2.VideoCapture(self._device_id)
            if not self._cap.isOpened():
                logger.error(f"Cannot open camera device {self._device_id}")
                return False
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._frame_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._frame_height)
            self._running = True
            self._thread = threading.Thread(target=self._capture_loop,
                                            daemon=True, name="CameraThread")
            self._thread.start()
            logger.info(f"Camera started (device={self._device_id})")
            return True
        except Exception as e:
            logger.error(f"Camera start error: {e}")
            self._cleanup()
            return False

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._cleanup()
        logger.info("Camera stopped")

    def _cleanup(self):
        if self._cap:
            self._cap.release()
            self._cap = None
        self._latest_frame = None
        self._frame_available.clear()

    def _capture_loop(self):
        while self._running and self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret and frame is not None:
                with self._lock:
                    self._latest_frame = frame
                    self._frame_available.set()
            else:
                time.sleep(0.01)

    def get_frame(self, timeout: float = None) -> Optional[numpy.ndarray]:
        if timeout:
            self._frame_available.wait(timeout=timeout)
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
            return None

    def read(self) -> Optional[numpy.ndarray]:
        if self._cap and self._cap.isOpened():
            ret, frame = self._cap.read()
            if ret:
                return frame
        return None
