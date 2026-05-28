import { expect, test, type Page } from "@playwright/test"

import { createQuizViaUi } from "../helpers/createQuiz"

const OWNER_ID = "e2e00000-0000-4000-8000-000000000001"

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

test("create → edit → student → results → PDF", async ({ page }) => {
  await createQuizViaUi(page, { topic: "Клетка", questionCount: 3 })

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()

  const editUrl = page.url()
  const quizId = editUrl.match(/\/edit\/([^/?#]+)/)?.[1]
  expect(quizId).toBeTruthy()

  await page
    .getByRole("navigation", { name: "Разделы викторины" })
    .getByRole("link", { name: "Быстрый просмотр", exact: true })
    .click()
  const downloadPromise = page.waitForEvent("download")
  await page.getByRole("button", { name: "Скачать PDF" }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename().toLowerCase()).toMatch(/\.pdf$/)

  await page.goto(`/student/${quizId}`)
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible()
  await expect(page.getByText(/quiz_id|owner_id|result_id/i)).toHaveCount(0)
  await expect(page.getByRole("link", { name: /назад/i })).toHaveCount(0)
  await page.getByPlaceholder("Например: Иван").fill("E2E Student")
  await page.getByRole("button", { name: "Начать" }).click()
  await expect(page.getByText("Осталось времени:", { exact: false })).toHaveCount(0)

  await answerMockQuestion(page, 0)
  await answerMockQuestion(page, 1)

  await expect(page.getByText(/Результат:/)).toBeVisible({ timeout: 20_000 })

  await page.goto(`/results/${quizId}`)
  await expect(page.getByRole("heading", { name: /Результаты:/ })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Сводка класса" })).toBeVisible()
  await expect(page.getByText("E2E Student")).toBeVisible()
  await expect(
    page
      .locator(".results-summary, .results-hardest, .results-attempts-section")
      .getByText(/quiz_id|owner_id|result_id/i)
  ).toHaveCount(0)
})
