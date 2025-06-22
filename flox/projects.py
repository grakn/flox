from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Project:
    tenant_id: str
    project_code: str
    config: Dict[str, Any]
    models: Dict[str, Any] = field(default_factory=dict)
    infra: Dict[str, Any] = field(default_factory=dict)
