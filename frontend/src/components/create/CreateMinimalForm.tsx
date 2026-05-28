import { useId } from "react"

import {
  GRADES,
  QUESTION_COUNT_PRESETS,
  SUBJECTS,
  type CreateTypePreset,
} from "@/components/create/createConstants"

type CreateMinimalFormProps = {
  subject: string
  setSubject: (v: string) => void
  grade: string
  setGrade: (v: string) => void
  topic: string
  setTopic: (v: string) => void

  questionCount: number
  setQuestionCount: (v: number) => void
  difficulty: string
  setDifficulty: (v: string) => void
  typePreset: CreateTypePreset
  setTypePreset: (v: CreateTypePreset) => void

  sourceText: string
  setSourceText: (v: string) => void
  uploadFile: File | null
  setUploadFile: (f: File | null) => void

  isLoading: boolean
  canSubmit: boolean
}

export function CreateMinimalForm({
  subject,
  setSubject,
  grade,
  setGrade,
  topic,
  setTopic,
  questionCount,
  setQuestionCount,
  difficulty,
  setDifficulty,
  typePreset,
  setTypePreset,
  sourceText,
  setSourceText,
  uploadFile,
  setUploadFile,
  isLoading,
  canSubmit,
}: CreateMinimalFormProps) {
  const advancedId = useId()

  return (
    <section aria-label="Создание викторины" className="create-minimal">
      <p className="create-minimal-lead">
        Вставьте конспект или загрузите файл — ИИ составит вопросы за 1–2 минуты.
      </p>

      <div className="form-grid">
        <label className="create-minimal-source">
          Текст урока
          <textarea
            value={sourceText}
            onChange={(e) => setSourceText(e.target.value)}
            placeholder="Вставьте текст урока..."
            rows={6}
            disabled={isLoading}
          />
        </label>

        <label>
          Файл (PDF, DOCX, фото)
          <input
            type="file"
            disabled={isLoading}
            accept=".txt,.pdf,.docx,.pptx,.png,.jpg,.jpeg,.webp,text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.presentationml.presentation,image/png,image/jpeg,image/webp"
            onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
          />
          {uploadFile && (
            <span className="create-minimal-file-name">{uploadFile.name}</span>
          )}
        </label>

        <label>
          Тема викторины
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Например: Клетка"
            required
            disabled={isLoading}
          />
        </label>
      </div>

      <div className="create-minimal-params">
        <fieldset className="create-minimal-chips">
          <legend>Вопросов</legend>
          {QUESTION_COUNT_PRESETS.map((count) => (
            <button
              key={count}
              type="button"
              className={
                questionCount === count
                  ? "chip chip-active"
                  : "chip"
              }
              disabled={isLoading}
              aria-pressed={questionCount === count}
              onClick={() => setQuestionCount(count)}
            >
              {count}
            </button>
          ))}
        </fieldset>

        <fieldset className="create-minimal-chips">
          <legend>Сложность</legend>
          {(
            [
              { value: "easy", label: "Легко" },
              { value: "medium", label: "Средне" },
              { value: "hard", label: "Сложно" },
            ] as const
          ).map((item) => (
            <button
              key={item.value}
              type="button"
              className={
                difficulty === item.value ? "chip chip-active" : "chip"
              }
              disabled={isLoading}
              aria-pressed={difficulty === item.value}
              onClick={() => setDifficulty(item.value)}
            >
              {item.label}
            </button>
          ))}
        </fieldset>

        <fieldset className="create-minimal-type">
          <legend>Тип вопросов</legend>
          <label>
            <input
              type="radio"
              name="type-preset"
              checked={typePreset === "single_only"}
              disabled={isLoading}
              onChange={() => setTypePreset("single_only")}
            />
            Один правильный ответ
          </label>
          <label>
            <input
              type="radio"
              name="type-preset"
              checked={typePreset === "single_and_true_false"}
              disabled={isLoading}
              onChange={() => setTypePreset("single_and_true_false")}
            />
            + Верно / Неверно
          </label>
        </fieldset>
      </div>

      <details className="create-minimal-advanced">
        <summary id={advancedId}>Дополнительно: предмет и класс</summary>
        <div className="form-grid" aria-labelledby={advancedId}>
          <label>
            Предмет
            <select
              value={subject}
              disabled={isLoading}
              onChange={(e) => setSubject(e.target.value)}
            >
              {SUBJECTS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            Класс
            <select
              value={grade}
              disabled={isLoading}
              onChange={(e) => setGrade(e.target.value)}
            >
              {GRADES.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </label>
        </div>
      </details>

      <button
        type="submit"
        className="btn btn-primary create-minimal-submit"
        disabled={isLoading || !canSubmit}
      >
        {isLoading ? "Генерация..." : "Сгенерировать с ИИ"}
      </button>
    </section>
  )
}
