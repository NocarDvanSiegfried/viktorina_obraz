import { useEffect, useState } from "react"

import {
  createQuestion,
  deleteQuestion,
  regenerateQuestion,
  reorderQuestion,
  updateQuestion,
  type QuestionPayload,
  type QuestionType,
  type QuizDetailResponse,
  type QuizQuestionDetail,
} from "@/lib/api"
import { SourceFragmentBadge } from "@/components/SourceFragmentBadge"
import type { SourceFragmentCatalogItem } from "@/lib/sourceFragment"

const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  single_choice: "Один ответ",
  multiple_choice: "Несколько ответов",
  true_false: "Верно / Неверно",
}

const TRUE_FALSE_OPTIONS = ["Верно", "Неверно"]

function defaultAnswersForType(type: QuestionType): string[] {
  if (type === "true_false") {
    return [...TRUE_FALSE_OPTIONS]
  }
  return ["", ""]
}

function toPayload(
  questionText: string,
  questionType: QuestionType,
  answers: string[],
  correctAnswers: string[],
  explanation: string,
  sourceFragment: string
): QuestionPayload {
  return {
    question_text: questionText.trim(),
    question_type: questionType,
    answers: answers.map((a) => a.trim()).filter(Boolean),
    correct_answers: correctAnswers,
    explanation: explanation.trim() || undefined,
    source_fragment: sourceFragment.trim() || undefined,
  }
}

type QuestionEditorProps = {
  quizId: string
  ownerId: string
  question: QuizQuestionDetail
  index: number
  total: number
  fragmentCatalog?: SourceFragmentCatalogItem[]
  onQuizUpdated: (quiz: QuizDetailResponse) => void
  onError: (message: string) => void
  onSelectQuestion?: (questionId: string) => void
}

export function QuestionEditor({
  quizId,
  ownerId,
  question,
  index,
  total,
  fragmentCatalog,
  onQuizUpdated,
  onError,
  onSelectQuestion,
}: QuestionEditorProps) {
  const [questionText, setQuestionText] = useState(question.question_text)
  const [questionType, setQuestionType] = useState<QuestionType>(
    question.question_type as QuestionType
  )
  const [answers, setAnswers] = useState<string[]>([...question.answers])
  const [correctAnswers, setCorrectAnswers] = useState<string[]>([
    ...question.correct_answers,
  ])
  const [explanation, setExplanation] = useState(question.explanation ?? "")
  const [sourceFragment, setSourceFragment] = useState(
    question.source_fragment ?? ""
  )
  const [isBusy, setIsBusy] = useState(false)

  useEffect(() => {
    setQuestionText(question.question_text)
    setQuestionType(question.question_type as QuestionType)
    setAnswers([...question.answers])
    setCorrectAnswers([...question.correct_answers])
    setExplanation(question.explanation ?? "")
    setSourceFragment(question.source_fragment ?? "")
  }, [question])

  const onTypeChange = (nextType: QuestionType) => {
    setQuestionType(nextType)
    if (nextType === "true_false") {
      setAnswers([...TRUE_FALSE_OPTIONS])
      setCorrectAnswers(
        correctAnswers.filter((c) => TRUE_FALSE_OPTIONS.includes(c)).slice(0, 1)
      )
      return
    }
    if (answers.length < 2 || answers.join("") === TRUE_FALSE_OPTIONS.join("")) {
      setAnswers(["", ""])
    }
    if (nextType === "single_choice" && correctAnswers.length > 1) {
      setCorrectAnswers(correctAnswers.slice(0, 1))
    }
  }

  const toggleCorrect = (option: string) => {
    if (questionType === "multiple_choice") {
      setCorrectAnswers((prev) =>
        prev.includes(option)
          ? prev.filter((item) => item !== option)
          : [...prev, option]
      )
      return
    }
    setCorrectAnswers([option])
  }

  const runAction = async (action: () => Promise<QuizDetailResponse>) => {
    setIsBusy(true)
    onError("")
    try {
      const updated = await action()
      onQuizUpdated(updated)
    } catch (err) {
      onError(err instanceof Error ? err.message : "Ошибка операции")
    } finally {
      setIsBusy(false)
    }
  }

  const handleSave = () => {
    void runAction(() =>
      updateQuestion(
        quizId,
        question.id,
        ownerId,
        toPayload(
          questionText,
          questionType,
          answers,
          correctAnswers,
          explanation,
          sourceFragment
        )
      )
    )
  }

  const handleDelete = () => {
    if (!window.confirm("Удалить этот вопрос?")) {
      return
    }
    void runAction(() => deleteQuestion(quizId, question.id, ownerId))
  }

  const handleMove = (direction: "up" | "down") => {
    void runAction(async () => {
      const updated = await reorderQuestion(
        quizId,
        question.id,
        ownerId,
        direction
      )
      const neighborIndex = direction === "up" ? index - 1 : index + 1
      const neighbor = updated.questions[neighborIndex]
      if (neighbor && onSelectQuestion) {
        onSelectQuestion(neighbor.id)
      }
      return updated
    })
  }

  const handleRegenerate = () => {
    if (
      !window.confirm(
        "Пересоздать вопрос через GigaChat? Текущий текст и варианты будут заменены."
      )
    ) {
      return
    }
    void runAction(() => regenerateQuestion(quizId, question.id, ownerId))
  }

  return (
    <section className="question-item question-edit-card">
      <div className="question-edit-header">
        <strong>
          Вопрос {index + 1} из {total}
        </strong>
        {sourceFragment.trim() && (
          <SourceFragmentBadge
            fragmentId={sourceFragment}
            catalog={fragmentCatalog}
          />
        )}
        <div className="link-row question-edit-order">
          <button
            type="button"
            title="Выше"
            disabled={isBusy || index === 0}
            onClick={() => handleMove("up")}
          >
            ↑
          </button>
          <button
            type="button"
            title="Ниже"
            disabled={isBusy || index >= total - 1}
            onClick={() => handleMove("down")}
          >
            ↓
          </button>
        </div>
      </div>

      <div className="form-grid">
        <label>
          Текст вопроса
          <textarea
            rows={3}
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
          />
        </label>

        <label>
          Тип
          <select
            value={questionType}
            onChange={(e) => onTypeChange(e.target.value as QuestionType)}
          >
            {(Object.keys(QUESTION_TYPE_LABELS) as QuestionType[]).map(
              (type) => (
                <option key={type} value={type}>
                  {QUESTION_TYPE_LABELS[type]}
                </option>
              )
            )}
          </select>
        </label>

        <div>
          <span className="field-label">Варианты ответов</span>
          {answers.map((option, optionIndex) => (
            <div key={`${question.id}-opt-${optionIndex}`} className="option-row">
              <input
                value={option}
                disabled={questionType === "true_false"}
                onChange={(e) => {
                  const next = [...answers]
                  const prev = next[optionIndex]
                  next[optionIndex] = e.target.value
                  setAnswers(next)
                  setCorrectAnswers((prevCorrect) =>
                    prevCorrect.map((c) => (c === prev ? e.target.value : c))
                  )
                }}
              />
              <label>
                <input
                  type={questionType === "multiple_choice" ? "checkbox" : "radio"}
                  name={`correct-${question.id}`}
                  checked={correctAnswers.includes(option)}
                  onChange={() => toggleCorrect(option)}
                />
                Верный
              </label>
              {questionType !== "true_false" && answers.length > 2 && (
                <button
                  type="button"
                  onClick={() => {
                    const next = answers.filter((_, i) => i !== optionIndex)
                    setAnswers(next)
                    setCorrectAnswers((prevCorrect) =>
                      prevCorrect.filter((c) => c !== option)
                    )
                  }}
                >
                  ×
                </button>
              )}
            </div>
          ))}
          {questionType !== "true_false" && (
            <button
              type="button"
              onClick={() => setAnswers((prev) => [...prev, ""])}
            >
              + вариант
            </button>
          )}
        </div>

        <details className="question-edit-advanced">
          <summary>Пояснение (необязательно)</summary>
          <label>
            Текст пояснения
            <textarea
              rows={2}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
            />
          </label>
        </details>

        <div className="link-row question-edit-actions">
          <button
            type="button"
            className="btn btn-primary"
            disabled={isBusy}
            onClick={handleSave}
          >
            {isBusy ? "Сохранение..." : "Сохранить"}
          </button>
          <button type="button" disabled={isBusy} onClick={handleRegenerate}>
            {isBusy ? "ИИ..." : "Другой вариант (ИИ)"}
          </button>
          <button
            type="button"
            disabled={isBusy || total <= 1}
            onClick={handleDelete}
          >
            Удалить
          </button>
        </div>
      </div>
    </section>
  )
}

type NewQuestionFormProps = {
  quizId: string
  ownerId: string
  disabled: boolean
  onQuizUpdated: (quiz: QuizDetailResponse) => void
  onError: (message: string) => void
}

export function NewQuestionForm({
  quizId,
  ownerId,
  disabled,
  onQuizUpdated,
  onError,
}: NewQuestionFormProps) {
  const [questionText, setQuestionText] = useState("")
  const [questionType, setQuestionType] = useState<QuestionType>("single_choice")
  const [answers, setAnswers] = useState<string[]>(["", ""])
  const [correctAnswers, setCorrectAnswers] = useState<string[]>([])
  const [explanation, setExplanation] = useState("")
  const [isBusy, setIsBusy] = useState(false)

  const onTypeChange = (nextType: QuestionType) => {
    setQuestionType(nextType)
    setAnswers(defaultAnswersForType(nextType))
    setCorrectAnswers([])
  }

  const toggleCorrect = (option: string) => {
    if (questionType === "multiple_choice") {
      setCorrectAnswers((prev) =>
        prev.includes(option)
          ? prev.filter((item) => item !== option)
          : [...prev, option]
      )
      return
    }
    setCorrectAnswers([option])
  }

  const handleCreate = () => {
    setIsBusy(true)
    onError("")
    void createQuestion(
      quizId,
      ownerId,
      toPayload(questionText, questionType, answers, correctAnswers, explanation, "")
    )
      .then((updated) => {
        onQuizUpdated(updated)
        setQuestionText("")
        setQuestionType("single_choice")
        setAnswers(["", ""])
        setCorrectAnswers([])
        setExplanation("")
      })
      .catch((err) => {
        onError(err instanceof Error ? err.message : "Не удалось добавить вопрос")
      })
      .finally(() => setIsBusy(false))
  }

  return (
    <details className="question-edit-card question-add-details">
      <summary>Добавить вопрос вручную</summary>
      <div className="form-grid">
        <label>
          Текст вопроса
          <textarea
            rows={2}
            value={questionText}
            onChange={(e) => setQuestionText(e.target.value)}
          />
        </label>
        <label>
          Тип
          <select
            value={questionType}
            onChange={(e) => onTypeChange(e.target.value as QuestionType)}
          >
            {(Object.keys(QUESTION_TYPE_LABELS) as QuestionType[]).map((type) => (
              <option key={type} value={type}>
                {QUESTION_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>
        <div>
          <span className="field-label">Варианты</span>
          {answers.map((option, optionIndex) => (
            <div key={`new-opt-${optionIndex}`} className="option-row">
              <input
                value={option}
                disabled={questionType === "true_false"}
                onChange={(e) => {
                  const next = [...answers]
                  next[optionIndex] = e.target.value
                  setAnswers(next)
                }}
              />
              <label>
                <input
                  type={questionType === "multiple_choice" ? "checkbox" : "radio"}
                  name="new-correct"
                  checked={correctAnswers.includes(option)}
                  onChange={() => toggleCorrect(option)}
                />
                Верный
              </label>
            </div>
          ))}
          {questionType !== "true_false" && (
            <button type="button" onClick={() => setAnswers((prev) => [...prev, ""])}>
              + вариант
            </button>
          )}
        </div>
        <button
          type="button"
          className="btn btn-primary"
          disabled={disabled || isBusy || !questionText.trim()}
          onClick={handleCreate}
        >
          {isBusy ? "Добавление..." : "Добавить"}
        </button>
      </div>
    </details>
  )
}
