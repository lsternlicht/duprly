from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from loguru import logger

from duprly.dupr_client import DuprClient
from duprly.dupr_db import open_db


@dataclass
class AppRuntime:
    verbose: bool = False
    quiet: bool = False
    no_color: bool = False
    json_output: bool = False
    config_path: Optional[str] = None
    interactive: bool = True

    _client: Optional[DuprClient] = None
    _engine: Any = None
    _env_loaded: bool = False

    def setup_logging(self) -> None:
        logger.remove()
        if self.quiet:
            level = "WARNING"
        elif self.verbose:
            level = "DEBUG"
        else:
            level = "INFO"
        logger.add(
            sys.stderr,
            level=level,
            colorize=not self.no_color,
            format="<level>{level: <8}</level> | {message}",
        )

    def load_environment(self) -> None:
        if self._env_loaded:
            return
        env_path = self.config_path
        if env_path:
            load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=False)
        self._env_loaded = True

    @property
    def client(self) -> DuprClient:
        if self._client is None:
            self.load_environment()
            self._client = DuprClient(verbose=self.verbose)
        return self._client

    @property
    def engine(self):
        if self._engine is None:
            self._engine = open_db()
        return self._engine

    @property
    def db_path(self) -> Path:
        return Path("dupr.sqlite")

    def require_env(self, key: str) -> str:
        self.load_environment()
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value
