from typing import Dict, Any
from .config import GroxAppConfig, GroxProjectConfig

class GroxProject:

    def __init__(self, tenant_id:str, app: GroxAppConfig, config: GroxProjectConfig):
        self.tenant_id = tenant_id
        self.project_code = config.metadata.project
        self.app = app
        self.config = config
