import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react"
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { useToast } from "@/components/feedback/ToastProvider"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { MaterialFragmentsPanel } from "@/components/MaterialFragmentsPanel"
import { NewQuestionForm } from "@/components/QuestionEditor"
import { QuestionListPanel } from "@/components/questions/QuestionListPanel"
import { QuizVersionHistory } from "@/components/QuizVersionHistory"
import {
  getActiveHubTab,
  QuizHubLayout,
} from "@/components/quiz/QuizHubLayout"
import { Button } from "@/components/ui/Button"
import {
  downloadQuizDocx,
  downloadQuizPdf,
  downloadQuizPptx,
  deleteQuiz,
  getQuiz,
  getQuizResults,
  updateQuizSettings,
  type QuizDetailResponse,
} from "@/lib/api"
import {
  markSettingsSaved,
} from "@/lib/quizHubStorage"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { formatDifficultyLabel, formatStatusLabel } from "@/lib/quizLabels"
import { getOrCreateOwnerId } from "@/lib/owner"

const MAX_QUESTIONS = 15
const PREVIEW_TEXT_MAX = 120

function truncatePreviewText(value: string): string {
  const text = value.trim()
  if (text.length <= PREVIEW_TEXT_MAX) {
    return text
  }
  return `${text.slice(0, PREVIEW_TEXT_MAX)}…`
}

export default function EditPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const activeTab = getActiveHubTab(searchParams)
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])
  const toast = useToast()

  const [quiz, setQuiz] = useState<QuizDetailResponse | null>(null)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [resultsCount, setResultsCount] = useState(0)

  const [title, setTitle] = useState("")
  const [difficulty, setDifficulty] = useState("easy")
  const [fullTimeSeconds, setFullTimeSeconds] = useState(0)
  const [questionTimeSeconds, setQuestionTimeSeconds] = useState(0)
  const [maxAttempts, setMaxAttempts] = useState(1)
  const [status, setStatus] = useState("draft")
  const [versionRefreshKey, setVersionRefreshKey] = useState(0)

  const studentLink = useMemo(() => {
    if (!id) return ""
    return `${window.location.origin}/student/${id}`
  }, [id])

  const legacyCopy = (text: string): boolean => {
    const el = document.createElement("textarea")
    el.value = text
    el.style.position = "fixed"
    el.style.opacity = "0"
    document.body.appendChild(el)
    el.focus()
    el.select()
    try {
      const ok = document.execCommand("copy")
      document.body.removeChild(el)
      return ok
    } catch {
      document.body.removeChild(el)
      return false
    }
  }

  const copyToClipboard = useCallback(async (text: string) => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text)
        toast.showSuccess("Ссылка скопирована")
        return true
      }
      const ok = legacyCopy(text)
      if (ok) {
        toast.showSuccess("Ссылка скопирована")
      } else {
        toast.showError("Не удалось скопировать ссылку")
      }
      return ok
    } catch {
      const ok = legacyCopy(text)
      if (ok) {
        toast.showSuccess("Ссылка скопирована")
      } else {
        toast.showError("Не удалось скопировать ссылку")
      }
      return ok
    }
  }, [toast])

  const handleOperationError = useCallback(
    (message: string) => {
      const mapped = mapErrorMessage(message, "Не удалось выполнить операцию")
      setError(mapped)
    },
    []
  )

  const copyStudentLink = useCallback(async () => {
    await copyToClipboard(studentLink)
  }, [copyToClipboard, studentLink])

  const handleDownloadPdf = async () => {
    if (!quiz) return
    setError("")
    try {
      await downloadQuizPdf(quiz.quiz_id, ownerId)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось скачать PDF"))
    }
  }

  const handleDownloadDocx = async () => {
    if (!quiz) return
    setError("")
    try {
      await downloadQuizDocx(quiz.quiz_id, ownerId)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось скачать DOCX"))
    }
  }

  const handleDownloadPptx = async () => {
    if (!quiz) return
    setError("")
    try {
      await downloadQuizPptx(quiz.quiz_id, ownerId)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось скачать PPTX"))
    }
  }

  const handleDownloadPptxClassroom = async () => {
    if (!quiz) return
    setError("")
    try {
      await downloadQuizPptx(quiz.quiz_id, ownerId, { includeAnswers: false })
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось скачать PPTX для класса"))
    }
  }

  useEffect(() => {
    if (!id) {
      setError("Не указан идентификатор викторины.")
      setIsLoading(false)
      return
    }

    let cancelled = false

    const loadQuiz = async () => {
      setIsLoading(true)
      setError("")
      try {
        const data = await getQuiz(id, ownerId)
        if (!cancelled) {
          setQuiz(data)
          setTitle(data.title)
          setDifficulty(data.difficulty)
          setFullTimeSeconds(data.full_time_seconds ?? 0)
          setQuestionTimeSeconds(data.question_time_seconds ?? 0)
          setMaxAttempts(data.max_attempts ?? 1)
          setStatus(data.status)
        }
      } catch (err) {
        if (!cancelled) {
          setError(mapErrorMessage(err, "Не удалось загрузить викторину"))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadQuiz()

    return () => {
      cancelled = true
    }
  }, [id, ownerId])

  useEffect(() => {
    if (!quiz) return

    let cancelled = false

    const loadResults = async () => {
      try {
        const data = await getQuizResults(quiz.quiz_id, ownerId)
        if (!cancelled) setResultsCount(data.results.length)
      } catch {
        if (!cancelled) setResultsCount(0)
      }
    }

    void loadResults()

    return () => {
      cancelled = true
    }
  }, [quiz, ownerId])

  const handleSave = async (event: FormEvent) => {
    event.preventDefault()
    if (!quiz || !id) return

    setError("")
    setIsSaving(true)
    try {
      const updated = await updateQuizSettings(quiz.quiz_id, ownerId, {
        title,
        difficulty,
        full_time_seconds: fullTimeSeconds,
        question_time_seconds: questionTimeSeconds,
        max_attempts: maxAttempts,
        status,
      })
      setQuiz(updated)
      markSettingsSaved(id)
      setVersionRefreshKey((key) => key + 1)
      toast.showSuccess("Настройки сохранены")
    } catch (err) {
      const message = mapErrorMessage(err, "Не удалось сохранить настройки")
      setError(message)
      toast.showError(message)
    } finally {
      setIsSaving(false)
    }
  }

  const handleDeleteQuiz = useCallback(async () => {
    if (!quiz) return

    const confirmed = window.confirm(
      `Удалить викторину "${quiz.title}"? Это действие можно отменить только через резервную копию базы данных.`
    )
    if (!confirmed) return

    setError("")
    try {
      await deleteQuiz(quiz.quiz_id, ownerId)
      toast.showSuccess("Викторина удалена")
      navigate("/")
    } catch (err) {
      const message = mapErrorMessage(err, "Не удалось удалить викторину")
      setError(message)
      toast.showError(message)
    }
  }, [navigate, ownerId, quiz, toast])

  const handleQuizUpdated = (updated: QuizDetailResponse) => {
    setQuiz(updated)
    setTitle(updated.title)
    setDifficulty(updated.difficulty)
    setFullTimeSeconds(updated.full_time_seconds ?? 0)
    setQuestionTimeSeconds(updated.question_time_seconds ?? 0)
    setMaxAttempts(updated.max_attempts ?? 1)
    setStatus(updated.status)
    setVersionRefreshKey((key) => key + 1)
  }

  const headerTitle = quiz?.title ?? "Моя викторина"
  return (
    <div className="page">
      <div className="card">
        <PageHeader
          title={headerTitle}
          subtitle="Проверьте вопросы, настройте правила и поделитесь ссылкой с классом."
          backTo="/"
          backLabel="← Мои викторины"
        />

        {isLoading && <PageLoadingSkeleton variant="detail" />}
        <ErrorAlert message={error} />

        {quiz && id && (
          <QuizHubLayout quizId={id}>
            {activeTab === "preview" && (
              <section className="result">
                <h2>Быстрый просмотр</h2>
                <p className="subtitle">
                  Сразу проверьте вопросы и скачайте материалы. Редактирование открывается отдельно.
                </p>

                <div className="link-row">
                  <Button type="button" variant="secondary" onClick={handleDownloadPdf}>
                    Скачать PDF
                  </Button>
                  <Button type="button" variant="secondary" onClick={handleDownloadDocx}>
                    Скачать DOCX
                  </Button>
                  <Button type="button" variant="secondary" onClick={handleDownloadPptx}>
                    Скачать PPTX
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={handleDownloadPptxClassroom}
                  >
                    PPTX для класса
                  </Button>
                </div>

                <div className="link-row">
                  <Button type="button" onClick={() => void copyStudentLink()}>
                    Скопировать ссылку ученику
                  </Button>
                  <Link to={`/edit/${id}?tab=questions`} className="btn btn-ghost">
                    Открыть редактор вопросов
                  </Link>
                </div>

                <ol className="question-preview-list">
                  {quiz.questions.map((question, index) => (
                    <li key={question.id} className="question-preview-item">
                      <span className="question-preview-number">{index + 1}</span>
                      <div>
                        <p className="question-preview-text">
                          {truncatePreviewText(question.question_text)}
                        </p>
                        <p className="question-preview-meta">
                          {question.question_type} · {question.answers.length} вариант(ов)
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {activeTab === "questions" && (
              <section className="result">
                <h2>Вопросы</h2>
                <p className="subtitle">
                  Проверьте формулировки и ответы перед отправкой ученикам.
                </p>
                <QuestionListPanel
                  quizId={quiz.quiz_id}
                  ownerId={ownerId}
                  questions={quiz.questions}
                  fragmentCatalog={quiz.fragments}
                  onQuizUpdated={handleQuizUpdated}
                  onError={handleOperationError}
                />
                <NewQuestionForm
                  quizId={quiz.quiz_id}
                  ownerId={ownerId}
                  disabled={quiz.questions.length >= MAX_QUESTIONS}
                  onQuizUpdated={handleQuizUpdated}
                  onError={handleOperationError}
                />
                {quiz.questions.length >= MAX_QUESTIONS && (
                  <p className="subtitle">Достигнут лимит {MAX_QUESTIONS} вопросов.</p>
                )}
              </section>
            )}

            {activeTab === "settings" && (
              <section className="result">
                <h2>Настройки</h2>
                <form className="form-grid" onSubmit={handleSave}>
                  <label>
                    Заголовок
                    <input value={title} onChange={(e) => setTitle(e.target.value)} />
                  </label>

                  <label>
                    Сложность
                    <select
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                    >
                      <option value="easy">Легко</option>
                      <option value="medium">Средне</option>
                      <option value="hard">Сложно</option>
                    </select>
                  </label>

                  <label>
                    Общее время (сек)
                    <input
                      type="number"
                      min={0}
                      value={fullTimeSeconds}
                      onChange={(e) => setFullTimeSeconds(Number(e.target.value))}
                    />
                  </label>

                  <label>
                    Время на вопрос (сек)
                    <input
                      type="number"
                      min={0}
                      value={questionTimeSeconds}
                      onChange={(e) => setQuestionTimeSeconds(Number(e.target.value))}
                    />
                  </label>

                  <label>
                    Максимум попыток
                    <input
                      type="number"
                      min={1}
                      value={maxAttempts}
                      onChange={(e) => setMaxAttempts(Number(e.target.value))}
                    />
                  </label>

                  <label>
                    Статус
                    <select value={status} onChange={(e) => setStatus(e.target.value)}>
                      <option value="draft">Черновик</option>
                      <option value="published">Готово</option>
                    </select>
                  </label>

                  <Button type="submit" disabled={isSaving}>
                    {isSaving ? "Сохранение..." : "Сохранить настройки"}
                  </Button>
                </form>

                <div className="meta quiz-settings-meta">
                  <div>
                    <strong>Предмет:</strong> {quiz.subject}, {quiz.grade} класс
                  </div>
                  <div>
                    <strong>Сложность:</strong> {formatDifficultyLabel(quiz.difficulty)}
                  </div>
                  <div>
                    <strong>Статус:</strong> {formatStatusLabel(quiz.status)}
                  </div>
                  <div>
                    <strong>Вопросов:</strong> {quiz.questions.length}
                  </div>
                </div>

                <section className="danger-zone">
                  <h3>Опасная зона</h3>
                  <p className="subtitle">
                    Удалённая викторина исчезнет из списков, истории и ссылок для учеников.
                  </p>
                  <Button variant="ghost" onClick={() => void handleDeleteQuiz()}>
                    Удалить викторину
                  </Button>
                </section>
              </section>
            )}

            {activeTab === "results" && (
              <section className="result">
                <h2>Результаты</h2>
                {resultsCount === 0 ? (
                  <>
                    <p className="subtitle">
                      Результаты появятся после прохождения учениками.
                    </p>
                    <Link to={`/edit/${id}?tab=preview`} className="btn btn-primary">
                      Открыть быстрый просмотр
                    </Link>
                  </>
                ) : (
                  <>
                    <p className="subtitle">
                      Учеников прошло: {resultsCount}. Откройте полную аналитику.
                    </p>
                    <Link to={`/results/${id}`} className="btn btn-primary">
                      Посмотреть результаты
                    </Link>
                  </>
                )}
              </section>
            )}

            {activeTab === "sources" && (
              <MaterialFragmentsPanel fragments={quiz.fragments ?? []} />
            )}

            {activeTab === "history" && (
              <QuizVersionHistory
                quizId={quiz.quiz_id}
                ownerId={ownerId}
                refreshKey={versionRefreshKey}
                onQuizUpdated={handleQuizUpdated}
                onError={handleOperationError}
              />
            )}
          </QuizHubLayout>
        )}

        <DebugPanel ownerId={ownerId} quizId={quiz?.quiz_id ?? id} />
      </div>
    </div>
  )
}
