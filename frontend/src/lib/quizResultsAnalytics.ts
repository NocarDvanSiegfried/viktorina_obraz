import type { QuizResultItemDTO } from "@/lib/api"

export type HardestQuestionRow = {
  question_id: string
  question_text: string
  wrong_count: number
}

export function averagePercent(results: QuizResultItemDTO[]): number {
  if (results.length === 0) return 0
  const sum = results.reduce((acc, item) => acc + item.percent, 0)
  return Math.round(sum / results.length)
}

export function uniqueStudentCount(results: QuizResultItemDTO[]): number {
  return new Set(results.map((item) => item.student_name.trim().toLowerCase())).size
}

export function totalAttemptsCount(results: QuizResultItemDTO[]): number {
  return results.length
}

export function topHardestQuestions(
  results: QuizResultItemDTO[],
  topN = 3
): HardestQuestionRow[] {
  const map = new Map<string, HardestQuestionRow>()

  for (const attempt of results) {
    for (const wrong of attempt.wrong_questions) {
      const key = wrong.question_id || wrong.question_text
      const row = map.get(key) ?? {
        question_id: wrong.question_id,
        question_text: wrong.question_text,
        wrong_count: 0,
      }
      row.wrong_count += 1
      map.set(key, row)
    }
  }

  return [...map.values()]
    .sort((a, b) => b.wrong_count - a.wrong_count)
    .slice(0, topN)
}

export function attemptsWithErrors(results: QuizResultItemDTO[]): QuizResultItemDTO[] {
  return results.filter((item) => item.wrong_questions.length > 0)
}

export function formatDurationSeconds(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds) || seconds < 0) {
    return "—"
  }
  return `${Math.round(seconds)} сек`
}

export function pluralizeErrors(count: number): string {
  const n = Math.abs(count)
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return `${n} ошибка`
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return `${n} ошибки`
  }
  return `${n} ошибок`
}

export function studentsWithErrorsCount(results: QuizResultItemDTO[]): number {
  const names = new Set<string>()
  for (const attempt of attemptsWithErrors(results)) {
    names.add(attempt.student_name.trim().toLowerCase())
  }
  return names.size
}

export function formatAttemptSummary(attempt: QuizResultItemDTO): string {
  const errors = pluralizeErrors(attempt.wrong_questions.length)
  const duration = formatDurationSeconds(attempt.duration_seconds)
  return `${attempt.student_name} — ${attempt.score}/${attempt.max_score} (${attempt.percent}%) — ${errors} — ${duration}`
}
