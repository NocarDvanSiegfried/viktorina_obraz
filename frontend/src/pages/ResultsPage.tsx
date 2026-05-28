import { useEffect, useMemo, useRef, useState } from "react"
import { useParams } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { useToast } from "@/components/feedback/ToastProvider"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { HardestQuestionsBlock } from "@/components/results/HardestQuestionsBlock"
import { ResultsAttemptAccordion } from "@/components/results/ResultsAttemptAccordion"
import { ResultsNextSteps } from "@/components/results/ResultsNextSteps"
import { ResultsSummary } from "@/components/results/ResultsSummary"
import { Button } from "@/components/ui/Button"
import {
  downloadQuizPdf,
  getQuizResults,
  type QuizResultsResponse,
} from "@/lib/api"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { getOrCreateOwnerId } from "@/lib/owner"
import {
  attemptsWithErrors,
  studentsWithErrorsCount,
  topHardestQuestions,
} from "@/lib/quizResultsAnalytics"

type ResultsFilter = "all" | "errors"

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])
  const toast = useToast()
  const attemptsRef = useRef<HTMLDivElement>(null)

  const [data, setData] = useState<QuizResultsResponse | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<ResultsFilter>("all")
  const [pdfError, setPdfError] = useState("")

  useEffect(() => {
    if (!id) {
      setError("Не указан идентификатор викторины.")
      setIsLoading(false)
      return
    }

    let cancelled = false

    const load = async () => {
      setIsLoading(true)
      setError("")
      try {
        const res = await getQuizResults(id, ownerId)
        if (!cancelled) setData(res)
      } catch (err) {
        if (!cancelled) {
          setError(mapErrorMessage(err, "Не удалось загрузить результаты"))
        }
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [id, ownerId])

  const hardest = useMemo(
    () => (data ? topHardestQuestions(data.results) : []),
    [data]
  )

  const filteredAttempts = useMemo(() => {
    if (!data) return []
    return filter === "errors" ? attemptsWithErrors(data.results) : data.results
  }, [data, filter])

  const showErrorsOnly = () => {
    setFilter("errors")
    attemptsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
  }

  const handleDownloadPdf = async () => {
    if (!id) return
    setPdfError("")
    try {
      await downloadQuizPdf(id, ownerId)
    } catch (err) {
      const message = mapErrorMessage(err, "Не удалось скачать PDF")
      setPdfError(message)
      toast.showError(message)
    }
  }

  const pageTitle = data?.title ? `Результаты: ${data.title}` : "Результаты"

  return (
    <div className="page results-page">
      <div className="card">
        <PageHeader
          title={pageTitle}
          subtitle="Аналитика прохождений и типичные ошибки класса."
          backTo={id ? `/edit/${id}` : "/"}
          backLabel="← К викторине"
        />

        {isLoading && <PageLoadingSkeleton variant="results" />}
        <ErrorAlert message={error} />
        <ErrorAlert message={pdfError} />

        {data && data.results.length === 0 && (
          <section className="results-empty">
            <p className="subtitle">
              Пока никто не прошёл викторину. Отправьте ссылку ученикам.
            </p>
            {id && (
              <Button as="link" to={`/edit/${id}?tab=preview`}>
                Открыть быстрый просмотр
              </Button>
            )}
          </section>
        )}

        {data && data.results.length > 0 && (
          <>
            <div className="results-toolbar">
              <Button type="button" onClick={showErrorsOnly}>
                Посмотреть ошибки
              </Button>
              <div
                className="results-filter"
                role="group"
                aria-label="Фильтр прохождений"
              >
                <button
                  type="button"
                  className={
                    filter === "all"
                      ? "results-filter-btn results-filter-btn-active"
                      : "results-filter-btn"
                  }
                  onClick={() => setFilter("all")}
                >
                  Все прохождения
                </button>
                <button
                  type="button"
                  className={
                    filter === "errors"
                      ? "results-filter-btn results-filter-btn-active"
                      : "results-filter-btn"
                  }
                  onClick={() => setFilter("errors")}
                >
                  Только с ошибками
                </button>
              </div>
            </div>

            <ResultsSummary results={data.results} />
            <HardestQuestionsBlock questions={hardest} />

            <section
              ref={attemptsRef}
              className="results-attempts-section"
              aria-labelledby="results-attempts-heading"
            >
              <h2 id="results-attempts-heading">Ответы учеников</h2>
              <ResultsAttemptAccordion attempts={filteredAttempts} />
            </section>

            <ResultsNextSteps
              quizId={data.quiz_id}
              hardest={hardest}
              studentsWithErrors={studentsWithErrorsCount(data.results)}
              onDownloadPdf={() => void handleDownloadPdf()}
            />
          </>
        )}

        <DebugPanel ownerId={ownerId} quizId={id} />
      </div>
    </div>
  )
}
