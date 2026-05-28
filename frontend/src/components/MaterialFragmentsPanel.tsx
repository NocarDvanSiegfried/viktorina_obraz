import { useState } from "react"

import {
  formatFragmentPreviewLine,
  formatSourceLine,
  type SourceFragmentCatalogItem,
} from "@/lib/sourceFragment"

type MaterialFragmentsPanelProps = {
  fragments: SourceFragmentCatalogItem[]
}

export function MaterialFragmentsPanel({ fragments }: MaterialFragmentsPanelProps) {
  const [openId, setOpenId] = useState<string | null>(null)

  if (!fragments.length) {
    return null
  }

  return (
    <section className="material-fragments-panel">
      <h3>Источники вопросов</h3>
      <p className="subtitle">
        На чём основаны вопросы этой викторины — фрагменты загруженного материала.
      </p>
      <ul className="fragment-catalog-list">
        {fragments.map((fragment) => {
          const expanded = openId === fragment.id
          const preview = fragment.preview?.trim() ?? ""
          const hasPreview = Boolean(preview)
          const previewLine = formatFragmentPreviewLine(preview)
          return (
            <li key={fragment.id} className="fragment-catalog-item">
              <div className="fragment-catalog-item-header">
                <div className="fragment-catalog-labels">
                  <strong>{formatSourceLine(fragment.source_type, fragment.id)}</strong>
                  {previewLine && !expanded && (
                    <p className="fragment-preview-line">{previewLine}</p>
                  )}
                </div>
                {hasPreview && (
                  <button
                    type="button"
                    className="source-fragment-toggle"
                    onClick={() => setOpenId(expanded ? null : fragment.id)}
                    aria-expanded={expanded}
                  >
                    {expanded ? "Свернуть" : "Показать фрагмент"}
                  </button>
                )}
              </div>
              {hasPreview && expanded && (
                <blockquote className="source-fragment-preview">{preview}</blockquote>
              )}
              {!hasPreview && (
                <p className="source-fragment-empty">
                  Текст фрагмента недоступен (викторина создана до сохранения preview).
                </p>
              )}
              <details className="fragment-debug-details">
                <summary>Для отладки</summary>
                <code className="source-fragment-id">{fragment.id}</code>
              </details>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
