"""Mirrors frontend apiErrorMessage.ts (UI-9)."""

GIGACHAT_PATTERNS = [
    "gigachat",
    "не удалось сгенерировать викторину",
    "не удалось пересоздать вопрос",
    "502",
    "bad gateway",
]

NETWORK_PATTERNS = [
    "failed to fetch",
    "networkerror",
    "network error",
    "load failed",
]


def _map_error_message(error: str, fallback: str = "Что-то пошло не так. Попробуйте ещё раз.") -> str:
    trimmed = error.strip()
    if not trimmed:
        return fallback
    lower = trimmed.lower()
    if any(pattern in lower for pattern in GIGACHAT_PATTERNS):
        return (
            "Сервис ИИ временно недоступен. Подождите минуту и попробуйте снова. "
            "Если ошибка повторяется — упростите материал или используйте текст вместо файла."
        )
    if any(pattern in lower for pattern in NETWORK_PATTERNS):
        return "Нет связи с сервером. Проверьте интернет и обновите страницу."
    return trimmed


def test_maps_gigachat_502_message():
    raw = "Не удалось сгенерировать викторину: Connection timeout"
    mapped = _map_error_message(raw)
    assert "Сервис ИИ временно недоступен" in mapped


def test_maps_network_error():
    mapped = _map_error_message("Failed to fetch")
    assert "Нет связи с сервером" in mapped


def test_keeps_validation_message():
    mapped = _map_error_message("Укажите тему викторины.")
    assert mapped == "Укажите тему викторины."
