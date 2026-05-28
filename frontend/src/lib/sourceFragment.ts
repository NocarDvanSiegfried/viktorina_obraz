export type SourceFragmentCatalogItem = {
  id: string
  preview: string
  source_type: string
}

const SOURCE_TYPE_LABELS: Record<string, string> = {
  manual_text: "Текст учителя",
  txt: "TXT",
  pdf: "PDF",
  docx: "DOCX",
  pptx: "PPTX",
  image: "Изображение (OCR)",
  unknown: "Материал",
}

export function formatSourceTypeLabel(
  sourceType?: string,
  fragmentId?: string
): string {
  const typeKey = (sourceType || inferSourceTypeFromId(fragmentId ?? "")).trim()
  return SOURCE_TYPE_LABELS[typeKey] ?? SOURCE_TYPE_LABELS.unknown
}

/** `Источник: PDF` */
export function formatSourceLine(
  sourceType?: string,
  fragmentId?: string
): string {
  return `Источник: ${formatSourceTypeLabel(sourceType, fragmentId)}`
}

function truncatePreview(text: string, maxLen = 120): string {
  const trimmed = text.trim()
  if (trimmed.length <= maxLen) return trimmed
  return `${trimmed.slice(0, maxLen)}…`
}

/** Collapsed one-line fragment preview for list cards. */
export function formatFragmentPreviewLine(preview: string): string {
  const trimmed = preview.trim()
  if (!trimmed) return ""
  return `Фрагмент: «${truncatePreview(trimmed)}»`
}

/** @deprecated Prefer formatSourceLine — kept for badge fallback. */
export function formatSourceFragmentLabel(
  fragmentId: string,
  sourceType?: string
): string {
  return formatSourceLine(sourceType, fragmentId)
}

function inferSourceTypeFromId(fragmentId: string): string {
  if (fragmentId.startsWith("image_ocr_")) return "image"
  if (fragmentId.startsWith("pdf_ocr_") || fragmentId.startsWith("pdf_page_")) {
    return "pdf"
  }
  if (fragmentId.startsWith("docx_chunk_")) return "docx"
  if (fragmentId.startsWith("pptx_slide_")) return "pptx"
  if (fragmentId.startsWith("txt_")) return "txt"
  if (fragmentId === "manual_1" || fragmentId.startsWith("manual_")) {
    return "manual_text"
  }
  return "unknown"
}