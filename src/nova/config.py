import os
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class NovaConfig:
    home: Path

    @property
    def database_path(self) -> Path:
        return self.home / "nova.db"

    @classmethod
    def load(cls) -> "NovaConfig":
        configured = os.environ.get("NOVA_HOME")
        home = Path(configured).expanduser() if configured else Path.home() / ".nova"
        home.mkdir(parents=True, exist_ok=True)
        return cls(home)
