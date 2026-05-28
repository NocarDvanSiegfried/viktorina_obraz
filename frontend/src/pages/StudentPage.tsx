import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react"
import { useParams } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageHeader } from "@/components/layout/PageHeader"

import {
  answerStudentQuestion,
  finishStudentAttempt,
  getQuiz,
  getStudentQuestions,
  startStudentAttempt,
  type StudentFinishResponse,
  type StudentQuestionsResponse,
} from "@/lib/api"
import {
  formatCountdown,
  isTimeExpired,
  remainingSeconds,
} from "@/lib/studentTimers"
import { mapErrorMessage } from "@/lib/apiErrorMessage"

type ChoiceQuestion = {
  id: string
  question_text: string
  question_type: string
  options: string[]
}

function getQuestionType(q: ChoiceQuestion) {
  return q.question_type as "single_choice" | "multiple_choice" | "true_false"
}

export default function StudentPage() {
  const { id } = useParams<{ id: string }>()

  const [studentName, setStudentName] = useState("")
  const [resultId, setResultId] = useState<string | null>(null)
  const [questions, setQuestions] = useState<StudentQuestionsResponse | null>(
    null
  )
  const [finishResult, setFinishResult] = useState<StudentFinishResponse | null>(
    null
  )
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [nowMs, setNowMs] = useState(() => Date.now())
  const [quizTitle, setQuizTitle] = useState("Викторина")

  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [questionStartedAtIso, setQuestionStartedAtIso] = useState<string>("")

  useEffect(() => {
    async function loadQuizTitle() {
      if (!id) return
      const ownerId = window.localStorage.getItem("viktorina_owner_id")
      if (!ownerId) return
      try {
        const quiz = await getQuiz(id, ownerId)
        if (quiz.title?.trim()) {
          setQuizTitle(quiz.title.trim())
        }
      } catch {
        // Public student flow may not have owner id, keep generic title.
      }
    }
    void loadQuizTitle()
  }, [id])

  const completeAttempt = useCallback(
    async (activeResultId: string) => {
      const res = await finishStudentAttempt({
        resultId: activeResultId,
        finishedAtIso: new Date().toISOString(),
      })
      setFinishResult(res)
      const loaded = await getStudentQuestions(activeResultId)
      setQuestions(loaded)
    },
    []
  )

  useEffect(() => {
    if (questions?.next_question) {
      setSelectedOptions([])
      setQuestionStartedAtIso(new Date().toISOString())
    }
  }, [questions?.next_question?.id])

  useEffect(() => {
    if (!questions || questions.completed || finishResult) {
      return
    }
    const timerId = window.setInterval(() => setNowMs(Date.now()), 1000)
    return () => window.clearInterval(timerId)
  }, [questions, finishResult])

  const questionRemaining = useMemo(
    () =>
      remainingSeconds(
        questions?.question_time_seconds,
        questionStartedAtIso,
        nowMs
      ),
    [questions?.question_time_seconds, questionStartedAtIso, nowMs]
  )

  const quizRemaining = useMemo(
    () =>
      remainingSeconds(questions?.full_time_seconds, questions?.started_at, nowMs),
    [questions?.full_time_seconds, questions?.started_at, nowMs]
  )

  const activeTimerRemaining =
    questionRemaining === null
      ? quizRemaining
      : quizRemaining === null
        ? questionRemaining
        : Math.min(questionRemaining, quizRemaining)
  const timeExpired = isTimeExpired(activeTimerRemaining)

  const onStart = async (event: FormEvent) => {
    event.preventDefault()
    setError("")
    if (!id) return
    if (!studentName.trim()) {
      setError("Введите имя ученика.")
      return
    }

    setIsLoading(true)
    setFinishResult(null)
    try {
      const start = await startStudentAttempt(id, studentName.trim())
      setResultId(start.result_id)
      const loaded = await getStudentQuestions(start.result_id)
      setQuestions(loaded)
      setNowMs(Date.now())
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось начать попытку"))
    } finally {
      setIsLoading(false)
    }
  }

  const submitAnswer = async (question: ChoiceQuestion) => {
    if (!resultId) return
    if (!questionStartedAtIso) return
    if (timeExpired) {
      setError("Время вышло. Завершите попытку.")
      return
    }
    setError("")
    setIsSubmitting(true)
    try {
      const qtype = getQuestionType(question)
      let payloadOptions = selectedOptions

      if (qtype === "single_choice" || qtype === "true_false") {
        if (selectedOptions.length !== 1) {
          throw new Error("Выберите один вариант.")
        }
        payloadOptions = selectedOptions
      } else if (selectedOptions.length < 2) {
        throw new Error("Выберите минимум два варианта.")
      }

      await answerStudentQuestion({
        resultId,
        questionId: question.id,
        selectedOptions: payloadOptions,
        questionStartedAtIso,
        answeredAtIso: new Date().toISOString(),
      })

      const loaded = await getStudentQuestions(resultId)
      setQuestions(loaded)
      if (loaded.completed) {
        await completeAttempt(resultId)
      }
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось отправить ответ"))
    } finally {
      setIsSubmitting(false)
    }
  }

  const finish = async () => {
    if (!resultId) return
    setError("")
    setIsSubmitting(true)
    try {
      await completeAttempt(resultId)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось завершить попытку"))
    } finally {
      setIsSubmitting(false)
    }
  }

  const question = questions?.next_question as ChoiceQuestion | undefined
  const qtype = question ? getQuestionType(question) : null
  const progressLabel = questions
    ? `Вопрос ${questions.answered_questions.length + (questions.completed ? 0 : 1)} из ${questions.questions_count}`
    : ""

  const phase = !resultId
    ? "start"
    : questions?.completed
      ? "done"
      : "question"

  return (
    <div className="page student-page" data-phase={phase}>
      <div className="card student-card">
        {phase === "start" && (
          <PageHeader
            title={quizTitle}
            subtitle="Введите имя, чтобы начать викторину."
          />
        )}

        {phase === "question" && (
          <header className="student-question-header">
            <p className="student-quiz-title">{quizTitle}</p>
            <p className="student-progress">{progressLabel}</p>
            {activeTimerRemaining !== null && (
              <p
                className={
                  isTimeExpired(activeTimerRemaining)
                    ? "student-timer timer-expired"
                    : "student-timer"
                }
              >
                Осталось времени: {formatCountdown(activeTimerRemaining)}
              </p>
            )}
          </header>
        )}

        {phase === "done" && (
          <PageHeader title="Готово" subtitle={quizTitle} />
        )}

        {!resultId && (
          <form className="form-grid student-start-form" onSubmit={onStart}>
            <label>
              Имя ученика
              <input
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                placeholder="Например: Иван"
              />
            </label>

            <button type="submit" disabled={isLoading}>
              {isLoading ? "Запуск..." : "Начать"}
            </button>
          </form>
        )}

        <ErrorAlert message={error} />

        {questions && resultId && (
          <>
            {questions.completed && (
              <section className="result student-done">
                {finishResult ? (
                  <div className="student-finish-summary">
                    <p className="student-finish-score">
                      Результат: {finishResult.score}/{finishResult.max_score} (
                      {finishResult.percent}%)
                    </p>
                    <p className="student-finish-time">
                      Время прохождения: {finishResult.duration_seconds} сек
                    </p>
                  </div>
                ) : (
                  <p className="subtitle">Подсчёт результата...</p>
                )}
              </section>
            )}

            {!questions.completed && question && qtype && (
              <section className="result student-question">
                <h2 className="visually-hidden">Вопрос</h2>

                {timeExpired && (
                  <p className="error">
                    Время вышло. Завершите попытку.
                  </p>
                )}

                <p className="student-question-text">{question.question_text}</p>

                {qtype === "multiple_choice" ? (
                  <div className="types-row">
                    {question.options.map((opt) => {
                      const checked = selectedOptions.includes(opt)
                      return (
                        <label key={opt}>
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={timeExpired || isSubmitting}
                            onChange={(e) => {
                              const isChecked = e.target.checked
                              setSelectedOptions((prev) => {
                                if (isChecked) return [...prev, opt]
                                return prev.filter((x) => x !== opt)
                              })
                            }}
                          />
                          {opt}
                        </label>
                      )
                    })}
                  </div>
                ) : (
                  <div className="types-row">
                    {question.options.map((opt) => (
                      <label key={opt}>
                        <input
                          type="radio"
                          name="single"
                          checked={selectedOptions[0] === opt}
                          disabled={timeExpired || isSubmitting}
                          onChange={() => setSelectedOptions([opt])}
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                )}

                <div className="student-actions">
                  <button
                    type="button"
                    className="btn btn-primary"
                    disabled={isSubmitting || timeExpired}
                    onClick={() => submitAnswer(question)}
                  >
                    {isSubmitting ? "Отправка..." : "Ответить"}
                  </button>

                  <button
                    type="button"
                    className="btn btn-ghost student-finish-early"
                    disabled={isSubmitting}
                    onClick={finish}
                  >
                    Завершить досрочно
                  </button>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </div>
  )
}
