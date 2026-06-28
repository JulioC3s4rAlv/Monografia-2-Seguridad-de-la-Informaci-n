import queue
import threading
from typing import Optional

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox

from gui.widgets import VideoFeed, InfoPanel, ActionButtons
from gui.register_window import RegisterWindow
from gui.logs_window import LogsWindow
from gui.statistics_window import StatisticsWindow
from gui.admin_window import AdminWindow
from services.recognition_service import RecognitionEvent
from services.log_service import LogService


class MainWindow:
    def __init__(self, root: tk.Tk, services: dict, settings):
        self._root = root
        self._services = services
        self._settings = settings

        self._recognition_service = services["recognition"]
        self._training_service = services["training"]
        self._user_service = services["user"]
        self._log_service = services["log"]
        self._stats_service = services["statistics"]

        self._current_event: Optional[RecognitionEvent] = None
        self._current_face: Optional[np.ndarray] = None
        self._recognition_active = False

        self._build_ui()

    def _build_ui(self):
        self._root.title("Sistema de Reconocimiento Facial")
        self._root.state("zoomed")
        self._root.configure(bg="#ecf0f1")

        self._create_toolbar()
        self._create_main_area()
        self._create_status_bar()

    def _create_toolbar(self):
        toolbar = tk.Frame(self._root, bg="#34495e", height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_style = {"bg": "#2c3e50", "fg": "white",
                     "font": ("Arial", 10, "bold"),
                     "padx": 15, "pady": 5, "cursor": "hand2",
                     "relief": tk.RAISED, "bd": 0}

        tk.Button(toolbar, text="Registrar usuario",
                  command=self._open_register, **btn_style).pack(side=tk.LEFT, padx=3, pady=5)
        tk.Button(toolbar, text="Entrenar nuevos usuarios",
                  command=self._start_training, **btn_style).pack(side=tk.LEFT, padx=3, pady=5)

        self._btn_start = tk.Button(toolbar, text="Iniciar reconocimiento",
                                    command=self._toggle_recognition, **btn_style)
        self._btn_start.pack(side=tk.LEFT, padx=3, pady=5)

        tk.Button(toolbar, text="Ver logs",
                  command=self._open_logs, **btn_style).pack(side=tk.LEFT, padx=3, pady=5)
        tk.Button(toolbar, text="Estadísticas",
                  command=self._open_statistics, **btn_style).pack(side=tk.LEFT, padx=3, pady=5)
        tk.Button(toolbar, text="Administrar usuarios",
                  command=self._open_admin, **btn_style).pack(side=tk.LEFT, padx=3, pady=5)

        self._training_label = tk.Label(toolbar, text="",
                                        bg="#34495e", fg="#f1c40f",
                                        font=("Arial", 10))
        self._training_label.pack(side=tk.RIGHT, padx=10, pady=5)

    def _create_main_area(self):
        main = tk.Frame(self._root, bg="#ecf0f1")
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_panel = tk.Frame(main, bg="black", relief=tk.SUNKEN, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._video_feed = VideoFeed(left_panel, width=640, height=480)
        self._video_feed.pack(fill=tk.BOTH, expand=True)

        right_panel = tk.Frame(main, bg="white", width=320,
                               relief=tk.SUNKEN, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_panel.pack_propagate(False)

        self._info_panel = InfoPanel(right_panel)
        self._info_panel.pack(fill=tk.BOTH, expand=True)

        self._action_buttons = ActionButtons(
            right_panel,
            allow_callback=self._allow_entry,
            deny_callback=self._deny_entry,
        )

    def _create_status_bar(self):
        status = tk.Frame(self._root, bg="#2c3e50", height=25)
        status.pack(side=tk.BOTTOM, fill=tk.X)

        self._status_var = tk.StringVar(value="Listo")
        tk.Label(status, textvariable=self._status_var,
                 bg="#2c3e50", fg="white",
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=10)

    def _open_register(self):
        RegisterWindow(self._root, self._user_service, self._settings)

    def _open_logs(self):
        LogsWindow(self._root, self._log_service)

    def _open_statistics(self):
        StatisticsWindow(self._root, self._stats_service)

    def _open_admin(self):
        AdminWindow(self._root, self._user_service, self._settings)

    def _start_training(self):
        if self._training_service.is_running:
            messagebox.showinfo("Entrenamiento",
                                "Ya hay un entrenamiento en progreso")
            return

        self._training_label.config(text="Entrenando...")
        self._training_service.train_new_users(
            progress_callback=self._on_training_progress,
            done_callback=self._on_training_done,
        )

    def _on_training_progress(self, current: int, total: int, name: str):
        self._root.after(0, lambda: self._training_label.config(
            text=f"Entrenando {current}/{total}: {name}"))

    def _on_training_done(self, results: dict):
        self._root.after(0, lambda: self._training_finished(results))

    def _training_finished(self, results: dict):
        self._training_label.config(text="")
        if results.get("error"):
            messagebox.showerror("Error", f"Error en entrenamiento: {results['error']}")
            return

        msg = (f"Entrenamiento completado:\n"
               f"Entrenados: {results['trained']}\n"
               f"Fallidos: {results['failed']}\n"
               f"Sin video: {results['skipped']}")
        messagebox.showinfo("Entrenamiento", msg)

        if results["trained"] > 0:
            self._recognition_service.reload_gallery()

    def _toggle_recognition(self):
        if self._recognition_active:
            self._stop_recognition()
        else:
            self._start_recognition()

    def _start_recognition(self):
        if self._recognition_service.start():
            self._recognition_active = True
            self._btn_start.config(text="Detener reconocimiento", bg="#c0392b")
            self._status_var.set("Reconocimiento activo")
            self._poll_queue()
        else:
            messagebox.showerror("Error",
                                 "No se pudo iniciar la cámara.\n"
                                 "Verifique que la cámara esté conectada.")

    def _stop_recognition(self):
        self._recognition_service.stop()
        self._recognition_active = False
        self._btn_start.config(text="Iniciar reconocimiento", bg="#2c3e50")
        self._status_var.set("Reconocimiento detenido")
        self._video_feed.clear()
        self._info_panel.clear()
        self._action_buttons.hide()

    def _poll_queue(self):
        if not self._recognition_active:
            return

        try:
            while True:
                event = self._recognition_service.event_queue.get_nowait()
                self._process_event(event)
        except queue.Empty:
            pass

        self._root.after(50, self._poll_queue)

    def _process_event(self, event: RecognitionEvent):
        self._current_event = event
        self._current_face = event.face_image

        if event.frame is not None:
            self._video_feed.update_frame(event.frame)

        if event.person_type == "none":
            return

        if event.person_type == "active":
            self._info_panel.show_user(
                name=event.full_name,
                code=event.code or "---",
                status=event.status or "Activo",
                person_type="Personal activo",
                confidence=event.confidence or 0,
                photo_path=event.photo_path,
            )
            self._action_buttons.hide()
            self._recognition_service.handle_decision(event, "Permitir automático")

        elif event.person_type == "inactive":
            self._info_panel.show_user(
                name=event.full_name,
                code=event.code or "---",
                status=event.status or "Inactivo",
                person_type="Personal inactivo",
                confidence=event.confidence or 0,
                photo_path=event.photo_path,
            )
            self._action_buttons.show()

        elif event.person_type == "unknown":
            self._info_panel.show_unknown()
            if event.face_image is not None:
                self._info_panel.show_face_image(event.face_image)
            self._action_buttons.show()

    def _allow_entry(self):
        if self._current_event:
            self._recognition_service.handle_decision(
                self._current_event, "Permitir")
            self._action_buttons.hide()

    def _deny_entry(self):
        if self._current_event:
            self._recognition_service.handle_decision(
                self._current_event, "Denegar")
            self._action_buttons.hide()
