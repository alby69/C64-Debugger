import os
import json
from typing import Dict, Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

DEFAULT_CONFIG: Dict[str, Any] = {
    "vice": {
        "host": "127.0.0.1",
        "port": 6510,
        "timeout": 2.0,
        "max_retries": 5,
        "backoff_factor": 1.5,
    },
    "logging": {
        "level": "INFO",
        "file": None,
        "max_bytes": 10485760,  # 10MB
        "backup_count": 5
    },
    "llm": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.2,
        "max_tokens": 1000,
        "api_key": "",
        "c64_llm_url": "http://localhost:7860/api/predict",
        "ollama_url": "http://localhost:11434/api/chat"
    }
}

class C64DebuggerConfig:
    """
    Handles loading, parsing, and validating external configuration files (config.json or config.yaml).
    """

    def __init__(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        self._config = self._deep_merge(DEFAULT_CONFIG, config_data or {})

    def _deep_merge(self, base: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        merged = base.copy()
        for k, v in custom.items():
            if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
                merged[k] = self._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    @classmethod
    def load_from_file(cls, filepath: str) -> "C64DebuggerConfig":
        """
        Loads configuration from a JSON or YAML file.
        Falls back to default config if file is missing or invalid.
        """
        if not os.path.exists(filepath):
            return cls()

        _, ext = os.path.splitext(filepath.lower())
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                if ext == ".json":
                    data = json.load(f)
                elif ext in (".yaml", ".yml"):
                    if HAS_YAML:
                        data = yaml.safe_load(f) or {}
                    else:
                        raise ImportError("PyYAML is not installed; cannot load YAML config files. Please install pyyaml.")
                else:
                    raise ValueError(f"Unsupported config file extension: {ext}")
                return cls(data)
        except Exception as e:
            # Fall back to default config on any errors, but log or raise if necessary.
            # For simplicity, we return cls() but can log it if we have a configured logger.
            return cls()

    @property
    def vice_host(self) -> str:
        return self._config["vice"]["host"]

    @property
    def vice_port(self) -> int:
        return self._config["vice"]["port"]

    @property
    def vice_timeout(self) -> float:
        return float(self._config["vice"]["timeout"])

    @property
    def vice_max_retries(self) -> int:
        return int(self._config["vice"]["max_retries"])

    @property
    def vice_backoff_factor(self) -> float:
        return float(self._config["vice"]["backoff_factor"])

    @property
    def log_level(self) -> str:
        return self._config["logging"]["level"]

    @property
    def log_file(self) -> Optional[str]:
        return self._config["logging"]["file"]

    @property
    def log_max_bytes(self) -> int:
        return int(self._config["logging"]["max_bytes"])

    @property
    def log_backup_count(self) -> int:
        return int(self._config["logging"]["backup_count"])

    @property
    def llm_provider(self) -> str:
        return self._config["llm"]["provider"]

    @property
    def llm_model(self) -> str:
        return self._config["llm"]["model"]

    @property
    def llm_temperature(self) -> float:
        return float(self._config["llm"]["temperature"])

    @property
    def llm_max_tokens(self) -> int:
        return int(self._config["llm"]["max_tokens"])

    @property
    def llm_api_key(self) -> str:
        return self._config["llm"]["api_key"]

    @property
    def llm_c64_llm_url(self) -> str:
        return self._config["llm"].get("c64_llm_url", "http://localhost:7860/api/predict")

    @property
    def llm_ollama_url(self) -> str:
        return self._config["llm"].get("ollama_url", "http://localhost:11434/api/chat")
