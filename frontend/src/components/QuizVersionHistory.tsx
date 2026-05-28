import { useCallback, useEffect, useState } from "react"

import {
  getQuizVersion,
  listQuizVersions,
  restoreQuizVersion,
  type QuizDetailResponse,
  type QuizVersionDetail,
  type QuizVersionSummary,
} from "@/lib/api"
import { formatVersionEventLabel } from "@/lib/quizHistoryLabels"

type QuizVersionHistoryProps = {
  quizId: string
  ownerId: string
  refreshKey: number
  onQuizUpdated: (quiz: QuizDetailResponse) => void
  onError: (message: string) => void
}

export function QuizVersionHistory({
  quizId,
  ownerId,
  refreshKey,
  onQuizUpdated,
  onError,
}: QuizVersionHistoryProps) {
  const [versions, setVersions] = useState<QuizVersionSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selected, setSelected] = useState<QuizVersionDetail | null>(null)
  const [isBusy, setIsBusy] = useState(false)

  const loadVersions = useCallback(async () => {
    setIsLoading(true)
    try {
      const data = await listQuizVersions(quizId, ownerId)
      setVersions(data.versions)
    } catch (err) {
      onError(err instanceof Error ? err.message : "Не удалось загрузить историю")
    } finally {
      setIsLoading(false)
    }
  }, [quizId, ownerId, onError])

  useEffect(() => {
    void loadVersions()
  }, [loadVersions, refreshKey])

  const handlePreview = async (versionId: string) => {
    setIsBusy(true)
    onError("")
    try {
      const detail = await getQuizVersion(quizId, versionId, ownerId)
      setSelected(detail)
    } catch (err) {
      onError(err instanceof Error ? err.message : "Не удалось открыть изменение")
    } finally {
      setIsBusy(false)
    }
  }

  const handleRestore = async (version: QuizVersionSummary) => {
    const eventLabel = formatVersionEventLabel(version.label)
    const confirmed = window.confirm(
      `Восстановить эту версию?\n\n«${eventLabel}» (изменение №${version.version_number}) заменит текущие вопросы и настройки.`
    )
    if (!confirmed) return

    setIsBusy(true)
    onError("")
    try {
      const restored = await restoreQuizVersion(quizId, version.id, ownerId)
      onQuizUpdated(restored)
      setSelected(null)
      await loadVersions()
    } catch (err) {
      onError(err instanceof Error ? err.message : "Не удалось восстановить версию")
    } finally {
      setIsBusy(false)
    }
  }

  return (
    <section className="version-history">
      <h3>История изменений</h3>
      <p className="subtitle">
        Снимки викторины при создании, изменении настроек и правках вопросов.
      </p>

      {isLoading && <p>Загрузка истории...</p>}

      {!isLoading && versions.length === 0 && (
        <p className="subtitle">Изменений пока нет.</p>
      )}

      {!isLoading && versions.length > 0 && (
        <ul className="version-list">
          {versions.map((version) => {
            const eventLabel = formatVersionEventLabel(version.label)
            return (
              <li key={version.id} className="version-item">
                <div className="version-item-main">
                  <strong>{eventLabel}</strong>
                  <span className="version-number">Изменение №{version.version_number}</span>
                  <span className="version-meta">
                    {version.question_count} вопр.
                    {version.created_at &&
                      ` · ${new Date(version.created_at).toLocaleString()}`}
                  </span>
                </div>
                <div className="link-row">
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handlePreview(version.id)}
                  >
                    Открыть изменения
                  </button>
                  <button
                    type="button"
                    disabled={isBusy}
                    onClick={() => void handleRestore(version)}
                  >
                    Восстановить эту версию
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}

      {selected && (
        <div className="version-preview card-nested">
          <h4>
            {formatVersionEventLabel(selected.label)} · изменение №
            {selected.version_number}
          </h4>
          <p>
            <strong>Название:</strong> {selected.snapshot.quiz.title}
          </p>
          <p>
            <strong>Сложность:</strong> {selected.snapshot.quiz.difficulty ?? "—"}
            {" · "}
            <strong>Попыток:</strong> {selected.snapshot.quiz.max_attempts ?? "—"}
          </p>
          <ol>
            {selected.snapshot.questions.map((question, index) => (
              <li key={question.id ?? index}>
                {question.question_text}
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  )
}
