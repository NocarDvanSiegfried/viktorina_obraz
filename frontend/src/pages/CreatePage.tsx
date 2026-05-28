import { useMemo, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { CreateMinimalForm } from "@/components/create/CreateMinimalForm"
import {
  questionTypesForPreset,
  type CreateTypePreset,
} from "@/components/create/createConstants"
import {
  generateQuizFromMaterials,
  type GenerateQuizResponse,
} from "@/lib/api"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { getOrCreateOwnerId } from "@/lib/owner"

export default function CreatePage() {
  const navigate = useNavigate()
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])

  const [subject, setSubject] = useState("Биология")
  const [grade, setGrade] = useState("8")
  const [topic, setTopic] = useState("")
  const [questionCount, setQuestionCount] = useState(5)
  const [difficulty, setDifficulty] = useState("easy")
  const [typePreset, setTypePreset] = useState<CreateTypePreset>("single_only")
  const [sourceText, setSourceText] = useState("")
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<GenerateQuizResponse | null>(null)

  const trimmedText = sourceText.trim()
  const canSubmit =
    topic.trim().length > 0 && (trimmedText.length > 0 || uploadFile != null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError("")
    setResult(null)

    if (!trimmedText && !uploadFile) {
      setError(
        "Введите текст или загрузите .txt / .pdf / .docx / .pptx / изображение."
      )
      return
    }

    if (!topic.trim()) {
      setError("Укажите тему викторины.")
      return
    }

    const questionTypes = questionTypesForPreset(typePreset)
    const formData = new FormData()
    formData.append("owner_id", ownerId)
    formData.append("subject", subject)
    formData.append("grade", grade)
    formData.append("topic", topic.trim())
    formData.append("question_count", String(questionCount))
    formData.append("difficulty", difficulty)
    questionTypes.forEach((type) => formData.append("question_types", type))

    if (trimmedText) {
      formData.append("source_text", trimmedText)
    }
    if (uploadFile) {
      formData.append("file", uploadFile)
    }

    setIsLoading(true)
    try {
      const data = await generateQuizFromMaterials(formData)
      setResult(data)
      navigate(`/edit/${data.quiz_id}?tab=preview`)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось сгенерировать викторину"))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="page">
      <div className="card">
        <PageHeader
          title="Новая викторина"
          subtitle="Загрузите материал и нажмите «Сгенерировать с ИИ» — затем проверьте вопросы."
          backTo="/"
          backLabel="← Мои викторины"
        />

        {isLoading && (
          <p className="create-minimal-progress" role="status" aria-live="polite">
            Читаем материал и составляем вопросы…
          </p>
        )}
        {isLoading && <PageLoadingSkeleton variant="detail" />}

        <form
          className={`form-grid${isLoading ? " form-grid-loading" : ""}`}
          onSubmit={handleSubmit}
        >
          <CreateMinimalForm
            subject={subject}
            setSubject={setSubject}
            grade={grade}
            setGrade={setGrade}
            topic={topic}
            setTopic={setTopic}
            questionCount={questionCount}
            setQuestionCount={setQuestionCount}
            difficulty={difficulty}
            setDifficulty={setDifficulty}
            typePreset={typePreset}
            setTypePreset={setTypePreset}
            sourceText={sourceText}
            setSourceText={setSourceText}
            uploadFile={uploadFile}
            setUploadFile={setUploadFile}
            isLoading={isLoading}
            canSubmit={canSubmit}
          />
        </form>

        <ErrorAlert message={error} />

        {result && (
          <section className="result">
            <h2>Викторина готова</h2>
            <div className="meta">
              <div>
                <strong>Название:</strong> {result.title}
              </div>
              <div>
                <strong>Вопросов:</strong> {result.questions.length}
              </div>
              <div>
                <Link to={`/edit/${result.quiz_id}?tab=preview`}>
                  Открыть быстрый просмотр →
                </Link>
              </div>
            </div>
          </section>
        )}

        <DebugPanel ownerId={ownerId} quizId={result?.quiz_id} />
      </div>
    </div>
  )
}
