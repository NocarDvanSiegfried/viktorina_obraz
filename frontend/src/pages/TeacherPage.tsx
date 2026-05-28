import { useEffect, useMemo, useState } from "react"
import { useParams } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { getQuiz, type QuizDetailResponse } from "@/lib/api"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { getOrCreateOwnerId } from "@/lib/owner"

export default function TeacherPage() {
  const { id } = useParams<{ id: string }>()
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])

  const [quiz, setQuiz] = useState<QuizDetailResponse | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [index, setIndex] = useState(0)
  const [showAnswer, setShowAnswer] = useState(false)

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
        const data = await getQuiz(id, ownerId)
        if (!cancelled) {
          setQuiz(data)
          setIndex(0)
          setShowAnswer(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(mapErrorMessage(err, "Не удалось загрузить викторину"))
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

  const current = quiz?.questions[index] ?? null
  const total = quiz?.questions.length ?? 0

  const goPrev = () => {
    setShowAnswer(false)
    setIndex((prev) => Math.max(0, prev - 1))
  }

  const goNext = () => {
    setShowAnswer(false)
    setIndex((prev) => Math.min(Math.max(total - 1, 0), prev + 1))
  }

  const toggleFullscreen = async () => {
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen()
      return
    }
    await document.exitFullscreen()
  }

  return (
    <div className="page page-wide teacher-page">
      <div className="card teacher-card">
        <PageHeader
          title="Режим учителя"
          subtitle="Показ вопросов на экране класса."
          backTo={id ? `/edit/${id}` : "/"}
          backLabel="← К викторине"
        />

        {isLoading && <PageLoadingSkeleton variant="detail" />}
        <ErrorAlert message={error} />

        {quiz && current && (
          <section className="result">
            <div className="meta">
              <div>
                <strong>{quiz.title}</strong>
              </div>
              <div>
                Вопрос {index + 1} из {total}
              </div>
            </div>

            <h2>{current.question_text}</h2>

            <ul>
              {current.answers.map((opt) => (
                <li key={opt}>
                  {opt}
                  {showAnswer && current.correct_answers.includes(opt) ? " ✓" : ""}
                </li>
              ))}
            </ul>

            {showAnswer && current.explanation && (
              <p className="subtitle">Пояснение: {current.explanation}</p>
            )}

            <div className="link-row">
              <button type="button" onClick={goPrev} disabled={index === 0}>
                Назад
              </button>
              <button type="button" onClick={() => setShowAnswer((v) => !v)}>
                {showAnswer ? "Скрыть ответ" : "Показать ответ"}
              </button>
              <button type="button" onClick={goNext} disabled={index >= total - 1}>
                Далее
              </button>
              <button type="button" onClick={toggleFullscreen}>
                Fullscreen
              </button>
            </div>
          </section>
        )}

        <DebugPanel ownerId={ownerId} quizId={id} />
      </div>
    </div>
  )
}

