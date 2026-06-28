import tkinter as tk
from tkinter import ttk


class StatisticsWindow(tk.Toplevel):
    def __init__(self, parent, stats_service):
        super().__init__(parent)
        self._stats_service = stats_service

        self.title("Estadísticas")
        self.geometry("700x500")
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="Estadísticas del Sistema",
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))

        self._summary_frame = ttk.LabelFrame(main, text="Resumen", padding=15)
        self._summary_frame.pack(fill=tk.X, pady=10)

        self._stats_labels = {}
        stats = [
            ("total_entries", "Total de ingresos:"),
            ("active_personnel", "Personal activo:"),
            ("inactive_personnel", "Personal inactivo:"),
            ("unknown_allowed", "Desconocidos permitidos:"),
            ("unknown_denied", "Desconocidos denegados:"),
        ]
        for key, label in stats:
            row = ttk.Frame(self._summary_frame)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=label, font=("Arial", 11)).pack(side=tk.LEFT)
            lbl = ttk.Label(row, text="0", font=("Arial", 11, "bold"),
                            foreground="#2c3e50")
            lbl.pack(side=tk.RIGHT)
            self._stats_labels[key] = lbl

        chart_frame = ttk.LabelFrame(main, text="Ingresos por día (últimos 30 días)",
                                     padding=15)
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self._chart_text = tk.Text(chart_frame, height=12, font=("Courier", 9),
                                   bg="white", wrap=tk.NONE)
        self._chart_text.pack(fill=tk.BOTH, expand=True)

        ttk.Button(main, text="Actualizar",
                   command=self._refresh).pack(pady=10)

    def _refresh(self):
        summary = self._stats_service.get_summary()
        for key, lbl in self._stats_labels.items():
            lbl.config(text=str(summary.get(key, 0)))

        days_data = self._stats_service.get_entries_by_day(days=30)
        self._chart_text.delete(1.0, tk.END)
        if days_data:
            max_count = max(d["count"] for d in days_data) if days_data else 1
            for entry in days_data:
                day = entry["date"]
                count = entry["count"]
                bar_len = int((count / max_count) * 40) if max_count > 0 else 0
                bar = "█" * bar_len
                self._chart_text.insert(
                    tk.END, f"{day}  {bar} {count}\n")
        else:
            self._chart_text.insert(tk.END, "No hay datos disponibles\n")
