import os
from typing import Optional
from Server.variables import MirageConfig

_DEFAULT_CONFIG_PATH = "Server/config.json"
_CONFIG_PATH: Optional[str] = None
_CONFIG: Optional[MirageConfig] = None

def load_config(file_path: Optional[str] = None, force_reload: bool = False) -> MirageConfig:
    """Load config from disk, caching the result for reuse."""
    global _CONFIG, _CONFIG_PATH

    path = file_path or os.getenv("MIRAGE_CONFIG", _DEFAULT_CONFIG_PATH)

    if force_reload or _CONFIG is None or _CONFIG_PATH != path:
        _CONFIG = MirageConfig.load(path)
        _CONFIG_PATH = path

    return _CONFIG

CONFIG = load_config()