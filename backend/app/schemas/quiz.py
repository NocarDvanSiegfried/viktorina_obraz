from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


QuestionType = Literal["single_choice", "multiple_choice", "true_false"]


class DifficultyLevel(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuizQuestion(BaseModel):
    type: QuestionType
    text: str
    options: List[str]
    correct_answers: List[str]
    explanation: str
    difficulty: DifficultyLevel
    source_fragment_id: Optional[str] = None


class GenerateQuizResponse(BaseModel):
    quiz_title: str
    subject: str
    grade: str
    topic: str
    questions: List[QuizQuestion]
