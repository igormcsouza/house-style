import os


def environment() -> str:
    return os.environ.get("ENVIRONMENT", "local")
