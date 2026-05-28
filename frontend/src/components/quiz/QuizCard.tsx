import { useState } from "react"
import { Link } from "react-router-dom"

import { Badge } from "@/components/ui/Badge"
import type { QuizListItem } from "@/lib/api"
import {
  formatDifficultyLabel,
  formatGradeLabel,
  formatStatusLabel,
  formatUpdatedAt,
} from "@/lib/quizLabels"

type QuizCardProps = {
  quiz: QuizListItem
  onDuplicate?: (quizId: string) => Promise<void>
  onArchive?: (quizId: string, title: string) => Promise<void>
}

export function QuizCard({ quiz, onDuplicate, onArchive }: QuizCardProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const updatedLabel = formatUpdatedAt(quiz.updated_at ?? quiz.created_at)
  const subjectLine = [quiz.subject, formatGradeLabel(quiz.grade)]
    .filter((part) => part && part !== "—")
    .join(" · ")

  const primaryAction =
    quiz.status === "published"
      ? { to: `/results/${quiz.id}`, label: "Смотреть результаты" }
      : { to: `/edit/${quiz.id}`, label: "Продолжить редактирование" }

  return (
    <article className="quiz-card">
      <Link to={`/results/${quiz.id}`} className="quiz-card-hitarea">
        <div className="quiz-card-header">
          <h2 className="quiz-card-title">{quiz.title}</h2>
          <span className="quiz-card-cta">Посмотреть результаты →</span>
        </div>

        <div className="quiz-card-badges">
          {quiz.difficulty && (
            <Badge variant="difficulty">{formatDifficultyLabel(quiz.difficulty)}</Badge>
          )}
          <Badge variant="status">{formatStatusLabel(quiz.status)}</Badge>
          <Badge variant="neutral">
            {quiz.questions_count}{" "}
            {quiz.questions_count === 1 ? "вопрос" : "вопросов"}
          </Badge>
        </div>

        <p className="quiz-card-meta">
          {subjectLine || "Без предмета"}
          {updatedLabel && ` · Обновлено: ${updatedLabel}`}
        </p>
      </Link>

      <div className="quiz-card-actions">
        <Link
          to={primaryAction.to}
          className="quiz-card-action quiz-card-action-primary"
          onClick={(event) => event.stopPropagation()}
        >
          {primaryAction.label}
        </Link>
        <Link
          to={`/edit/${quiz.id}`}
          className="quiz-card-action"
          onClick={(event) => event.stopPropagation()}
        >
          Редактировать
        </Link>
        <Link
          to={`/student/${quiz.id}`}
          className="quiz-card-action"
          onClick={(event) => event.stopPropagation()}
        >
          Ссылка для ученика
        </Link>
        <div className="quiz-card-menu">
          <button
            type="button"
            className="quiz-card-action"
            aria-expanded={isMenuOpen}
            onClick={() => setIsMenuOpen((v) => !v)}
          >
            Действия
          </button>
          {isMenuOpen && (
            <div className="quiz-card-menu-popover">
              <Link
                to={`/edit/${quiz.id}?tab=history`}
                className="quiz-card-menu-item"
                onClick={() => setIsMenuOpen(false)}
              >
                История изменений
              </Link>
              <button
                type="button"
                className="quiz-card-menu-item"
                onClick={async () => {
                  if (!onDuplicate) return
                  await onDuplicate(quiz.id)
                  setIsMenuOpen(false)
                }}
              >
                Дублировать
              </button>
              <button
                type="button"
                className="quiz-card-menu-item quiz-card-menu-item-danger"
                onClick={async () => {
                  if (!onArchive) return
                  await onArchive(quiz.id, quiz.title)
                  setIsMenuOpen(false)
                }}
              >
                Архивировать
              </button>
            </div>
          )}
        </div>
      </div>
    </article>
  )
}
