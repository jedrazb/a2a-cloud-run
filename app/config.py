from __future__ import annotations

import os


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

        # HTTP client timeout seconds
        try:
            self.TIMEOUT_SECONDS: float = float(os.environ.get("TIMEOUT_SECONDS", "30"))
        except ValueError:
            self.TIMEOUT_SECONDS = 120.0

        # Proxy base URL for URL remapping in agent.json responses
        # Proxy base URL for URL remapping in agent.json responses
        self.PROXY_BASE_URL: str = os.environ.get(
            "PROXY_BASE_URL", "http://127.0.0.1:8080"
        )

        # Configurable downstream agent API path (used for both POST and JSON card)
        agent_proxy_path = os.environ.get("AGENT_PROXY_PATH", "/elastic/agent")
        if not agent_proxy_path.startswith("/"):
            agent_proxy_path = "/" + agent_proxy_path
        # Normalize: remove trailing slash
        agent_proxy_path = agent_proxy_path.rstrip("/") or "/elastic/agent"
        self.AGENT_PROXY_PATH: str = agent_proxy_path

        #  Upstream Kibana A2A endpoint path
        self.KIBANA_A2A_ENDPOINT: str = "api/chat/a2a"


settings = Settings()
