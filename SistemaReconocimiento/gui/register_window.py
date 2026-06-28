from pathlib import Path
from tkinter import ttk, messagebox
import tkinter as tk

from utils.file_utils import ensure_dir


class RegisterWindow(tk.Toplevel):
    def __init__(self, parent, user_service, settings):
        super().__init__(parent)
        self._user_service = user_service
        self._settings = settings

        self.title("Registrar Usuario")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._photo_path = None
        self._video_path = None
        self._build_ui()

    def _build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Registro de nuevo usuario",
                  font=("Arial", 14, "bold")).pack(pady=(0, 15))

        fields = [
            ("Código institucional:", "code"),
            ("Nombres:", "names"),
            ("Apellidos:", "last_names"),
        ]

        self._entries = {}
        for label, key in fields:
            row = ttk.Frame(main)
            row.pack(fill=tk.X, pady=5)
            ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
            entry = ttk.Entry(row)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._entries[key] = entry

        row = ttk.Frame(main)
        row.pack(fill=tk.X, pady=10)
        ttk.Label(row, text="Estado:", width=18).pack(side=tk.LEFT)
        self._status_var = tk.StringVar(value="Activo")
        ttk.Combobox(row, textvariable=self._status_var,
                     values=["Activo", "Inactivo"],
                     state="readonly", width=15).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Seleccionar foto",
                   command=self._select_photo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Seleccionar video",
                   command=self._select_video).pack(side=tk.LEFT, padx=5)

        self._photo_label = ttk.Label(main, text="Sin foto seleccionada",
                                      foreground="gray")
        self._photo_label.pack()
        self._video_label = ttk.Label(main, text="Sin video seleccionado",
                                      foreground="gray")
        self._video_label.pack()

        ttk.Button(main, text="Guardar",
                   command=self._save).pack(pady=15)

    def _select_photo(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Seleccionar fotografía",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            self._photo_path = path
            self._photo_label.config(text=f"Foto: {Path(path).name}",
                                     foreground="green")

    def _select_video(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Seleccionar video de entrenamiento",
            filetypes=[("Videos", "*.mp4 *.avi *.mov *.mkv")])
        if path:
            self._video_path = path
            self._video_label.config(text=f"Video: {Path(path).name}",
                                     foreground="green")

    def _save(self):
        code = self._entries["code"].get().strip()
        names = self._entries["names"].get().strip()
        last_names = self._entries["last_names"].get().strip()
        status = self._status_var.get()

        if not all([code, names, last_names]):
            messagebox.showerror("Error", "Todos los campos son obligatorios")
            return

        if not self._video_path or not Path(self._video_path).exists():
            messagebox.showerror("Error", "Debe seleccionar un video de entrenamiento")
            return

        try:
            result = self._user_service.register_user(
                code=code,
                names=names,
                last_names=last_names,
                status=status,
                photo_path=self._photo_path,
            )

            import shutil
            dst = self._settings.new_videos_path / f"{code}{Path(self._video_path).suffix}"
            shutil.copy2(str(self._video_path), str(dst))

            messagebox.showinfo("Éxito",
                                f"Usuario {code} registrado correctamente")
            self.destroy()

        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al registrar: {e}")
