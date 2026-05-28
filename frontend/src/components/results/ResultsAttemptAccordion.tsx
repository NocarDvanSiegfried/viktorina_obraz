import { useState } from "react"

import {
  formatAttemptSummary,
  pluralizeErrors,
} from "@/lib/quizResultsAnalytics"
import type { QuizResultItemDTO } from "@/lib/api"

type ResultsAttemptAccordionProps = {
  attempts: QuizResultItemDTO[]
}

export function ResultsAttemptAccordion({ attempts }: ResultsAttemptAccordionProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  if (attempts.length === 0) {
    return (
      <p className="subtitle results-attempts-empty">
        Нет прохождений с ошибками. Попробуйте фильтр «Все прохождения».
      </p>
    )
  }

  return (
    <div className="results-attempt-list">
      {attempts.map((attempt) => {
        const expanded = openId === attempt.result_id
        const hasErrors = attempt.wrong_questions.length > 0
        return (
          <details
            key={attempt.result_id}
            className="results-attempt-card"
            open={expanded}
            onToggle={(event) => {
              const target = event.currentTarget
              setOpenId(target.open ? attempt.result_id : null)
            }}
          >
            <summary className="results-attempt-summary">
              {formatAttemptSummary(attempt)}
            </summary>
            {hasErrors ? (
              <ul className="results-attempt-errors">
                {attempt.wrong_questions.map((wrong) => (
                  <li key={`${attempt.result_id}-${wrong.question_id}`}>
                    <p className="results-wrong-question">{wrong.question_text}</p>
                    <p className="results-wrong-answer">
                      Ответ: {wrong.selected_options.join(", ") || "—"}
                    </p>
                    <p className="results-wrong-correct">
                      Правильно: {wrong.correct_answers.join(", ") || "—"}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="subtitle results-attempt-no-errors">
                Без ошибок ({pluralizeErrors(0)}).
              </p>
            )}
          </details>
        )
      })}
    </div>
  )
}
