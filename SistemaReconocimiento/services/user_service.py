import logging
from pathlib import Path
from typing import Optional

from utils.file_utils import safe_copy, unique_filename

logger = logging.getLogger("sistema_reconocimiento.services.user")


class UserService:
    def __init__(self, database, settings):
        self._db = database
        self._settings = settings

    def register_user(self, code: str, names: str, last_names: str,
                      status: str = "Activo", photo: Optional[bytes] = None,
                      photo_path: Optional[str] = None) -> dict:
        if self._db.user_exists(code):
            raise ValueError(f"User with code '{code}' already exists")

        final_photo_path = None
        if photo is not None:
            import cv2
            import numpy as np
            img_array = np.frombuffer(photo, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            if img is not None:
                dest = unique_filename(
                    self._settings.reference_images_path,
                    f"user_{code}", ".jpg")
                cv2.imwrite(str(dest), img)
                final_photo_path = str(dest)
        elif photo_path:
            src = Path(photo_path)
            if src.exists():
                dest = safe_copy(src, self._settings.reference_images_path,
                                 f"user_{code}{src.suffix}")
                if dest:
                    final_photo_path = str(dest)

        user_id = self._db.add_user(code, names, last_names, status, final_photo_path)
        logger.info(f"User registered: {code} - {names} {last_names} (id={user_id})")
        return {"id": user_id, "code": code, "names": names,
                "last_names": last_names, "status": status,
                "photo_path": final_photo_path}

    def get_user(self, code: str = None, user_id: int = None) -> Optional[dict]:
        return self._db.get_user(user_id=user_id, code=code)

    def get_all_users(self) -> list:
        return self._db.get_all_users()

    def update_user(self, user_id: int, **kwargs) -> bool:
        self._db.update_user(user_id, **kwargs)
        return True

    def user_exists(self, code: str) -> bool:
        return self._db.user_exists(code)

    def delete_user(self, user_id: int) -> bool:
        return self._db.delete_user(user_id)
