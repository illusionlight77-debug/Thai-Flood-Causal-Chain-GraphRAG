"""Neo4j driver wrapper — อ่าน creds/uri จาก src.config.settings."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from src.config import settings


class Neo4jClient:
    def __init__(self, uri: str | None = None, user: str | None = None, password: str | None = None):
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            from neo4j import GraphDatabase  # import lazily เพื่อไม่บังคับ dep ตอน scaffold

            self._driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self._driver

    @contextmanager
    def session(self) -> Iterator["object"]:
        with self.driver.session() as s:
            yield s

    def run(self, cypher: str, **params):
        with self.session() as s:
            return list(s.run(cypher, **params))

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
