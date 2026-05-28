import { Link } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import type { QuizHubTabId } from "@/components/quiz/QuizHubLayout"

type QuizProgressChecklistProps = {
  quizId: string
  questionsReady: boolean
  settingsSaved: boolean
  shareCopied: boolean
  resultsCount: number
  onCopyStudentLink: () => void
  onMarkSettingsOk: () => void
}

type StepConfig = {
  id: string
  title: string
  done: boolean
  tab: QuizHubTabId
  ctaPending: string
  ctaDone: string
  hint?: string
  disabled?: boolean
  externalResults?: boolean
}

export function QuizProgressChecklist({
  quizId,
  questionsReady,
  settingsSaved,
  shareCopied,
  resultsCount,
  onCopyStudentLink,
  onMarkSettingsOk,
}: QuizProgressChecklistProps) {
  const hasResults = resultsCount > 0

  const steps: StepConfig[] = [
    {
      id: "questions",
      title: "Вопросы готовы",
      done: questionsReady,
      tab: "questions",
      ctaPending: "Проверить вопросы",
      ctaDone: "Открыть вопросы",
    },
    {
      id: "settings",
      title: "Настройки проверены",
      done: settingsSaved,
      tab: "settings",
      ctaPending: "Проверить настройки",
      ctaDone: "Настройки проверены",
    },
    {
      id: "share",
      title: "Ссылка создана",
      done: shareCopied,
      tab: "preview",
      ctaPending: "Скопировать ссылку ученику",
      ctaDone: "Скопировать снова",
      hint: shareCopied ? "Ссылка уже скопирована — можно отправлять в чат класса." : undefined,
    },
    {
      id: "results",
      title: "Результаты",
      done: hasResults,
      tab: "results",
      ctaPending: "Результаты появятся после прохождения",
      ctaDone: hasResults ? `Смотреть результаты (${resultsCount})` : "Смотреть результаты",
      disabled: !hasResults,
      externalResults: hasResults,
    },
  ]

  return (
    <section className="quiz-progress-checklist" aria-label="Прогресс викторины">
      <h2>Прогресс викторины</h2>
      <p className="subtitle">
        Проверьте качество, настройте правила и отправьте ссылку ученикам.
      </p>

      <ol className="quiz-progress-steps">
        {steps.map((step, index) => (
          <li key={step.id} className="quiz-progress-step">
            <div className="quiz-progress-step-main">
              <span className="quiz-progress-step-index" aria-hidden="true">
                {index + 1}.
              </span>
              <span className="quiz-progress-step-title">{step.title}</span>
              <span
                className={
                  step.done ? "quiz-progress-step-status done" : "quiz-progress-step-status"
                }
                aria-label={step.done ? "Готово" : "Не готово"}
              >
                {step.done ? "✅" : "○"}
              </span>
            </div>

            {step.hint && <p className="quiz-progress-hint">{step.hint}</p>}

            <div className="quiz-progress-step-actions">
              {step.id === "share" && !step.done && (
                <Button type="button" onClick={onCopyStudentLink}>
                  {step.ctaPending}
                </Button>
              )}

              {step.id === "share" && step.done && (
                <>
                  <span className="quiz-progress-done-label">Ссылка готова</span>
                  <Button type="button" variant="secondary" onClick={onCopyStudentLink}>
                    {step.ctaDone}
                  </Button>
                </>
              )}

              {step.id === "settings" && step.done && (
                <>
                  <span className="quiz-progress-done-label">{step.ctaDone}</span>
                  <Link
                    to={`/edit/${quizId}?tab=settings`}
                    className="quiz-progress-link"
                  >
                    Открыть настройки
                  </Link>
                </>
              )}

              {step.id === "settings" && !step.done && (
                <>
                  <Link
                    to={`/edit/${quizId}?tab=settings`}
                    className="btn btn-primary quiz-progress-link-btn"
                  >
                    {step.ctaPending}
                  </Link>
                  <Button type="button" variant="ghost" onClick={onMarkSettingsOk}>
                    Оставить как есть
                  </Button>
                </>
              )}

              {step.id === "questions" && (
                <Link
                  to={`/edit/${quizId}?tab=questions`}
                  className="btn btn-primary quiz-progress-link-btn"
                >
                  {step.done ? step.ctaDone : step.ctaPending}
                </Link>
              )}

              {step.id === "results" && step.disabled && (
                <span className="quiz-progress-disabled">{step.ctaPending}</span>
              )}

              {step.id === "results" && !step.disabled && step.externalResults && (
                <Link
                  to={`/results/${quizId}`}
                  className="btn btn-primary quiz-progress-link-btn"
                >
                  {step.ctaDone}
                </Link>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  )
}
