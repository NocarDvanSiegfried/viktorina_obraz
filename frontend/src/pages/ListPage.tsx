import { useCallback, useEffect, useMemo, useState } from "react"

import { ErrorAlert } from "@/components/feedback/ErrorAlert"
import { PageLoadingSkeleton } from "@/components/feedback/PageLoadingSkeleton"
import { useToast } from "@/components/feedback/ToastProvider"
import { DebugPanel } from "@/components/layout/DebugPanel"
import { PageHeader } from "@/components/layout/PageHeader"
import { QuizCard } from "@/components/quiz/QuizCard"
import { Button } from "@/components/ui/Button"
import { deleteQuiz, duplicateQuiz, listQuizzes, type QuizListItem } from "@/lib/api"
import { mapErrorMessage } from "@/lib/apiErrorMessage"
import { getOrCreateOwnerId } from "@/lib/owner"
import {
  formatDifficultyLabel,
  formatStatusLabel,
  formatUpdatedAt,
} from "@/lib/quizLabels"

export default function ListPage() {
  const ownerId = useMemo(() => getOrCreateOwnerId(), [])
  const toast = useToast()

  const [items, setItems] = useState<QuizListItem[]>([])
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState<"all" | "draft" | "published">("all")
  const [sortBy, setSortBy] = useState<"updated_desc" | "updated_asc" | "title_asc">(
    "updated_desc"
  )
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards")

  const loadItems = useCallback(async () => {
    setIsLoading(true)
    setError("")
    try {
      const data = await listQuizzes(ownerId)
      setItems(data.quizzes)
    } catch (err) {
      setError(mapErrorMessage(err, "Не удалось загрузить список"))
    } finally {
      setIsLoading(false)
    }
  }, [ownerId])

  useEffect(() => {
    void loadItems()
  }, [loadItems])

  const filteredItems = items
    .filter((quiz) => {
      if (statusFilter !== "all" && quiz.status !== statusFilter) {
        return false
      }

      const q = search.trim().toLowerCase()
      if (!q) return true

      const haystack = [quiz.title, quiz.subject, quiz.grade]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
      return haystack.includes(q)
    })
    .sort((a, b) => {
      if (sortBy === "title_asc") {
        return a.title.localeCompare(b.title, "ru")
      }

      const aTs = new Date(a.updated_at ?? a.created_at ?? 0).getTime()
      const bTs = new Date(b.updated_at ?? b.created_at ?? 0).getTime()

      if (sortBy === "updated_asc") {
        return aTs - bTs
      }
      return bTs - aTs
    })

  const hasActiveFilters = search.trim().length > 0 || statusFilter !== "all" || sortBy !== "updated_desc"

  const resetFilters = () => {
    setSearch("")
    setStatusFilter("all")
    setSortBy("updated_desc")
  }

  const handleDuplicateQuiz = async (quizId: string) => {
    try {
      const duplicated = await duplicateQuiz(quizId, ownerId)
      toast.showSuccess(`Создана копия: ${duplicated.title}`)
      await loadItems()
    } catch (err) {
      const message = mapErrorMessage(err, "Не удалось создать копию")
      setError(message)
      toast.showError(message)
    }
  }

  const handleArchiveQuiz = async (quizId: string, title: string) => {
    const confirmed = window.confirm(
      `Архивировать викторину "${title}"? Она исчезнет из списка.`
    )
    if (!confirmed) return

    try {
      await deleteQuiz(quizId, ownerId)
      toast.showSuccess("Викторина отправлена в архив")
      await loadItems()
    } catch (err) {
      const message = mapErrorMessage(err, "Не удалось архивировать викторину")
      setError(message)
      toast.showError(message)
    }
  }

  const draftItems = filteredItems.filter((quiz) => quiz.status === "draft")
  const publishedItems = filteredItems.filter((quiz) => quiz.status === "published")
  const groupedCards = [
    { id: "draft", title: "Нужно завершить", items: draftItems },
    { id: "published", title: "Готово к прохождению", items: publishedItems },
  ].filter((group) => group.items.length > 0)

  return (
    <div className="page">
      <div className="card">
        <PageHeader
          title="Ваши викторины"
          subtitle="Создавайте викторины из конспекта или файла и делитесь ссылкой с классом."
          actions={
            <Button as="link" to="/create">
              Создать викторину
            </Button>
          }
        />

        {isLoading && <PageLoadingSkeleton variant="list" />}
        <ErrorAlert message={error} />

        {!isLoading && !error && items.length > 0 && (
          <section className="list-controls" aria-label="Панель списка викторин">
            <label className="list-control">
              Поиск
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Поиск по названию или предмету"
              />
            </label>

            <label className="list-control">
              Статус
              <select
                aria-label="Фильтр по статусу"
                value={statusFilter}
                onChange={(event) =>
                  setStatusFilter(event.target.value as "all" | "draft" | "published")
                }
              >
                <option value="all">Все</option>
                <option value="draft">Черновик</option>
                <option value="published">Готово</option>
              </select>
            </label>

            <label className="list-control">
              Сортировка
              <select
                aria-label="Сортировка"
                value={sortBy}
                onChange={(event) =>
                  setSortBy(
                    event.target.value as "updated_desc" | "updated_asc" | "title_asc"
                  )
                }
              >
                <option value="updated_desc">Сначала новые</option>
                <option value="updated_asc">Сначала старые</option>
                <option value="title_asc">По названию А-Я</option>
              </select>
            </label>

            <div className="list-view-toggle" aria-label="Режим отображения">
              <Button
                variant={viewMode === "cards" ? "secondary" : "ghost"}
                onClick={() => setViewMode("cards")}
              >
                Карточки
              </Button>
              <Button
                variant={viewMode === "table" ? "secondary" : "ghost"}
                onClick={() => setViewMode("table")}
              >
                Таблица
              </Button>
            </div>

            {hasActiveFilters && (
              <Button variant="ghost" onClick={resetFilters}>
                Сбросить фильтры
              </Button>
            )}
          </section>
        )}

        {!isLoading && !error && items.length === 0 && (
          <section className="quiz-list-empty">
            <h2 className="quiz-list-empty-title">Пока нет викторин</h2>
            <p className="subtitle">
              Загрузите конспект или файл — викторина появится в этом списке.
            </p>
            <Button as="link" to="/create">
              Создать викторину
            </Button>
          </section>
        )}

        {filteredItems.length > 0 && viewMode === "cards" && (
          <div className="quiz-groups">
            {groupedCards.map((group) => (
              <section key={group.id} className="quiz-group" aria-label={group.title}>
                <h2 className="quiz-group-title">
                  {group.title} ({group.items.length})
                </h2>
                <ul className="quiz-list">
                  {group.items.map((quiz) => (
                    <li key={quiz.id}>
                      <QuizCard
                        quiz={quiz}
                        onDuplicate={handleDuplicateQuiz}
                        onArchive={handleArchiveQuiz}
                      />
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}

        {filteredItems.length > 0 && viewMode === "table" && (
          <div className="quiz-table-wrap">
            <table className="quiz-table">
              <caption className="visually-hidden">Таблица викторин</caption>
              <thead>
                <tr>
                  <th scope="col">Название</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Сложность</th>
                  <th scope="col">Вопросов</th>
                  <th scope="col">Обновлено</th>
                  <th scope="col">Действия</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((quiz) => (
                  <tr key={quiz.id}>
                    <td>{quiz.title}</td>
                    <td>{formatStatusLabel(quiz.status)}</td>
                    <td>{quiz.difficulty ? formatDifficultyLabel(quiz.difficulty) : "—"}</td>
                    <td>{quiz.questions_count}</td>
                    <td>{formatUpdatedAt(quiz.updated_at ?? quiz.created_at) ?? "—"}</td>
                    <td>
                      <div className="quiz-table-actions">
                        <Button as="link" to={`/edit/${quiz.id}`} variant="ghost">
                          Редактировать
                        </Button>
                        <Button
                          as="link"
                          to={quiz.status === "published" ? `/results/${quiz.id}` : `/edit/${quiz.id}`}
                          variant="secondary"
                        >
                          {quiz.status === "published"
                            ? "Смотреть результаты"
                            : "Продолжить"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!isLoading && !error && items.length > 0 && filteredItems.length === 0 && (
          <section className="quiz-list-empty">
            <h2 className="quiz-list-empty-title">Ничего не найдено</h2>
            <p className="subtitle">Измените фильтры или очистите поиск.</p>
            <Button variant="ghost" onClick={resetFilters}>
              Сбросить фильтры
            </Button>
          </section>
        )}

        <DebugPanel ownerId={ownerId} />
      </div>
    </div>
  )
}
