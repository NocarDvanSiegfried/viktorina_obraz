import json
import re

from app.core.logger import logger
from app.schemas.material import SourceFragment
from app.schemas.quiz import DifficultyLevel, GenerateQuizResponse
from app.services.gigachat_service import gigachat_service
from app.services.material_service import material_service
from app.services.prompt_service import build_quiz_prompt, build_regenerate_question_prompt


class QuizService:
    def _extract_json(self, raw_text: str) -> dict:
        raw_text = raw_text.strip()

        for start_tag, end_tag in (
            ("[JSON_START]", "[JSON_END]"),
            ("JSON_START", "JSON_END"),
        ):
            start = raw_text.find(start_tag)
            end = raw_text.find(end_tag)
            if start != -1 and end != -1 and end > start:
                raw_text = raw_text[start + len(start_tag) : end].strip()
                break
            if start != -1:
                raw_text = raw_text[start + len(start_tag) :].strip()
                break

        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        last_brace = raw_text.rfind("}")
        if last_brace > 0:
            raw_text = raw_text[: last_brace + 1]

        open_braces = raw_text.count("{")
        close_braces = raw_text.count("}")
        open_brackets = raw_text.count("[")
        close_brackets = raw_text.count("]")

        raw_text += "}" * (open_braces - close_braces)
        raw_text += "]" * (open_brackets - close_brackets)
        raw_text = re.sub(r"(?<!\\)\\([a-zA-Z]+)", r"\\\\\1", raw_text)
        raw_text = raw_text.replace("\n", " ").replace("\r", "").strip()

        if not raw_text:
            raise ValueError("Пустой JSON после обработки")

        return json.loads(raw_text)

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

    def _normalize_question_dict(self, question: dict, fallback_difficulty: str) -> dict:
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

        return normalized

    def _normalize_quiz_response_data(self, data: dict, fallback_difficulty: str) -> dict:
        normalized = dict(data)
        questions = normalized.get("questions", [])
        normalized["questions"] = [
            self._normalize_question_dict(question, fallback_difficulty)
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

        prompt = build_quiz_prompt(
            subject=subject,
            grade=grade,
            topic=topic,
            question_count=question_count,
            question_types=question_types,
            difficulty=difficulty,
            combined_context=combined_context,
            fragments=fragments,
        )

        raw = gigachat_service.chat(
            messages=[
                {"role": "system", "content": "Ты возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )

        logger.info("RAW_MODEL_RESPONSE: %s", raw[:2000])

        try:
            data = self._extract_json(raw)
            data = self._normalize_quiz_response_data(data, difficulty)
            result = GenerateQuizResponse(**data)
            return self._apply_difficulty_to_all_questions(result, difficulty)
        except Exception as exc:
            logger.error("JSON_PARSE_ERROR: %s", exc)
            logger.error("BROKEN_RAW_RESPONSE: %s", raw[:2000])
            raise

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
        prompt = build_regenerate_question_prompt(
            subject=subject,
            grade=grade,
            topic=topic,
            difficulty=difficulty,
            question_type=question_type,
            current_question_text=current_question_text,
            source_fragment_id=source_fragment_id,
        )

        raw = gigachat_service.chat(
            messages=[
                {"role": "system", "content": "Ты возвращаешь только валидный JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        data = self._extract_json(raw)
        if isinstance(data, dict) and "questions" in data and data["questions"]:
            data = data["questions"][0]
        if not isinstance(data, dict):
            raise ValueError("Модель вернула некорректный формат вопроса")

        return self._normalize_question_dict(data, difficulty)


quiz_service = QuizService()
