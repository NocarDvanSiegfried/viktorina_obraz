from gigachat import GigaChat
from gigachat.exceptions import UnprocessableEntityError

from app.core.config import settings
from app.core.logger import logger
from app.services.e2e_mocks import E2E_MOCK_CHAT_RESPONSE, E2E_MOCK_OCR_TEXT
from app.services.gigachat_chat_meta import GigaChatChatMeta
from app.services.quiz_generation_config import CHAT_MAX_TOKENS_CAP

VISION_OCR_PROMPT = (
    "Извлеки весь читаемый текст с приложенного изображения или документа. "
    "Верни только текст учебного материала (русский или английский). "
    "Без markdown и пояснений. Если текста нет — верни пустую строку."
)


class GigaChatService:
    def __init__(self) -> None:
        self.last_chat_meta: GigaChatChatMeta | None = None

    @staticmethod
    def _read_usage_tokens(usage: object | None) -> tuple[int | None, int | None, int | None]:
        if usage is None:
            return None, None, None
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        return (
            int(prompt_tokens) if prompt_tokens is not None else None,
            int(completion_tokens) if completion_tokens is not None else None,
            int(total_tokens) if total_tokens is not None else None,
        )

    @staticmethod
    def _read_finish_reason(choice: object) -> str | None:
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason is None:
            return None
        return str(finish_reason).strip().lower() or None

    def _client_kwargs(self, *, model: str | None = None) -> dict:
        ca_bundle = settings.GIGACHAT_CA_BUNDLE_FILE
        client_kwargs = {
            "credentials": settings.GIGACHAT_AUTH_KEY,
            "scope": settings.GIGACHAT_SCOPE,
            "model": model or settings.GIGACHAT_MODEL,
            "verify_ssl_certs": True,
        }
        if ca_bundle:
            client_kwargs["ca_bundle_file"] = ca_bundle
        return client_kwargs

    def _get_client(self, *, model: str | None = None) -> GigaChat:
        return GigaChat(**self._client_kwargs(model=model))

    def chat(
        self,
        messages: list,
        temperature: float = 0.2,
        *,
        max_tokens: int | None = None,
    ) -> str:
        if settings.E2E_MOCK_GIGACHAT:
            logger.info("GigaChat mock chat (E2E_MOCK_GIGACHAT)")
            self.last_chat_meta = GigaChatChatMeta(
                finish_reason="stop",
                completion_tokens=None,
                prompt_tokens=None,
                total_tokens=None,
            )
            return E2E_MOCK_CHAT_RESPONSE

        formatted_messages = [
            {"role": message["role"], "content": message["content"]}
            for message in messages
        ]

        token_budget = max_tokens if max_tokens is not None else CHAT_MAX_TOKENS_CAP
        token_budget = min(CHAT_MAX_TOKENS_CAP, max(256, token_budget))

        with self._get_client() as giga:
            response = giga.chat(
                {
                    "messages": formatted_messages,
                    "temperature": temperature,
                    "max_tokens": token_budget,
                }
            )

        choice = response.choices[0]
        content = choice.message.content or ""
        prompt_tokens, completion_tokens, total_tokens = self._read_usage_tokens(
            getattr(response, "usage", None)
        )
        finish_reason = self._read_finish_reason(choice)
        self.last_chat_meta = GigaChatChatMeta(
            finish_reason=finish_reason,
            completion_tokens=completion_tokens,
            prompt_tokens=prompt_tokens,
            total_tokens=total_tokens,
        )
        logger.info(
            "GigaChat response received | chars=%s finish_reason=%s "
            "completion_tokens=%s prompt_tokens=%s",
            len(content),
            finish_reason,
            completion_tokens,
            prompt_tokens,
        )
        return content

    def extract_text_from_visual(self, filename: str, content: bytes) -> str:
        """OCR via GigaChat vision: upload file and read text from attachment."""
        if settings.E2E_MOCK_GIGACHAT:
            logger.info("GigaChat mock vision OCR (E2E_MOCK_GIGACHAT) | file=%s", filename)
            return E2E_MOCK_OCR_TEXT

        vision_model = settings.GIGACHAT_VISION_MODEL
        try:
            with self._get_client(model=vision_model) as giga:
                uploaded = giga.upload_file((filename, content))
                file_id = uploaded.id_

                response = giga.chat(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": VISION_OCR_PROMPT,
                                "attachments": [file_id],
                            }
                        ],
                        "temperature": 0.1,
                        "max_tokens": 8000,
                    }
                )
        except UnprocessableEntityError as exc:
            raise ValueError(
                f"Модель {vision_model!r} не поддерживает изображения. "
                "Укажите GIGACHAT_VISION_MODEL=GigaChat-Pro (или GigaChat-2-Pro) в .env."
            ) from exc

        text = (response.choices[0].message.content or "").strip()
        logger.info(
            "GigaChat vision OCR | model=%s file=%s chars=%s",
            vision_model,
            filename,
            len(text),
        )
        return text


gigachat_service = GigaChatService()
