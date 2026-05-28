import time

from app.core.logger import logger
from app.schemas.material import SourceFragment
from app.schemas.quiz import DifficultyLevel, GenerateQuizResponse
from app.services.gigachat_service import gigachat_service
from app.services.material_service import material_service
from app.services.prompt_service import build_quiz_prompt, build_regenerate_question_prompt
from app.services.quiz_generation_config import (
    QUIZ_GENERATION_MAX_ATTEMPTS,
    QUESTION_REGENERATE_MAX_ATTEMPTS,
    compute_chat_max_tokens,
    explanation_max_chars,
    truncate_explanation,
)
from app.services.quiz_json_parser import JsonExtractionFailed, extract_quiz_json
from app.services.quiz_model_observability import (
    ModelResponseDiagnostics,
    QuizModelResponseError,
    analyze_model_response,
    build_parse_error,
    log_json_parse_failure,
    log_model_response_received,
)


class QuizService:
    def _extract_json(self, raw_text: str) -> dict:
        parsed, _report = extract_quiz_json(raw_text)
        return parsed

    def _parse_model_quiz_json(
        self,
        raw: str,
        *,
        diagnostics: ModelResponseDiagnostics,
    ) -> dict:
        try:
            data, _report = extract_quiz_json(raw)
            return data
        except JsonExtractionFailed as exc:
            err = build_parse_error(
                diagnostics=diagnostics,
                extraction=exc.report,
                parse_error=exc.cause,
            )
            log_json_parse_failure(
                code=err.code,
                diagnostics=diagnostics,
                extraction=exc.report,
                technical_detail=err.technical_detail,
                raw_preview=raw,
            )
            raise err from exc.cause

    def _normalize_difficulty_value(self, value: str) -> str:
        if not isinstance(value, str):
            return "easy"

        value = value.strip()
        if "." in value:
            value = value.split(".")[-1]
        value = value.lower()

        if value in {"easy", "medium", "hard"}:
            return value
        return "easy"

    def _normalize_question_dict(
        self,
        question: dict,
        fallback_difficulty: str,
        *,
        compact: bool = False,
    ) -> dict:
        normalized = dict(question)

        if "correct answers" in normalized and "correct_answers" not in normalized:
            normalized["correct_answers"] = normalized.pop("correct answers")

        if "correctAnswers" in normalized and "correct_answers" not in normalized:
            normalized["correct_answers"] = normalized.pop("correctAnswers")

        if "source fragment id" in normalized and "source_fragment_id" not in normalized:
            normalized["source_fragment_id"] = normalized.pop("source fragment id")

        normalized["difficulty"] = self._normalize_difficulty_value(
            normalized.get("difficulty", fallback_difficulty)
        )

        if "correct_answers" not in normalized:
            normalized["correct_answers"] = []

        if isinstance(normalized.get("explanation"), str):
            normalized["explanation"] = truncate_explanation(
                normalized["explanation"],
                max_chars=explanation_max_chars(compact=compact),
            )

        return normalized

    def _normalize_quiz_response_data(
        self,
        data: dict,
        fallback_difficulty: str,
        *,
        compact: bool = False,
    ) -> dict:
        normalized = dict(data)
        questions = normalized.get("questions", [])
        normalized["questions"] = [
            self._normalize_question_dict(question, fallback_difficulty, compact=compact)
            for question in questions
            if isinstance(question, dict)
        ]
        return normalized

    def _apply_difficulty_to_all_questions(
        self,
        result: GenerateQuizResponse,
        difficulty: str,
    ) -> GenerateQuizResponse:
        difficulty_enum = DifficultyLevel(difficulty)
        updated_questions = [
            question.model_copy(update={"difficulty": difficulty_enum})
            for question in result.questions
        ]
        return result.model_copy(update={"questions": updated_questions})

    def _diagnostics_for_raw(
        self,
        raw: str,
        *,
        question_count: int | None,
    ) -> ModelResponseDiagnostics:
        meta = gigachat_service.last_chat_meta
        return analyze_model_response(
            raw,
            finish_reason=meta.finish_reason if meta else None,
            question_count=question_count,
            completion_tokens=meta.completion_tokens if meta else None,
        )

    def _chat_and_parse_quiz(
        self,
        *,
        messages: list[dict[str, str]],
        temperature: float,
        question_count: int,
        difficulty: str,
        compact: bool,
    ) -> GenerateQuizResponse:
        max_tokens = compute_chat_max_tokens(question_count)
        raw = gigachat_service.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        diagnostics = self._diagnostics_for_raw(raw, question_count=question_count)
        meta = gigachat_service.last_chat_meta
        log_model_response_received(
            diagnostics=diagnostics,
            completion_tokens=meta.completion_tokens if meta else None,
            prompt_tokens=meta.prompt_tokens if meta else None,
        )

        if diagnostics.likely_truncated:
            logger.warning(
                "JSON_TRUNCATED | question_count=%s chars=%s finish_reason=%s",
                question_count,
                diagnostics.raw_chars,
                diagnostics.finish_reason,
            )

        data = self._parse_model_quiz_json(raw, diagnostics=diagnostics)
        data = self._normalize_quiz_response_data(data, difficulty, compact=compact)
        result = GenerateQuizResponse(**data)
        return self._apply_difficulty_to_all_questions(result, difficulty)

    def generate_quiz_from_fragments(
        self,
        subject: str,
        grade: str,
        topic: str,
        question_count: int,
        question_types: list[str],
        difficulty: str,
        fragments: list[SourceFragment],
    ) -> GenerateQuizResponse:
        logger.info(
            "generate_quiz_from_fragments | subject=%s grade=%s topic=%s count=%s",
            subject,
            grade,
            topic,
            question_count,
        )

        combined_context = material_service.build_combined_context(
            fragments,
            max_chars=6000,
        )

        last_error: QuizModelResponseError | None = None

        for attempt in range(1, QUIZ_GENERATION_MAX_ATTEMPTS + 1):
            compact = attempt > 1
            prompt = build_quiz_prompt(
                subject=subject,
                grade=grade,
                topic=topic,
                question_count=question_count,
                question_types=question_types,
                difficulty=difficulty,
                combined_context=combined_context,
                fragments=fragments,
                compact=compact,
            )
            messages = [
                {"role": "system", "content": "Ты возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt},
            ]
            temperature = 0.15 if compact else 0.2

            try:
                if attempt > 1:
                    logger.info(
                        "QUIZ_GENERATION_RETRY | attempt=%s/%s compact=%s",
                        attempt,
                        QUIZ_GENERATION_MAX_ATTEMPTS,
                        compact,
                    )
                    time.sleep(0.5)

                return self._chat_and_parse_quiz(
                    messages=messages,
                    temperature=temperature,
                    question_count=question_count,
                    difficulty=difficulty,
                    compact=compact,
                )
            except QuizModelResponseError as exc:
                last_error = exc
                logger.warning(
                    "QUIZ_GENERATION_RETRY_SCHEDULED | attempt=%s code=%s",
                    attempt,
                    exc.code,
                )
            except Exception as exc:
                logger.error(
                    "JSON_PARSE_ERROR | unexpected | subject=%s topic=%s | %s",
                    subject,
                    topic,
                    exc,
                )
                raise

        assert last_error is not None
        raise last_error

    def regenerate_question(
        self,
        subject: str,
        grade: str,
        topic: str,
        difficulty: str,
        question_type: str,
        current_question_text: str,
        source_fragment_id: str | None,
    ) -> dict:
        last_error: QuizModelResponseError | None = None

        for attempt in range(1, QUESTION_REGENERATE_MAX_ATTEMPTS + 1):
            compact = attempt > 1
            prompt = build_regenerate_question_prompt(
                subject=subject,
                grade=grade,
                topic=topic,
                difficulty=difficulty,
                question_type=question_type,
                current_question_text=current_question_text,
                source_fragment_id=source_fragment_id,
                compact=compact,
            )
            messages = [
                {"role": "system", "content": "Ты возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt},
            ]

            try:
                if attempt > 1:
                    logger.info(
                        "QUESTION_REGENERATE_RETRY | attempt=%s/%s",
                        attempt,
                        QUESTION_REGENERATE_MAX_ATTEMPTS,
                    )
                    time.sleep(0.5)

                raw = gigachat_service.chat(
                    messages,
                    temperature=0.25 if compact else 0.3,
                    max_tokens=compute_chat_max_tokens(1),
                )
                diagnostics = self._diagnostics_for_raw(raw, question_count=1)
                meta = gigachat_service.last_chat_meta
                log_model_response_received(
                    diagnostics=diagnostics,
                    completion_tokens=meta.completion_tokens if meta else None,
                    prompt_tokens=meta.prompt_tokens if meta else None,
                )

                data = self._parse_model_quiz_json(raw, diagnostics=diagnostics)
                if isinstance(data, dict) and "questions" in data and data["questions"]:
                    data = data["questions"][0]
                if not isinstance(data, dict):
                    raise ValueError("Модель вернула некорректный формат вопроса")

                return self._normalize_question_dict(
                    data,
                    difficulty,
                    compact=compact,
                )
            except QuizModelResponseError as exc:
                last_error = exc

        assert last_error is not None
        raise last_error


quiz_service = QuizService()
