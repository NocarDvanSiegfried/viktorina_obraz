/** Human-readable labels for quiz list cards (UX-1 glossary). */

const DIFFICULTY_LABELS: Record<string, string> = {
  easy: "Легко",
  medium: "Средне",
  hard: "Сложно",
}

const STATUS_LABELS: Record<string, string> = {
  draft: "Черновик",
  published: "Готово",
}

export function formatDifficultyLabel(value: string | null | undefined): string {
  if (!value) return "—"
  return DIFFICULTY_LABELS[value] ?? value
}

export function formatStatusLabel(value: string | null | undefined): string {
  if (!value) return "—"
  return STATUS_LABELS[value] ?? value
}

export function formatGradeLabel(grade: string | null | undefined): string {
  if (!grade) return "—"
  return `${grade} класс`
}

export function formatUpdatedAt(iso: string | null | undefined): string | null {
  if (!iso) return null
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return null
  return date.toLocaleString()
}
