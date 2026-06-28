import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path


class AdminWindow(tk.Toplevel):
    def __init__(self, parent, user_service, settings):
        super().__init__(parent)
        self._user_service = user_service
        self._settings = settings

        self.title("Administración de Usuarios")
        self.geometry("900x500")
        self.transient(parent)
        self.grab_set()

        self._selected_user_id = None
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        filter_frame = ttk.LabelFrame(main, text="Filtros", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Código:").grid(row=0, column=0, padx=5)
        self._code_entry = ttk.Entry(filter_frame, width=15)
        self._code_entry.grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Nombre:").grid(row=0, column=2, padx=5)
        self._name_entry = ttk.Entry(filter_frame, width=20)
        self._name_entry.grid(row=0, column=3, padx=5)

        ttk.Label(filter_frame, text="Estado:").grid(row=0, column=4, padx=5)
        self._status_var = tk.StringVar(value="Todos")
        ttk.Combobox(filter_frame, textvariable=self._status_var,
                     values=["Todos", "Activo", "Inactivo"],
                     state="readonly", width=10).grid(row=0, column=5, padx=5)

        ttk.Button(filter_frame, text="Buscar",
                   command=self._load_users).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="Limpiar",
                   command=self._clear_filters).grid(row=0, column=7, padx=5)

        columns = ("id", "code", "names", "last_names", "status",
                   "created_at", "training_date")
        self._tree = ttk.Treeview(main, columns=columns, show="headings",
                                  height=15, selectmode="browse")

        col_widths = {"id": 40, "code": 100, "names": 150, "last_names": 150,
                      "status": 80, "created_at": 150, "training_date": 150}
        headings = {"id": "ID", "code": "Código", "names": "Nombres",
                    "last_names": "Apellidos", "status": "Estado",
                    "created_at": "Registro", "training_date": "Entrenamiento"}

        for col in columns:
            self._tree.heading(col, text=headings[col])
            self._tree.column(col, width=col_widths[col], minwidth=40)

        scrollbar = ttk.Scrollbar(main, orient=tk.VERTICAL,
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        action_frame = ttk.Frame(main)
        action_frame.pack(fill=tk.X, pady=10)

        ttk.Button(action_frame, text="Cambiar estado",
                   command=self._toggle_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Editar nombres",
                   command=self._edit_names).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Editar apellidos",
                   command=self._edit_last_names).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Actualizar foto",
                   command=self._update_photo).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Eliminar usuario",
                   command=self._delete_user).pack(side=tk.LEFT, padx=5)

        self._status_label = ttk.Label(main, text="", foreground="blue")
        self._status_label.pack()

    def _load_users(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        all_users = self._user_service.get_all_users()
        code_filter = self._code_entry.get().strip().lower()
        name_filter = self._name_entry.get().strip().lower()
        status_filter = self._status_var.get()

        for user in all_users:
            if code_filter and code_filter not in user.get("code", "").lower():
                continue
            if name_filter and name_filter not in f"{user.get('names', '')} {user.get('last_names', '')}".lower():
                continue
            if status_filter != "Todos" and user.get("status") != status_filter:
                continue

            training = user.get("training_date") or "—"
            values = (
                user["id"],
                user.get("code", ""),
                user.get("names", ""),
                user.get("last_names", ""),
                user.get("status", ""),
                user.get("created_at", ""),
                training,
            )
            self._tree.insert("", tk.END, values=values)

    def _clear_filters(self):
        self._code_entry.delete(0, tk.END)
        self._name_entry.delete(0, tk.END)
        self._status_var.set("Todos")
        self._load_users()

    def _on_select(self, event):
        selected = self._tree.selection()
        if selected:
            item = self._tree.item(selected[0])
            self._selected_user_id = item["values"][0]

    def _get_selected_user(self):
        if not self._selected_user_id:
            messagebox.showwarning("Selección", "Seleccione un usuario")
            return None
        return self._user_service.get_user(user_id=self._selected_user_id)

    def _toggle_status(self):
        user = self._get_selected_user()
        if not user:
            return
        new_status = "Inactivo" if user["status"] == "Activo" else "Activo"
        if messagebox.askyesno("Cambiar estado",
                               f"¿Cambiar estado de {user['code']} a {new_status}?"):
            self._user_service.update_user(user["id"], status=new_status)
            self._load_users()
            self._status_label.config(text=f"Estado actualizado a {new_status}",
                                      foreground="green")

    def _edit_names(self):
        user = self._get_selected_user()
        if not user:
            return
        dialog = _EditDialog(self, "Editar nombres", "Nombres:", user["names"])
        if dialog.result is not None:
            self._user_service.update_user(user["id"], names=dialog.result)
            self._load_users()
            self._status_label.config(text="Nombres actualizados", foreground="green")

    def _edit_last_names(self):
        user = self._get_selected_user()
        if not user:
            return
        dialog = _EditDialog(self, "Editar apellidos", "Apellidos:", user["last_names"])
        if dialog.result is not None:
            self._user_service.update_user(user["id"], last_names=dialog.result)
            self._load_users()
            self._status_label.config(text="Apellidos actualizados", foreground="green")

    def _update_photo(self):
        user = self._get_selected_user()
        if not user:
            return
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Seleccionar fotografía",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
        if path:
            from utils.file_utils import safe_copy
            import shutil
            src = Path(path)
            dst = self._settings.reference_images_path / f"user_{user['code']}{src.suffix}"
            shutil.copy2(str(src), str(dst))
            self._user_service.update_user(user["id"], photo_path=str(dst))
            self._status_label.config(text="Fotografía actualizada", foreground="green")

    def _delete_user(self):
        user = self._get_selected_user()
        if not user:
            return
        if messagebox.askyesno("Confirmar eliminación",
                               f"¿Eliminar a {user['names']} {user['last_names']} ({user['code']})?\n\nEsta acción no se puede deshacer.",
                               icon="warning"):
            self._user_service.delete_user(user["id"])
            self._selected_user_id = None
            self._load_users()
            self._status_label.config(text="Usuario eliminado", foreground="red")


class _EditDialog(tk.Toplevel):
    def __init__(self, parent, title, label_text, current_value):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x120")
        self.transient(parent)
        self.grab_set()
        self.result = None

        ttk.Label(self, text=label_text, padding=10).pack()
        self._entry = ttk.Entry(self, width=40)
        self._entry.insert(0, current_value)
        self._entry.pack(padx=10, pady=5)
        self._entry.focus_set()
        self._entry.bind("<Return>", lambda e: self._save())

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Guardar", command=self._save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _save(self):
        value = self._entry.get().strip()
        if value:
            self.result = value
            self.destroy()
        else:
            messagebox.showwarning("Validación", "El valor no puede estar vacío")
