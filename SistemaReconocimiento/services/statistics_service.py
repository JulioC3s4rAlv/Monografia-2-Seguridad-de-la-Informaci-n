import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from utils.helpers import date_now

logger = logging.getLogger("sistema_reconocimiento.services.statistics")


class StatisticsService:
    def __init__(self, database, settings):
        self._db = database
        self._settings = settings

    def get_summary(self) -> dict:
        logs_db = self._db.get_logs(limit=100000)
        if not logs_db:
            return self._empty_summary()

        df = pd.DataFrame(logs_db)
        summary = {
            "total_entries": len(df),
            "active_personnel": len(df[df["person_type"] == "Personal activo"]),
            "inactive_personnel": len(
                df[df["person_type"] == "Personal inactivo"]),
            "unknown_allowed": len(
                df[(df["person_type"] == "Desconocido")
                   & (df["decision"] == "Permitir")]),
            "unknown_denied": len(
                df[(df["person_type"] == "Desconocido")
                   & (df["decision"] == "Denegar")]),
        }
        return summary

    def get_entries_by_day(self, days: int = 30) -> list:
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = date_now()
        return self._db.get_logs_by_day(date_from=date_from, date_to=date_to)

    def get_entries_by_month(self, months: int = 12) -> list:
        date_from = (datetime.now() - timedelta(days=months * 30)).strftime(
            "%Y-%m-%d")
        date_to = date_now()
        return self._db.get_logs_by_month(date_from=date_from, date_to=date_to)

    def get_person_type_breakdown(self) -> dict:
        logs_db = self._db.get_logs(limit=100000)
        if not logs_db:
            return {}
        df = pd.DataFrame(logs_db)
        return df["person_type"].value_counts().to_dict()

    def get_decision_breakdown(self) -> dict:
        logs_db = self._db.get_logs(limit=100000)
        if not logs_db:
            return {}
        df = pd.DataFrame(logs_db)
        return df["decision"].value_counts().to_dict()

    def _empty_summary(self) -> dict:
        return {
            "total_entries": 0,
            "active_personnel": 0,
            "inactive_personnel": 0,
            "unknown_allowed": 0,
            "unknown_denied": 0,
        }

    def export_to_csv(self, filepath: str):
        logs_db = self._db.get_logs(limit=100000)
        if logs_db:
            df = pd.DataFrame(logs_db)
            df.to_csv(filepath, index=False, encoding="utf-8")
            logger.info(f"Statistics exported to {filepath}")
