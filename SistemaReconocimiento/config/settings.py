import json
import os
import threading
from pathlib import Path


class Settings:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, config_path: str = None):
        if self._initialized:
            return
        self._initialized = True

        self._base_dir = Path(__file__).resolve().parent.parent
        if config_path is None:
            config_path = self._base_dir / "config" / "config.json"

        self._config_path = Path(config_path)
        self._data = self._load_defaults()
        self._load_config()

    def _load_defaults(self):
        return {
            "database": {"path": "database/database.db"},
            "recognition": {
                "confidence_threshold": 0.4,
                "min_log_interval_minutes": 5,
            },
            "camera": {
                "device_id": 0,
                "frame_width": 640,
                "frame_height": 480,
            },
            "training": {
                "max_frames_per_video": 100,
                "face_detection_confidence": 0.5,
                "frame_interval": 5,
            },
            "log": {
                "image_enabled": True,
                "save_only_decision_images": True,
                "interval_minutes": 5,
            },
            "model": {
                "name": "buffalo_s",
                "providers": ["CUDAExecutionProvider", "CPUExecutionProvider"],
                "root": "models/pretrained",
            },
            "paths": {
                "new_videos": "data/new_videos",
                "trained_videos": "data/trained_videos",
                "reference_images": "data/reference_images",
                "captured_faces": "data/captured_faces",
                "exports": "data/exports",
                "log_images": "logs/images",
                "log_reports": "logs/reports",
                "system_log": "logs/system.log",
            },
        }

    def _load_config(self):
        if self._config_path.exists():
            with open(self._config_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            self._deep_update(self._data, loaded)

    def _deep_update(self, base, updates):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value

    def save(self):
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4, ensure_ascii=False)

    def get(self, *keys, default=None):
        current = self._data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, value, *keys):
        current = self._data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    def resolve_path(self, relative_path: str) -> Path:
        p = Path(relative_path)
        if p.is_absolute():
            return p
        return (self._base_dir / p).resolve()

    @property
    def database_path(self) -> Path:
        return self.resolve_path(self.get("database", "path"))

    @property
    def confidence_threshold(self) -> float:
        return self.get("recognition", "confidence_threshold", default=0.4)

    @property
    def min_log_interval_minutes(self) -> int:
        return self.get("recognition", "min_log_interval_minutes", default=5)

    @property
    def camera_device_id(self) -> int:
        return self.get("camera", "device_id", default=0)

    @property
    def camera_frame_width(self) -> int:
        return self.get("camera", "frame_width", default=640)

    @property
    def camera_frame_height(self) -> int:
        return self.get("camera", "frame_height", default=480)

    @property
    def max_frames_per_video(self) -> int:
        return self.get("training", "max_frames_per_video", default=100)

    @property
    def face_detection_confidence(self) -> float:
        return self.get("training", "face_detection_confidence", default=0.5)

    @property
    def training_frame_interval(self) -> int:
        return self.get("training", "frame_interval", default=5)

    @property
    def model_name(self) -> str:
        return self.get("model", "name", default="buffalo_s")

    @property
    def model_providers(self) -> list:
        return self.get("model", "providers", default=["CPUExecutionProvider"])

    @property
    def model_root(self) -> Path:
        return self.resolve_path(self.get("model", "root", default="models/pretrained"))

    @property
    def new_videos_path(self) -> Path:
        return self.resolve_path(self.get("paths", "new_videos"))

    @property
    def trained_videos_path(self) -> Path:
        return self.resolve_path(self.get("paths", "trained_videos"))

    @property
    def reference_images_path(self) -> Path:
        return self.resolve_path(self.get("paths", "reference_images"))

    @property
    def captured_faces_path(self) -> Path:
        return self.resolve_path(self.get("paths", "captured_faces"))

    @property
    def exports_path(self) -> Path:
        return self.resolve_path(self.get("paths", "exports"))

    @property
    def log_images_path(self) -> Path:
        return self.resolve_path(self.get("paths", "log_images"))

    @property
    def log_reports_path(self) -> Path:
        return self.resolve_path(self.get("paths", "log_reports"))

    @property
    def system_log_path(self) -> Path:
        return self.resolve_path(self.get("paths", "system_log"))


settings = Settings()
