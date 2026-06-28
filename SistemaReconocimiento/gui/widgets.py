import queue
import threading
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

from utils.image_utils import frame_to_tk


class VideoFeed(tk.Canvas):
    def __init__(self, parent, width: int = 640, height: int = 480, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg="black", highlightthickness=0, **kwargs)
        self._width = width
        self._height = height
        self._photo: Optional[ImageTk.PhotoImage] = None
        self._placeholder = None
        self._show_placeholder()

    def _show_placeholder(self):
        self.delete("all")
        self.create_text(
            self._width // 2, self._height // 2,
            text="Cámara desconectada",
            fill="gray", font=("Arial", 16),
            tags="placeholder",
        )

    def update_frame(self, frame: np.ndarray):
        try:
            pil_img = frame_to_tk(frame, width=self._width)
            self._photo = ImageTk.PhotoImage(pil_img)
            self.delete("all")
            self.create_image(
                self._width // 2, self._height // 2,
                image=self._photo, anchor=tk.CENTER,
            )
        except Exception:
            pass

    def clear(self):
        self._show_placeholder()


class InfoPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="white", **kwargs)
        self._photo_label: Optional[tk.Label] = None
        self._name_var = tk.StringVar(value="---")
        self._code_var = tk.StringVar(value="---")
        self._status_var = tk.StringVar(value="---")
        self._confidence_var = tk.StringVar(value="---")
        self._person_type_var = tk.StringVar(value="---")
        self._build_ui()

    def _build_ui(self):
        header = tk.Label(self, text="Información",
                          font=("Arial", 14, "bold"),
                          bg="#2c3e50", fg="white", pady=8)
        header.pack(fill=tk.X)

        content = tk.Frame(self, bg="white", padx=15, pady=10)
        content.pack(fill=tk.BOTH, expand=True)

        self._photo_label = tk.Label(content, bg="gray", width=120, height=140,
                                     relief=tk.SUNKEN)
        self._photo_label.pack(pady=(0, 10))

        fields = [
            ("Nombre:", self._name_var),
            ("Código:", self._code_var),
            ("Estado:", self._status_var),
            ("Tipo:", self._person_type_var),
            ("Confianza:", self._confidence_var),
        ]
        for label, var in fields:
            row = tk.Frame(content, bg="white")
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=label, font=("Arial", 10, "bold"),
                     bg="white", width=10, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, textvariable=var, font=("Arial", 10),
                     bg="white", anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def show_user(self, name: str, code: str, status: str,
                  person_type: str, confidence: float,
                  photo_path: str = None):
        self._name_var.set(name)
        self._code_var.set(code)
        self._status_var.set(status)
        self._person_type_var.set(person_type)
        self._confidence_var.set(f"{confidence:.2%}" if confidence else "---")

        if photo_path and Path(photo_path).exists():
            try:
                pil_img = Image.open(photo_path)
                pil_img.thumbnail((120, 140), Image.LANCZOS)
                photo = ImageTk.PhotoImage(pil_img)
                self._photo_label.config(image=photo)
                self._photo_label.image = photo
            except Exception:
                self._photo_label.config(image="", text="Sin foto")
        else:
            self._photo_label.config(image="", text="Sin foto")

    def show_unknown(self):
        self._name_var.set("---")
        self._code_var.set("---")
        self._status_var.set("---")
        self._person_type_var.set("Desconocido")
        self._confidence_var.set("---")
        self._photo_label.config(image="", text="Desconocido", fg="red",
                                 font=("Arial", 12))

    def clear(self):
        self._name_var.set("---")
        self._code_var.set("---")
        self._status_var.set("---")
        self._person_type_var.set("---")
        self._confidence_var.set("---")
        self._photo_label.config(image="", text="")

    def show_face_image(self, face_image: np.ndarray):
        try:
            pil_img = frame_to_tk(face_image, width=120)
            photo = ImageTk.PhotoImage(pil_img)
            self._photo_label.config(image=photo)
            self._photo_label.image = photo
        except Exception:
            pass


class ActionButtons(tk.Frame):
    def __init__(self, parent, allow_callback: Callable = None,
                 deny_callback: Callable = None, **kwargs):
        super().__init__(parent, bg="white", **kwargs)

        self._allow_btn = tk.Button(
            self, text="Permitir ingreso",
            command=allow_callback,
            bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
            padx=20, pady=8, cursor="hand2",
        )
        self._allow_btn.pack(side=tk.LEFT, padx=5)

        self._deny_btn = tk.Button(
            self, text="Denegar ingreso",
            command=deny_callback,
            bg="#e74c3c", fg="white", font=("Arial", 12, "bold"),
            padx=20, pady=8, cursor="hand2",
        )
        self._deny_btn.pack(side=tk.LEFT, padx=5)

        self.hide()

    def show(self):
        self.pack(pady=10)

    def hide(self):
        self.pack_forget()
