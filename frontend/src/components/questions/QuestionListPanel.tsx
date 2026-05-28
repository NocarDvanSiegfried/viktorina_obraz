import { useEffect, useState } from "react"

import { QuestionEditor } from "@/components/QuestionEditor"
import {
  QUESTION_TYPE_LABELS,
  type QuestionType,
} from "@/components/create/createConstants"
import type { QuizDetailResponse, QuizQuestionDetail } from "@/lib/api"
import type { SourceFragmentCatalogItem } from "@/lib/sourceFragment"

function truncate(text: string, max = 56): string {
  const trimmed = text.trim()
  if (trimmed.length <= max) return trimmed || "Без текста"
  return `${trimmed.slice(0, max)}…`
}

function typeLabel(type: string): string {
  if (type in QUESTION_TYPE_LABELS) {
    return QUESTION_TYPE_LABELS[type as QuestionType]
  }
  return type
}

type QuestionListPanelProps = {
  quizId: string
  ownerId: string
  questions: QuizQuestionDetail[]
  fragmentCatalog?: SourceFragmentCatalogItem[]
  onQuizUpdated: (quiz: QuizDetailResponse) => void
  onError: (message: string) => void
}

export function QuestionListPanel({
  quizId,
  ownerId,
  questions,
  fragmentCatalog,
  onQuizUpdated,
  onError,
}: QuestionListPanelProps) {
  const [selectedId, setSelectedId] = useState<string | null>(
    questions[0]?.id ?? null
  )

  useEffect(() => {
    if (questions.length === 0) {
      setSelectedId(null)
      return
    }
    if (!selectedId || !questions.some((q) => q.id === selectedId)) {
      setSelectedId(questions[0].id)
    }
  }, [questions, selectedId])

  const selected =
    questions.find((q) => q.id === selectedId) ?? questions[0] ?? null
  const selectedIndex = selected
    ? questions.findIndex((q) => q.id === selected.id)
    : -1

  if (questions.length === 0) {
    return (
      <p className="subtitle">Вопросов пока нет — добавьте первый ниже.</p>
    )
  }

  return (
    <div className="question-list-panel">
      <nav className="question-list-sidebar" aria-label="Список вопросов">
        <ol className="question-list-items">
          {questions.map((question, index) => {
            const isActive = selected?.id === question.id
            return (
              <li key={question.id}>
                <button
                  type="button"
                  className={
                    isActive
                      ? "question-list-item question-list-item-active"
                      : "question-list-item"
                  }
                  aria-current={isActive ? "true" : undefined}
                  onClick={() => setSelectedId(question.id)}
                >
                  <span className="question-list-item-num">{index + 1}</span>
                  <span className="question-list-item-text">
                    {truncate(question.question_text)}
                  </span>
                  <span className="question-list-item-type">
                    {typeLabel(question.question_type)}
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
      </nav>

      <div className="question-list-editor">
        {selected && selectedIndex >= 0 && (
          <QuestionEditor
            quizId={quizId}
            ownerId={ownerId}
            question={selected}
            index={selectedIndex}
            total={questions.length}
            fragmentCatalog={fragmentCatalog}
            onQuizUpdated={onQuizUpdated}
            onError={onError}
            onSelectQuestion={setSelectedId}
          />
        )}
      </div>
    </div>
  )
}
