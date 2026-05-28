import { pluralizeErrors } from "@/lib/quizResultsAnalytics"
import type { HardestQuestionRow } from "@/lib/quizResultsAnalytics"

type HardestQuestionsBlockProps = {
  questions: HardestQuestionRow[]
}

export function HardestQuestionsBlock({ questions }: HardestQuestionsBlockProps) {
  if (questions.length === 0) {
    return (
      <section className="results-hardest results-hardest-empty">
        <h2>Самые сложные вопросы</h2>
        <p className="subtitle">Все ответили без ошибок — отличный результат.</p>
      </section>
    )
  }

  return (
    <section className="results-hardest" aria-labelledby="results-hardest-heading">
      <h2 id="results-hardest-heading">Самые сложные вопросы</h2>
      <ol className="results-hardest-list">
        {questions.map((row, index) => (
          <li key={row.question_id || row.question_text}>
            <span className="results-hardest-rank">{index + 1}.</span>
            <span className="results-hardest-text">«{row.question_text}»</span>
            <span className="results-hardest-count">— {pluralizeErrors(row.wrong_count)}</span>
          </li>
        ))}
      </ol>
    </section>
  )
}
