from pydantic import BaseModel, Field


class StudentStartResponse(BaseModel):
    result_id: str
    quiz_id: str
    student_name: str
    attempt_number: int
    full_time_seconds: int | None
    question_time_seconds: int | None
    max_attempts: int
    questions_count: int
    started_at: str


class StudentQuestion(BaseModel):
    id: str
    question_text: str
    question_type: str
    options: list[str]


class StudentQuestionsResponse(BaseModel):
    result_id: str
    quiz_id: str
    student_name: str
    attempt_number: int
    full_time_seconds: int | None
    question_time_seconds: int | None
    max_attempts: int
    questions_count: int
    started_at: str
    completed: bool
    next_question: StudentQuestion | None = None
    answered_questions: list[str] = Field(default_factory=list)


class StudentAnswerResponse(BaseModel):
    result_id: str
    question_id: str
    received: bool


class StudentFinishResponse(BaseModel):
    result_id: str
    score: int
    max_score: int
    percent: int
    duration_seconds: int

