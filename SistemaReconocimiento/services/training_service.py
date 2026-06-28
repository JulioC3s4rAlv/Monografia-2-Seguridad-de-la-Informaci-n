import logging
import threading
from typing import Callable, Optional

from models.trainer import Trainer

logger = logging.getLogger("sistema_reconocimiento.services.training")


class TrainingService:
    def __init__(self, detector, recognizer, database, settings):
        self._trainer = Trainer(detector, recognizer, database, settings)
        self._running = False

    def train_new_users(self, progress_callback: Callable = None,
                        done_callback: Callable = None) -> threading.Thread:
        if self._running:
            logger.warning("Training already in progress")
            return None

        self._running = True
        thread = threading.Thread(
            target=self._run_training,
            args=(progress_callback, done_callback),
            daemon=True,
            name="TrainingThread",
        )
        thread.start()
        return thread

    def _run_training(self, progress_callback, done_callback):
        try:
            results = self._trainer.train_new_users(
                progress_callback=progress_callback
            )
            if done_callback:
                done_callback(results)
        except Exception as e:
            logger.error(f"Training error: {e}")
            if done_callback:
                done_callback({"trained": 0, "failed": 0,
                               "skipped": 0, "error": str(e)})
        finally:
            self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
