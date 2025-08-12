from __future__ import annotations

import os
from typing import List
from urllib.parse import urlparse

# Load variables from a local .env file if available (for development).
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # If python-dotenv is not installed, continue; env vars can still be provided by the OS.
    pass


class Settings:
    def __init__(self) -> None:
        # Required service configuration (no header overrides)
        self.AGENT_ID: str | None = os.environ.get("AGENT_ID")
        self.KBN_URL: str | None = os.environ.get("KBN_URL")
        self.API_KEY: str | None = os.environ.get("API_KEY")

        # Optional allowlist of hosts to mitigate open proxy risk. Comma-separated.
        self.ALLOWED_KBN_HOSTS: str | None = os.environ.get("ALLOWED_KBN_HOSTS")

        # HTTP client timeout seconds
        try:
            self.TIMEOUT_SECONDS: float = float(os.environ.get("TIMEOUT_SECONDS", "30"))
        except ValueError:
            self.TIMEOUT_SECONDS = 30.0

    @property
    def allowed_kbn_hosts(self) -> List[str]:
        if not self.ALLOWED_KBN_HOSTS:
            return []
        return [
            h.strip().lower() for h in self.ALLOWED_KBN_HOSTS.split(",") if h.strip()
        ]

    @staticmethod
    def validate_kbn_host(url: str, allowed_hosts: List[str]) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("kbnUrl must be http or https")
        if not parsed.netloc:
            raise ValueError("kbnUrl must include host")
        if (
            allowed_hosts
            and parsed.hostname
            and parsed.hostname.lower() not in allowed_hosts
        ):
            raise ValueError("kbnUrl host is not in allowlist")


settings = Settings()
