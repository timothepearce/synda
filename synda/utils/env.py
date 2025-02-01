import os

from dotenv import load_dotenv


load_dotenv()


def is_debug_enabled() -> bool:
    return os.getenv("DEBUG_ENABLED", False) == "true"
