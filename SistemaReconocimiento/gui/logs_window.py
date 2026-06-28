import tkinter as tk
from tkinter import ttk


class LogsWindow(tk.Toplevel):
    def __init__(self, parent, log_service):
        super().__init__(parent)
        self._log_service = log_service

        self.title("Registro de Logs")
        self.geometry("1100x600")
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._load_logs()

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        filter_frame = ttk.LabelFrame(main, text="Filtros", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Tipo:").grid(row=0, column=0, padx=5)
        self._type_var = tk.StringVar(value="Todos")
        ttk.Combobox(filter_frame, textvariable=self._type_var,
                     values=["Todos", "Personal activo", "Personal inactivo",
                             "Desconocido"],
                     state="readonly", width=20).grid(row=0, column=1, padx=5)

        ttk.Button(filter_frame, text="Filtrar",
                   command=self._load_logs).grid(row=0, column=2, padx=20)
        ttk.Button(filter_frame, text="Actualizar",
                   command=self._load_logs).grid(row=0, column=3, padx=5)

        columns = ("id", "date", "time", "code", "name", "person_type",
                   "status", "decision", "confidence", "image_path")
        self._tree = ttk.Treeview(main, columns=columns, show="headings",
                                  height=20)

        col_widths = {
            "id": 40, "date": 100, "time": 80, "code": 100, "name": 150,
            "person_type": 130, "status": 80, "decision": 130,
            "confidence": 80, "image_path": 150,
        }
        headings = {
            "id": "ID", "date": "Fecha", "time": "Hora", "code": "Código",
            "name": "Nombre", "person_type": "Tipo", "status": "Estado",
            "decision": "Decisión", "confidence": "Confianza",
            "image_path": "Imagen",
        }

        for col in columns:
            self._tree.heading(col, text=headings[col])
            self._tree.column(col, width=col_widths[col], minwidth=40)

        scrollbar = ttk.Scrollbar(main, orient=tk.VERTICAL,
                                  command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_logs(self):
        for item in self._tree.get_children():
            self._tree.delete(item)

        person_type = self._type_var.get()
        if person_type == "Todos":
            person_type = None

        logs = self._log_service.get_logs(limit=500, person_type=person_type)
        for log in logs:
            values = (
                log.get("id", ""),
                log.get("date", ""),
                log.get("time", ""),
                log.get("code", ""),
                log.get("name", ""),
                log.get("person_type", ""),
                log.get("status", ""),
                log.get("decision", ""),
                f"{log.get('confidence', 0):.3f}" if log.get("confidence") else "",
                log.get("image_path", ""),
            )
            self._tree.insert("", tk.END, values=values)
