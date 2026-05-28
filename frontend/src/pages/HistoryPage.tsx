import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { listQuizzes, type QuizListItem } from "@/lib/api"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { getOrCreateOwnerId } from "@/lib/owner"
import { formatUpdatedAt } from "@/lib/quizLabels"

export default function HistoryPage() {
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])
  const [items, setItems] = useState<QuizListItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError("")
      try {
        const data = await listQuizzes(ownerId)
        if (!cancelled) {
          setItems(data.quizzes)
        }
      } catch (err) {
        if (!cancelled) {
          setError(mapErrorMessage(err, "Не удалось загрузить историю"))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [ownerId])

  return (
    <div className="page">
      <div className="card">
        <PageHeader
          title="История викторин"
          subtitle="Откройте историю изменений по нужной викторине."
          backTo="/"
          backLabel="← Мои викторины"
        />

        {isLoading && <PageLoadingSkeleton variant="list" />}
        <ErrorAlert message={error} />

        {!isLoading && !error && items.length === 0 && (
          <section className="quiz-list-empty">
            <h2 className="quiz-list-empty-title">История пока пуста</h2>
            <p className="subtitle">
              Сначала создайте викторину, затем измените вопросы или настройки.
            </p>
          </section>
        )}

        {items.length > 0 && (
          <ul className="history-list">
            {items.map((quiz) => (
              <li key={quiz.id} className="history-list-item">
                <div className="history-list-main">
                  <h2>{quiz.title}</h2>
                  <p className="subtitle">
                    Последнее изменение: {formatUpdatedAt(quiz.updated_at ?? quiz.created_at) || "—"}
                  </p>
                </div>
                <Link to={`/edit/${quiz.id}?tab=history`} className="btn btn-secondary">
                  Открыть историю изменений
                </Link>
              </li>
            ))}
          </ul>
        )}

        <DebugPanel ownerId={ownerId} />
      </div>
    </div>
  )
}
