import { useState } from "react"

import {
  formatSourceTypeLabel,
  type SourceFragmentCatalogItem,
} from "@/lib/sourceFragment"

type SourceFragmentBadgeProps = {
  fragmentId: string
  catalog?: SourceFragmentCatalogItem[]
}

export function SourceFragmentBadge({ fragmentId, catalog }: SourceFragmentBadgeProps) {
  const [expanded, setExpanded] = useState(false)
  const trimmedId = fragmentId.trim()
  if (!trimmedId) {
    return null
  }

  const entry = catalog?.find((item) => item.id === trimmedId)
  const preview = entry?.preview?.trim() ?? ""
  const sourceLabel = formatSourceTypeLabel(entry?.source_type, trimmedId)

  return (
    <div className="source-fragment-badge">
      <div className="source-fragment-badge-header">
        <span className="source-fragment-badge-label">Из материала</span>
        <span className="source-fragment-badge-type">{sourceLabel}</span>
        {preview && (
          <button
            type="button"
            className="source-fragment-toggle"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
          >
            {expanded ? "Скрыть фрагмент" : "Показать фрагмент"}
          </button>
        )}
      </div>
      {preview && expanded && (
        <blockquote className="source-fragment-preview">{preview}</blockquote>
      )}
      {!preview && (
        <p className="source-fragment-empty">
          Текст фрагмента недоступен (викторина создана до сохранения preview).
        </p>
      )}
      <details className="fragment-debug-details">
        <summary>Для отладки</summary>
        <code className="source-fragment-id">{trimmedId}</code>
      </details>
    </div>
  )
}
