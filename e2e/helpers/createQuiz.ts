import { expect, type Page } from "@playwright/test"

export const DEFAULT_E2E_SOURCE =
  "Клетка — основная структурная и функциональная единица живых организмов. " +
  "Клеточная мембрана отделяет внутреннее содержимое от внешней среды."

export async function fillMinimalCreateForm(
  page: Page,
  options: {
    topic: string
    sourceText?: string
    questionCount?: 3 | 5 | 10
  }
) {
  await page.getByPlaceholder("Например: Клетка").fill(options.topic)
  await page
    .getByPlaceholder("Вставьте текст урока...")
    .fill(options.sourceText ?? DEFAULT_E2E_SOURCE)

  if (options.questionCount != null) {
    await page
      .getByRole("button", { name: String(options.questionCount), exact: true })
      .click()
  }
}

export async function generateQuizWithAi(page: Page) {
  await page.getByRole("button", { name: "Сгенерировать с ИИ" }).click()
  await page.waitForURL(/\/edit\//, { timeout: 60_000 })
}

export async function createQuizViaUi(
  page: Page,
  options: {
    topic: string
    sourceText?: string
    questionCount?: 3 | 5 | 10
  }
) {
  await page.goto("/create")
  await expect(
    page.getByRole("heading", { name: "Новая викторина" })
  ).toBeVisible()
  await fillMinimalCreateForm(page, options)
  await generateQuizWithAi(page)
}
