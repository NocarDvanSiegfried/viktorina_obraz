import { expect, test } from "@playwright/test"

const OWNER_ID = "e2e-list-usability-00000000-0000-4000-8000-000000000001"

async function createQuiz(apiBase: string, titleSeed: string) {
  const formData = new URLSearchParams()
  formData.append("owner_id", OWNER_ID)
  formData.append("subject", "Биология")
  formData.append("grade", "8")
  formData.append("topic", titleSeed)
  formData.append("question_count", "2")
  formData.append("difficulty", "easy")
  formData.append("question_types", "single_choice")
  formData.append("question_types", "true_false")
  formData.append("source_text", "Клетка — базовая единица живого организма.")

  const created = await fetch(`${apiBase}/quiz/generate-from-materials`, {
    method: "POST",
    body: formData,
  })
  expect(created.ok).toBeTruthy()
  const quiz = (await created.json()) as { quiz_id: string; title: string }

  const settings = new FormData()
  settings.append("owner_id", OWNER_ID)
  settings.append("title", titleSeed)
  settings.append("difficulty", "easy")
  settings.append("full_time_seconds", "0")
  settings.append("question_time_seconds", "0")
  settings.append("max_attempts", "1")
  settings.append("status", "draft")
  const renamed = await fetch(`${apiBase}/quiz/${quiz.quiz_id}`, {
    method: "PUT",
    body: settings,
  })
  expect(renamed.ok).toBeTruthy()

  return quiz
}

test("list page supports search/filter/sort, grouped cards and table toggle", async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)

  const apiBase = "http://127.0.0.1:8001"
  const alpha = await createQuiz(apiBase, "Alpha list")
  const beta = await createQuiz(apiBase, "Beta list")

  // Publish one quiz to verify status-driven primary action.
  const publishSettings = new FormData()
  publishSettings.append("owner_id", OWNER_ID)
  publishSettings.append("title", "Beta Published")
  publishSettings.append("difficulty", "easy")
  publishSettings.append("full_time_seconds", "0")
  publishSettings.append("question_time_seconds", "0")
  publishSettings.append("max_attempts", "1")
  publishSettings.append("status", "published")
  const updated = await fetch(`${apiBase}/quiz/${beta.quiz_id}`, {
    method: "PUT",
    body: publishSettings,
  })
  expect(updated.ok).toBeTruthy()

  await page.goto("/")

  await expect(page.getByPlaceholder("Поиск по названию или предмету")).toBeVisible()
  await expect(page.getByLabel("Фильтр по статусу")).toBeVisible()
  await expect(page.getByLabel("Сортировка")).toBeVisible()

  await page.getByPlaceholder("Поиск по названию или предмету").fill("alpha")
  await expect(page.getByText("Beta Published")).toHaveCount(0)
  await expect(page.getByText(/Alpha/i).first()).toBeVisible()

  await page.getByRole("button", { name: "Сбросить фильтры" }).click()
  await page.getByLabel("Фильтр по статусу").selectOption("published")
  await expect(page.getByText("Beta Published").first()).toBeVisible()
  await expect(page.getByText(/Alpha/i)).toHaveCount(0)

  await page.getByLabel("Фильтр по статусу").selectOption("all")
  await page.getByLabel("Сортировка").selectOption("title_asc")
  await page.getByRole("button", { name: "Таблица" }).click()
  const titles = await page.locator(".quiz-table tbody tr td:first-child").allTextContents()
  expect(titles.length).toBeGreaterThan(1)
  const normalized = titles.map((t) => t.trim())
  const sorted = [...normalized].sort((a, b) => a.localeCompare(b, "ru"))
  expect(normalized).toEqual(sorted)

  await page.getByRole("button", { name: "Карточки" }).click()
  await expect(page.getByRole("link", { name: "Продолжить редактирование" }).first()).toBeVisible()
  await expect(page.getByRole("link", { name: "Смотреть результаты" }).first()).toBeVisible()
  await expect(page.getByRole("heading", { name: /Нужно завершить/ })).toBeVisible()
  await expect(page.getByRole("heading", { name: /Готово к прохождению/ })).toBeVisible()

  await page.getByRole("button", { name: "Таблица" }).click()
  await expect(page.getByRole("table")).toBeVisible()
  await expect(page.getByRole("columnheader", { name: "Название" })).toBeVisible()
  await expect(page.getByRole("cell", { name: "Beta Published" }).first()).toBeVisible()

  // Keep lints quiet about unused variable from creation.
  expect(alpha.quiz_id).toBeTruthy()
})
