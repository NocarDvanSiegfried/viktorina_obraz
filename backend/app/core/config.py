import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Viktorina Obraz API"

    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    GIGACHAT_AUTH_KEY: str = os.getenv("GIGACHAT_AUTH_KEY", "")
    GIGACHAT_SCOPE: str = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    GIGACHAT_MODEL: str = os.getenv("GIGACHAT_MODEL", "GigaChat")
    GIGACHAT_VISION_MODEL: str = os.getenv("GIGACHAT_VISION_MODEL", "GigaChat-Pro")
    GIGACHAT_CA_BUNDLE_FILE: str = os.getenv(
        "GIGACHAT_CA_BUNDLE_FILE",
        "./certs/russian_trusted_root_ca_pem.crt",
    )

    # In-memory rate limiting for quiz generation.
    QUIZ_GENERATE_RATE_LIMIT_MAX_REQUESTS: int = int(
        os.getenv("QUIZ_GENERATE_RATE_LIMIT_MAX_REQUESTS", "3")
    )
    QUIZ_GENERATE_RATE_LIMIT_WINDOW_SECONDS: int = int(
        os.getenv("QUIZ_GENERATE_RATE_LIMIT_WINDOW_SECONDS", "60")
    )

    # E2E / CI: mock GigaChat without network (Playwright, health-check pipelines).
    E2E_MOCK_GIGACHAT: bool = os.getenv("E2E_MOCK_GIGACHAT", "").lower() in (
        "1",
        "true",
        "yes",
    )

    SOURCE_FRAGMENT_PREVIEW_MAX_CHARS: int = int(
        os.getenv("SOURCE_FRAGMENT_PREVIEW_MAX_CHARS", "200")
    )


settings = Settings()
