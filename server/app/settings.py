import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int, minimum: int = 1) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return max(minimum, value)


def parse_origins() -> list[str]:
    raw = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
HISTORY_ENABLED = env_bool("HISTORY_ENABLED", APP_ENV == "development")
ALLOWED_ORIGINS = parse_origins()
REQUESTS_PER_MINUTE = env_int("REQUESTS_PER_MINUTE", 20)
MAX_REQUEST_BYTES = env_int("MAX_REQUEST_BYTES", 250_000)

_default_db_path = Path(__file__).resolve().parent.parent / "conceptcanvas.db"
DB_PATH = Path(os.getenv("DB_PATH", str(_default_db_path))).expanduser().resolve()
