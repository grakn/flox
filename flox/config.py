from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, Callable
import yaml

class FloxConfig(BaseModel):
    service: str = "flox"
    environment: str = "production"
    log_level: str = "INFO"
    log_callback: Optional[Callable[[dict], None]] = None
    projects: dict = {}

    @classmethod
    def load_yaml(cls, path: str) -> "FloxConfig":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def to_yaml(self, path: str):
        with open(path, "w") as f:
            yaml.safe_dump(self.dict(), f)
