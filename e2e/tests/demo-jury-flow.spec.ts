/**
 * Day 22: full jury UI matrix (mock GigaChat via Playwright webServer).
 * material → generation → edit/versions/fragments → exports → student → results → teacher
 */

import { expect, test, type Page } from "@playwright/test"

import { createQuizViaUi } from "../helpers/createQuiz"

const OWNER_ID = "e2e-jury-00000000-0000-4000-8000-000000000001"

test.beforeEach(async ({ page }) => {
  await page.addInitScript((ownerId: string) => {
    localStorage.setItem("viktorina_owner_id", ownerId)
  }, OWNER_ID)
})

async function answerMockQuestion(page: Page, questionIndex: number) {
  await expect(page.getByText(/Вопрос \d+ из \d+/)).toBeVisible({
    timeout: 15_000,
  })

  if (questionIndex === 0) {
    await page.getByLabel("Клетка", { exact: true }).check()
  } else {
    await page.getByLabel("Неверно", { exact: true }).check()
  }

  await page.getByRole("button", { name: "Ответить" }).click()
}

test("jury: full demo matrix UI", async ({ page }) => {
  await createQuizViaUi(page, { topic: "Клетка", questionCount: 3 })

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()

  await page
    .getByRole("navigation", { name: "Разделы викторины" })
    .getByRole("link", { name: "Настройки", exact: true })
    .click()
  await page.getByRole("button", { name: "Сохранить настройки" }).click()
  await page
    .getByRole("navigation", { name: "Дополнительно" })
    .getByRole("link", { name: "История", exact: true })
    .click()
  await expect(page.getByText("Изменение настроек")).toBeVisible({ timeout: 15_000 })

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

  await page
    .getByRole("navigation", { name: "Дополнительно" })
    .getByRole("link", { name: "История", exact: true })
    .click()
  await expect(page.getByRole("heading", { name: "История изменений" })).toBeVisible({
    timeout: 20_000,
  })

  await page
    .getByRole("navigation", { name: "Дополнительно" })
    .getByRole("link", { name: "Источники", exact: true })
    .click()
  const sourcesPanel = page.getByRole("heading", { name: "Источники вопросов" })
  if (await sourcesPanel.isVisible({ timeout: 5_000 }).catch(() => false)) {
    await expect(
      page.getByRole("button", { name: /Показать (текст|фрагмент)/ }).first()
    ).toBeVisible()
  }

  const editUrl = page.url()
  const quizId = editUrl.match(/\/edit\/([^/?#]+)/)?.[1]
  expect(quizId).toBeTruthy()

  await page.goto(`/student/${quizId}`)
  await page.getByPlaceholder("Например: Иван").fill("Jury Demo Student")
  await page.getByRole("button", { name: "Начать" }).click()

  await answerMockQuestion(page, 0)
  await answerMockQuestion(page, 1)

  await expect(page.getByText(/Результат:/)).toBeVisible({ timeout: 20_000 })

  await page.goto(`/results/${quizId}`)
  await expect(page.getByRole("heading", { name: /Результаты:/ })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Сводка класса" })).toBeVisible()
  await expect(page.getByText("Jury Demo Student")).toBeVisible()

  await page.goto(`/teacher/${quizId}`)
  await expect(page.getByRole("heading", { name: "Режим учителя" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Fullscreen" })).toBeVisible()
  await expect(page.getByRole("button", { name: "Показать ответ" })).toBeVisible()
})
