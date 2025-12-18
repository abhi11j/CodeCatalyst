"""Environment helpers (env loading)"""
import os
import logging

logger = logging.getLogger(__name__)


def load_env_file(filepath: str = ".env") -> None:
    try:
        if not os.path.exists(filepath):
            logger.debug(".env file not found: %s", filepath)
            return
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):]
                if "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if key not in os.environ:
                    os.environ[key] = val
    except Exception as e:
        logger.debug("Ignoring .env load error: %s", e)
