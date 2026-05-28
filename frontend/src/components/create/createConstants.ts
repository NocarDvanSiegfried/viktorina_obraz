export const SUBJECTS = ["Биология", "История", "Математика", "Русский язык"]
export const GRADES = Array.from({ length: 11 }, (_, i) => String(i + 1))

export type QuestionType = "single_choice" | "multiple_choice" | "true_false"

export const QUESTION_TYPE_LABELS: Record<QuestionType, string> = {
  single_choice: "Один ответ",
  multiple_choice: "Несколько ответов",
  true_false: "Верно / Неверно",
}

export const QUESTION_COUNT_PRESETS = [3, 5, 10] as const

export type CreateTypePreset = "single_only" | "single_and_true_false"

export function questionTypesForPreset(preset: CreateTypePreset): QuestionType[] {
  if (preset === "single_and_true_false") {
    return ["single_choice", "true_false"]
  }
  return ["single_choice"]
}
