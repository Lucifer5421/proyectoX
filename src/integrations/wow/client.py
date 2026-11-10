"""Cliente MySQL de solo lectura para AzerothCore."""

import re
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

import pymysql
from pymysql.cursors import DictCursor

from src.integrations.wow.config import WowSettings

_IDENTIFIER = re.compile(r"^[A-Za-z0-9_]+$")


def _safe_identifier(name: str) -> str:
    """Valida nombres de base de datos usados en SQL interpolado."""
    if not _IDENTIFIER.match(name):
        raise ValueError(f"Nombre de base de datos inválido: {name!r}")
    return name


class WowClient:
    def __init__(self, settings: WowSettings):
        self.settings = settings

    @contextmanager
    def connect(self) -> Iterator[Any]:
        conn = pymysql.connect(
            host=self.settings.host,
            port=self.settings.port,
            user=self.settings.user,
            password=self.settings.password,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
        try:
            yield conn
        finally:
            conn.close()

    def fetch_characters(self) -> List[Dict[str, Any]]:
        characters = _safe_identifier(self.settings.characters_db)
        auth = _safe_identifier(self.settings.auth_db)
        query = f"""
            SELECT c.guid, c.account, c.name, c.level, c.class, c.money,
                   a.username
            FROM `{characters}`.characters AS c
            JOIN `{auth}`.account AS a ON a.id = c.account
            ORDER BY c.guid
        """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return list(cur.fetchall())

    def fetch_inventory(self) -> List[Dict[str, Any]]:
        characters = _safe_identifier(self.settings.characters_db)
        world = _safe_identifier(self.settings.world_db)
        query = f"""
            SELECT ci.guid AS character_guid,
                   ii.itemEntry AS item_entry,
                   SUM(ii.count) AS cantidad,
                   MAX(it.name) AS item_name,
                   MAX(it.Quality) AS quality,
                   MAX(it.RequiredLevel) AS required_level,
                   MAX(it.BuyPrice) AS buy_price
            FROM `{characters}`.character_inventory AS ci
            JOIN `{characters}`.item_instance AS ii ON ii.guid = ci.item
            JOIN `{world}`.item_template AS it ON it.entry = ii.itemEntry
            GROUP BY ci.guid, ii.itemEntry
            ORDER BY ci.guid, ii.itemEntry
        """
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                return list(cur.fetchall())
