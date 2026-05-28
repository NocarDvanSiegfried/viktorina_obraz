import { Link } from "react-router-dom"

import { Button } from "@/components/ui/Button"
import { pluralizeErrors } from "@/lib/quizResultsAnalytics"
import type { HardestQuestionRow } from "@/lib/quizResultsAnalytics"

type ResultsNextStepsProps = {
  quizId: string
  hardest: HardestQuestionRow[]
  studentsWithErrors: number
  onDownloadPdf: () => void
}

export function ResultsNextSteps({
  quizId,
  hardest,
  studentsWithErrors,
  onDownloadPdf,
}: ResultsNextStepsProps) {
  const topQuestion = hardest[0]

  return (
    <section className="results-next-steps" aria-labelledby="results-next-heading">
      <h2 id="results-next-heading">Что сделать дальше</h2>
      <div className="results-next-grid">
        {topQuestion && studentsWithErrors > 0 && (
          <article className="results-next-card">
            <h3>Повторить тему</h3>
            <p className="subtitle">
              {studentsWithErrors} ученик(ов) ошиблись в похожих вопросах. Повторите
              тему на следующем уроке.
            </p>
          </article>
        )}

        {topQuestion?.question_id && (
          <article className="results-next-card">
            <h3>Перегенерировать вопрос</h3>
            <p className="subtitle">
              Самый сложный: «{topQuestion.question_text}» ({pluralizeErrors(topQuestion.wrong_count)}).
            </p>
            <Button as="link" to={`/edit/${quizId}?tab=questions`} variant="secondary">
              Открыть вопросы
            </Button>
          </article>
        )}

        <article className="results-next-card">
          <h3>Сохранить отчёт</h3>
          <p className="subtitle">Скачайте PDF викторины для журнала или архива.</p>
          <div className="results-next-actions">
            <Button type="button" variant="secondary" onClick={onDownloadPdf}>
              Скачать PDF
            </Button>
            <button type="button" className="btn btn-ghost" onClick={() => window.print()}>
              Печать страницы
            </button>
          </div>
        </article>

        <article className="results-next-card">
          <h3>Поделиться с классом</h3>
          <p className="subtitle">Если прохождений мало — откройте быстрый просмотр и скопируйте ссылку.</p>
          <Link to={`/edit/${quizId}?tab=preview`} className="btn btn-ghost">
            Открыть быстрый просмотр
          </Link>
        </article>
      </div>
    </section>
  )
}
