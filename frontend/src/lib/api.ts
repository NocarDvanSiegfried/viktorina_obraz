export const API_BASE_URL =
  import.meta.env.VITE_API_URL?.replace(/\/$/, "") ?? ""

export interface GeneratedQuestion {
  type: string
  text: string
  options: string[]
  correct_answers: string[]
  explanation: string
  source_fragment_id?: string | null
}

export interface GenerateQuizResponse {
  quiz_id: string
  title: string
  subject: string
  grade: string
  topic: string
  difficulty: string
  questions: GeneratedQuestion[]
}

export type QuestionType = "single_choice" | "multiple_choice" | "true_false"

export interface QuizQuestionDetail {
  id: string
  question_text: string
  question_type: QuestionType | string
  answers: string[]
  correct_answers: string[]
  explanation: string | null
  source_fragment: string | null
  points: number
  order_idx: number
}

export interface SourceFragmentCatalogItem {
  id: string
  preview: string
  source_type: string
}

export interface QuizDetailResponse {
  quiz_id: string
  title: string
  subject: string
  grade: string
  topic: string
  difficulty: string
  status: string
  full_time_seconds: number | null
  question_time_seconds: number | null
  max_attempts: number
  created_at?: string | null
  updated_at?: string | null
  fragments?: SourceFragmentCatalogItem[]
  questions: QuizQuestionDetail[]
}

export interface QuizListItem {
  id: string
  title: string
  subject: string | null
  grade: string | null
  difficulty: string | null
  status: string
  questions_count: number
  created_at: string | null
  updated_at: string | null
}

export interface QuizListResponse {
  quizzes: QuizListItem[]
}

export async function generateQuizFromMaterials(
  formData: FormData
): Promise<GenerateQuizResponse> {
  const url = `${API_BASE_URL}/quiz/generate-from-materials`
  const response = await fetch(url, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }

    if (typeof body.detail === "string") {
      throw new Error(body.detail)
    }

    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      throw new Error(body.detail[0].msg)
    }

    throw new Error("Не удалось сгенерировать викторину")
  }

  return response.json() as Promise<GenerateQuizResponse>
}

export async function getQuiz(
  quizId: string,
  ownerId: string
): Promise<QuizDetailResponse> {
  const params = new URLSearchParams({ owner_id: ownerId })
  const url = `${API_BASE_URL}/quiz/${quizId}?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string
    }
    throw new Error(body.detail ?? "Не удалось загрузить викторину")
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function listQuizzes(ownerId: string): Promise<QuizListResponse> {
  const url = `${API_BASE_URL}/quiz/list?owner_id=${encodeURIComponent(ownerId)}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }

    if (typeof body.detail === "string") {
      throw new Error(body.detail)
    }

    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      throw new Error(body.detail[0].msg)
    }

    throw new Error("Не удалось загрузить список викторин")
  }

  return response.json() as Promise<QuizListResponse>
}

export async function updateQuizSettings(
  quizId: string,
  ownerId: string,
  payload: {
    title: string
    difficulty: string
    full_time_seconds: number
    question_time_seconds: number
    max_attempts: number
    status: string
  }
): Promise<QuizDetailResponse> {
  const url = `${API_BASE_URL}/quiz/${quizId}`
  const formData = new FormData()
  formData.append("owner_id", ownerId)
  formData.append("title", payload.title)
  formData.append("difficulty", payload.difficulty)
  formData.append("full_time_seconds", String(payload.full_time_seconds))
  formData.append(
    "question_time_seconds",
    String(payload.question_time_seconds)
  )
  formData.append("max_attempts", String(payload.max_attempts))
  formData.append("status", payload.status)

  const response = await fetch(url, {
    method: "PUT",
    body: formData,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }

    if (typeof body.detail === "string") {
      throw new Error(body.detail)
    }

    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      throw new Error(body.detail[0].msg)
    }

    throw new Error("Не удалось сохранить настройки")
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function deleteQuiz(
  quizId: string,
  ownerId: string
): Promise<{ quiz_id: string; deleted: boolean }> {
  const params = new URLSearchParams({ owner_id: ownerId })
  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}?${params.toString()}`,
    {
      method: "DELETE",
    }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось удалить викторину"))
  }

  return response.json() as Promise<{ quiz_id: string; deleted: boolean }>
}

export async function duplicateQuiz(
  quizId: string,
  ownerId: string
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)

  const response = await fetch(`${API_BASE_URL}/quiz/${quizId}/duplicate`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось создать копию викторины"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

function parseApiError(
  body: { detail?: string | { msg?: string }[] },
  fallback: string
): string {
  if (typeof body.detail === "string") {
    return body.detail
  }
  if (Array.isArray(body.detail) && body.detail[0]?.msg) {
    return body.detail[0].msg
  }
  return fallback
}

export interface QuestionPayload {
  question_text: string
  question_type: QuestionType
  answers: string[]
  correct_answers: string[]
  explanation?: string
  source_fragment?: string
}

function appendQuestionFormData(formData: FormData, payload: QuestionPayload): void {
  formData.append("question_text", payload.question_text)
  formData.append("question_type", payload.question_type)
  payload.answers.forEach((answer) => formData.append("answers", answer))
  payload.correct_answers.forEach((answer) =>
    formData.append("correct_answers", answer)
  )
  if (payload.explanation) {
    formData.append("explanation", payload.explanation)
  }
  if (payload.source_fragment) {
    formData.append("source_fragment", payload.source_fragment)
  }
}

export async function createQuestion(
  quizId: string,
  ownerId: string,
  payload: QuestionPayload
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)
  appendQuestionFormData(formData, payload)

  const response = await fetch(`${API_BASE_URL}/quiz/${quizId}/questions`, {
    method: "POST",
    body: formData,
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось добавить вопрос"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function updateQuestion(
  quizId: string,
  questionId: string,
  ownerId: string,
  payload: QuestionPayload
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)
  appendQuestionFormData(formData, payload)

  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/questions/${questionId}`,
    {
      method: "PUT",
      body: formData,
    }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось сохранить вопрос"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function deleteQuestion(
  quizId: string,
  questionId: string,
  ownerId: string
): Promise<QuizDetailResponse> {
  const params = new URLSearchParams({ owner_id: ownerId })
  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/questions/${questionId}?${params.toString()}`,
    { method: "DELETE" }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось удалить вопрос"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function reorderQuestion(
  quizId: string,
  questionId: string,
  ownerId: string,
  direction: "up" | "down"
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)
  formData.append("direction", direction)

  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/questions/${questionId}/reorder`,
    {
      method: "POST",
      body: formData,
    }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось изменить порядок"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

export interface StudentStartResponse {
  result_id: string
  quiz_id: string
  student_name: string
  attempt_number: number
  full_time_seconds: number | null
  question_time_seconds: number | null
  max_attempts: number
  questions_count: number
  started_at: string
}

export interface StudentQuestionDTO {
  id: string
  question_text: string
  question_type: string
  options: string[]
}

export interface StudentQuestionsResponse {
  result_id: string
  quiz_id: string
  student_name: string
  attempt_number: number
  full_time_seconds: number | null
  question_time_seconds: number | null
  max_attempts: number
  questions_count: number
  started_at: string
  completed: boolean
  next_question: StudentQuestionDTO | null
  answered_questions: string[]
}

export interface StudentFinishResponse {
  result_id: string
  score: number
  max_score: number
  percent: number
  duration_seconds: number
}

export async function startStudentAttempt(
  quizId: string,
  studentName: string,
  startedAtIso?: string
): Promise<StudentStartResponse> {
  const url = `${API_BASE_URL}/student/start`
  const formData = new FormData()
  formData.append("quiz_id", quizId)
  formData.append("student_name", studentName)
  if (startedAtIso) formData.append("started_at", startedAtIso)

  const response = await fetch(url, { method: "POST", body: formData })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось начать попытку")
  }

  return response.json() as Promise<StudentStartResponse>
}

export async function getStudentQuestions(
  resultId: string
): Promise<StudentQuestionsResponse> {
  const url = `${API_BASE_URL}/student/questions?result_id=${encodeURIComponent(
    resultId
  )}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось загрузить вопросы")
  }

  return response.json() as Promise<StudentQuestionsResponse>
}

export async function answerStudentQuestion(params: {
  resultId: string
  questionId: string
  selectedOptions: string[]
  questionStartedAtIso: string
  answeredAtIso: string
}): Promise<void> {
  const url = `${API_BASE_URL}/student/answer`
  const formData = new FormData()
  formData.append("result_id", params.resultId)
  formData.append("question_id", params.questionId)
  params.selectedOptions.forEach((opt) => formData.append("selected_options", opt))
  formData.append("question_started_at", params.questionStartedAtIso)
  formData.append("answered_at", params.answeredAtIso)

  const response = await fetch(url, { method: "POST", body: formData })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось отправить ответ")
  }
}

export async function finishStudentAttempt(params: {
  resultId: string
  finishedAtIso: string
}): Promise<StudentFinishResponse> {
  const url = `${API_BASE_URL}/student/finish`
  const formData = new FormData()
  formData.append("result_id", params.resultId)
  formData.append("finished_at", params.finishedAtIso)

  const response = await fetch(url, { method: "POST", body: formData })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось завершить попытку")
  }

  return response.json() as Promise<StudentFinishResponse>
}

export interface WrongQuestionDTO {
  question_id: string
  question_text: string
  selected_options: string[]
  correct_answers: string[]
}

export interface QuizResultItemDTO {
  result_id: string
  student_name: string
  attempt_number: number
  score: number
  max_score: number
  percent: number
  duration_seconds: number | null
  created_at: string | null
  wrong_questions: WrongQuestionDTO[]
}

export interface QuizResultsResponse {
  quiz_id: string
  title: string
  results: QuizResultItemDTO[]
}

export async function getQuizResults(
  quizId: string,
  ownerId: string
): Promise<QuizResultsResponse> {
  const url = `${API_BASE_URL}/quiz/${quizId}/results?owner_id=${encodeURIComponent(
    ownerId
  )}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось загрузить результаты")
  }

  return response.json() as Promise<QuizResultsResponse>
}

export async function downloadQuizPdf(
  quizId: string,
  ownerId: string
): Promise<void> {
  const url = `${API_BASE_URL}/quiz/${quizId}/export-pdf?owner_id=${encodeURIComponent(
    ownerId
  )}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось скачать PDF")
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = `quiz-${quizId}.pdf`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
}

export async function downloadQuizDocx(
  quizId: string,
  ownerId: string
): Promise<void> {
  const url = `${API_BASE_URL}/quiz/${quizId}/export-docx?owner_id=${encodeURIComponent(
    ownerId
  )}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось скачать DOCX")
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = `quiz-${quizId}.docx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
}

export async function downloadQuizPptx(
  quizId: string,
  ownerId: string,
  options?: { includeAnswers?: boolean }
): Promise<void> {
  const params = new URLSearchParams({ owner_id: ownerId })
  if (options?.includeAnswers === false) {
    params.set("include_answers", "false")
  }
  const url = `${API_BASE_URL}/quiz/${quizId}/export-pptx?${params.toString()}`
  const response = await fetch(url)

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    if (typeof body.detail === "string") throw new Error(body.detail)
    throw new Error("Не удалось скачать PPTX")
  }

  const blob = await response.blob()
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = objectUrl
  link.download = `quiz-${quizId}.pptx`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(objectUrl)
}

export interface QuizVersionSummary {
  id: string
  version_number: number
  label: string
  created_at: string | null
  created_by: string
  question_count: number
  quiz_title: string | null
}

export interface QuizVersionsResponse {
  quiz_id: string
  versions: QuizVersionSummary[]
}

export interface QuizVersionDetail {
  id: string
  quiz_id: string
  version_number: number
  label: string
  created_at: string | null
  created_by: string
  snapshot: {
    quiz: {
      title: string
      subject: string | null
      grade: string | null
      difficulty: string | null
      full_time_seconds: number | null
      question_time_seconds: number | null
      max_attempts: number | null
      status: string | null
    }
    questions: Array<{
      id: string
      question_text: string
      question_type: string
      answers: string[] | null
      correct_answers: string[] | null
    }>
  }
}

export async function listQuizVersions(
  quizId: string,
  ownerId: string
): Promise<QuizVersionsResponse> {
  const params = new URLSearchParams({ owner_id: ownerId })
  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/versions?${params.toString()}`
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось загрузить историю версий"))
  }

  return response.json() as Promise<QuizVersionsResponse>
}

export async function getQuizVersion(
  quizId: string,
  versionId: string,
  ownerId: string
): Promise<QuizVersionDetail> {
  const params = new URLSearchParams({ owner_id: ownerId })
  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/versions/${versionId}?${params.toString()}`
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось загрузить версию"))
  }

  return response.json() as Promise<QuizVersionDetail>
}

export async function restoreQuizVersion(
  quizId: string,
  versionId: string,
  ownerId: string
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)

  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/versions/${versionId}/restore`,
    {
      method: "POST",
      body: formData,
    }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось восстановить версию"))
  }

  return response.json() as Promise<QuizDetailResponse>
}

export async function regenerateQuestion(
  quizId: string,
  questionId: string,
  ownerId: string
): Promise<QuizDetailResponse> {
  const formData = new FormData()
  formData.append("owner_id", ownerId)

  const response = await fetch(
    `${API_BASE_URL}/quiz/${quizId}/questions/${questionId}/regenerate`,
    {
      method: "POST",
      body: formData,
    }
  )

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as {
      detail?: string | { msg?: string }[]
    }
    throw new Error(parseApiError(body, "Не удалось пересоздать вопрос"))
  }

  return response.json() as Promise<QuizDetailResponse>
}
