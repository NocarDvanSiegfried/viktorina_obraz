import {
  averagePercent,
  totalAttemptsCount,
  uniqueStudentCount,
} from "@/lib/quizResultsAnalytics"
import type { QuizResultItemDTO } from "@/lib/api"

type ResultsSummaryProps = {
  results: QuizResultItemDTO[]
}

export function ResultsSummary({ results }: ResultsSummaryProps) {
  if (results.length === 0) {
    return null
  }

  return (
    <section className="results-summary" aria-labelledby="results-summary-heading">
      <h2 id="results-summary-heading">Сводка класса</h2>
      <div className="results-kpi-grid">
        <article className="results-kpi-card">
          <p className="results-kpi-label">Средний результат</p>
          <p className="results-kpi-value">{averagePercent(results)}%</p>
        </article>
        <article className="results-kpi-card">
          <p className="results-kpi-label">Учеников прошли</p>
          <p className="results-kpi-value">{uniqueStudentCount(results)}</p>
        </article>
        <article className="results-kpi-card">
          <p className="results-kpi-label">Всего прохождений</p>
          <p className="results-kpi-value">{totalAttemptsCount(results)}</p>
        </article>
      </div>
    </section>
  )
}
