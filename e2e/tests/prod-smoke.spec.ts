/**
 * Day 20: production / staging UI smoke (external server, no Playwright webServer).
 *
 * Usage:
 *   PLAYWRIGHT_NO_WEBSERVER=1
 *   PLAYWRIGHT_BASE_URL=http://127.0.0.1:8080
 *   SMOKE_API_URL=http://127.0.0.1:8000
 *   npx playwright test e2e/tests/prod-smoke.spec.ts
 *
 * Optional: SMOKE_QUIZ_ID + SMOKE_OWNER_ID to skip API generation.
 */

import { expect, test, type Page } from "@playwright/test"

async function answerCurrentQuestion(page: Page) {
  await expect(page.getByText(/Вопрос \d+ из \d+/)).toBeVisible()
  const trueOption = page.getByLabel("Верно", { exact: true })
  if (await trueOption.isVisible()) {
    await trueOption.check()
  } else {
    await page.getByRole("radio").first().check()
  }
  await page.getByRole("button", { name: "Ответить" }).click()
}

const OWNER_ID =
  process.env.SMOKE_OWNER_ID ?? "prod-smoke-00000000-0000-4000-8000-000000000001"

const E2E_SOURCE =
  "The cell is the basic structural unit of living organisms. " +
  "The cell membrane separates the interior from the environment."

let quizId = process.env.SMOKE_QUIZ_ID ?? ""

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

test.beforeAll(async ({ request }) => {
  if (quizId) {
    return
  }

  const apiRoot = (
    process.env.SMOKE_API_URL ??
    process.env.PLAYWRIGHT_API_URL ??
    process.env.API_URL ??
    "http://127.0.0.1:8001"
  ).replace(/\/$/, "")

  const formBody = new URLSearchParams()
  formBody.set("owner_id", OWNER_ID)
  formBody.set("subject", "Biology")
  formBody.set("grade", "8")
  formBody.set("topic", "Cell")
  formBody.set("question_count", "2")
  formBody.set("difficulty", "easy")
  formBody.append("question_types", "single_choice")
  formBody.append("question_types", "true_false")
  formBody.set("source_text", E2E_SOURCE)

  const response = await request.post(`${apiRoot}/quiz/generate-from-materials`, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    data: formBody.toString(),
    timeout: 120_000,
  })

  if (!response.ok()) {
    console.warn(
      `prod-smoke: generation failed (${response.status()}). ` +
        "Set SMOKE_QUIZ_ID / SMOKE_OWNER_ID for UI-only checks."
    )
    return
  }

  const payload = (await response.json()) as { quiz_id?: string }
  quizId = payload.quiz_id ?? ""
})

test("prod: home and create pages load", async ({ page }) => {
  await page.goto("/")
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()

  await page.goto("/create")
  await expect(
    page.getByRole("heading", { name: "Новая викторина" })
  ).toBeVisible()
})

test("prod: edit exports PDF and DOCX", async ({ page }) => {
  test.skip(!quizId, "No quiz id — set SMOKE_QUIZ_ID or ensure API generation works")

  await page.goto(`/edit/${quizId}`)
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible({
    timeout: 30_000,
  })

  await page
    .getByRole("navigation", { name: "Разделы викторины" })
    .getByRole("link", { name: "Быстрый просмотр", exact: true })
    .click()
  const pdfDownload = page.waitForEvent("download")
  await page.getByRole("button", { name: "Скачать PDF" }).click()
  const pdf = await pdfDownload
  expect(pdf.suggestedFilename().toLowerCase()).toMatch(/\.pdf$/)

  const docxDownload = page.waitForEvent("download")
  await page.getByRole("button", { name: "Скачать DOCX" }).click()
  const docx = await docxDownload
  expect(docx.suggestedFilename().toLowerCase()).toMatch(/\.docx$/)

  const pptxDownload = page.waitForEvent("download")
  await page.getByRole("button", { name: "Скачать PPTX" }).click()
  const pptx = await pptxDownload
  expect(pptx.suggestedFilename().toLowerCase()).toMatch(/\.pptx$/)

  const classroomPptxDownload = page.waitForEvent("download")
  await page.getByRole("button", { name: "PPTX для класса (без ответов)" }).click()
  const classroomPptx = await classroomPptxDownload
  expect(classroomPptx.suggestedFilename().toLowerCase()).toMatch(/\.pptx$/)
})

test("prod: student flow and results", async ({ page }) => {
  test.skip(!quizId, "No quiz id — set SMOKE_QUIZ_ID or ensure API generation works")

  await page.goto(`/student/${quizId}`)
  await page.getByPlaceholder("Например: Иван").fill("Prod Smoke Student")
  await page.getByRole("button", { name: "Начать" }).click()

  await expect(page.getByText(/Вопрос \d+ из \d+/)).toBeVisible({
    timeout: 20_000,
  })

  await answerCurrentQuestion(page)
  await expect(page.getByText("Вопрос 2 из 2")).toBeVisible({ timeout: 15_000 })
  await answerCurrentQuestion(page)

  await expect(page.getByText(/Результат:/)).toBeVisible({ timeout: 30_000 })

  await page.goto(`/results/${quizId}`)
  await expect(page.getByRole("heading", { name: /Результаты:/ })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Сводка класса" })).toBeVisible()
  await expect(page.getByText("Prod Smoke Student")).toBeVisible()
})
