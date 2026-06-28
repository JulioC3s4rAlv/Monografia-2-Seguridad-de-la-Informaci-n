import sys
import os
import warnings

warnings.filterwarnings("ignore", message=".*SimilarityTransform.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*from_estimate.*", category=FutureWarning)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import messagebox

from config.settings import settings
from utils.logger import setup_logger
from database.database import Database, get_database
from services.user_service import UserService
from services.log_service import LogService
from services.training_service import TrainingService
from services.recognition_service import RecognitionService
from services.statistics_service import StatisticsService
from gui.main_window import MainWindow


def initialize_insightface():
    try:
        import insightface
        from insightface.app import FaceAnalysis
        logger.info(f"Loading InsightFace model '{settings.model_name}'...")
        app = FaceAnalysis(
            name=settings.model_name,
            root=str(settings.model_root),
            providers=settings.model_providers,
        )
        app.prepare(ctx_id=0, det_size=(640, 640))
        logger.info("InsightFace model loaded successfully")
        return app
    except ImportError:
        logger.error("InsightFace is not installed. Run: pip install insightface")
        raise
    except Exception as e:
        logger.error(f"Failed to load InsightFace model: {e}")
        raise


def main():
    try:
        setup_logger(
            log_file=str(settings.system_log_path),
            console=True,
        )
    except Exception:
        setup_logger(console=True)

    global logger
    logger = setup_logger("sistema_reconocimiento")

    logger.info("=" * 60)
    logger.info("Sistema de Reconocimiento Facial - Iniciando")
    logger.info("=" * 60)

    try:
        db = get_database(str(settings.database_path))
        logger.info(f"Database initialized at {settings.database_path}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        messagebox.showerror("Error crítico",
                             f"No se pudo inicializar la base de datos:\n{e}")
        sys.exit(1)

    try:
        insightface_app = initialize_insightface()
    except Exception as e:
        messagebox.showerror("Error crítico",
                             f"No se pudo cargar el modelo de IA:\n{e}")
        sys.exit(1)

    from cv.detector import FaceDetector
    from cv.recognizer import FaceRecognizer
    from cv.camera import Camera

    detector = FaceDetector(insightface_app)
    recognizer = FaceRecognizer(
        confidence_threshold=settings.confidence_threshold)

    camera = Camera(
        device_id=settings.camera_device_id,
        frame_width=settings.camera_frame_width,
        frame_height=settings.camera_frame_height,
    )

    user_service = UserService(db, settings)
    log_service = LogService(db, settings)
    training_service = TrainingService(detector, recognizer, db, settings)
    stats_service = StatisticsService(db, settings)

    recognition_service = RecognitionService(
        detector=detector,
        recognizer=recognizer,
        database=db,
        log_service=log_service,
        settings=settings,
        camera=camera,
    )

    services = {
        "user": user_service,
        "training": training_service,
        "recognition": recognition_service,
        "log": log_service,
        "statistics": stats_service,
    }

    root = tk.Tk()
    root.title("Sistema de Reconocimiento Facial")
    try:
        root.state("zoomed")
    except Exception:
        root.geometry("1200x700")

    app = MainWindow(root, services, settings)
    logger.info("Application started")

    def on_closing():
        logger.info("Shutting down...")
        recognition_service.stop()
        db.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
