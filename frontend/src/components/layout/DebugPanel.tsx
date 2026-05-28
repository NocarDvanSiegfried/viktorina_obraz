type DebugPanelProps = {
  ownerId: string
  quizId?: string
}

/** Collapsed technical IDs — only for support/debug, not for teachers. */
export function DebugPanel({ ownerId, quizId }: DebugPanelProps) {
  return (
    <details className="debug-panel">
      <summary>Для отладки</summary>
      <dl className="debug-panel-list">
        <div>
          <dt>owner_id</dt>
          <dd>{ownerId}</dd>
        </div>
        {quizId && (
          <div>
            <dt>quiz_id</dt>
            <dd>{quizId}</dd>
          </div>
        )}
      </dl>
    </details>
  )
}
