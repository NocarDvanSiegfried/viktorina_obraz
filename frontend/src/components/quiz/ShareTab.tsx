import { Link } from "react-router-dom"

import { Button } from "@/components/ui/Button"

type ShareTabProps = {
  quizId: string
  studentLink: string
  copyStatus: string
  onCopyStudentLink: () => void
  onCopyResultsLink: () => void
  onDownloadPdf: () => void
  onDownloadDocx: () => void
  onDownloadPptx: () => void
  onDownloadPptxClassroom: () => void
}

export function ShareTab({
  quizId,
  studentLink,
  copyStatus,
  onCopyStudentLink,
  onCopyResultsLink,
  onDownloadPdf,
  onDownloadDocx,
  onDownloadPptx,
  onDownloadPptxClassroom,
}: ShareTabProps) {
  return (
    <section className="result share-tab">
      <h2>Поделиться</h2>
      <p className="subtitle">Отправьте ссылку ученикам или скачайте материалы для класса.</p>

      <div className="share-primary-block">
        <h3 className="share-block-title">Ссылка для учеников</h3>
        <Button type="button" onClick={onCopyStudentLink}>
          Скопировать ссылку ученику
        </Button>
        {copyStatus && <p className="share-copy-status">{copyStatus}</p>}
        <p className="subtitle share-link-preview">{studentLink}</p>
        <Link to={`/student/${quizId}`} className="share-secondary-link">
          Открыть как ученик →
        </Link>
      </div>

      <div className="share-secondary-block">
        <h3 className="share-block-title">Дополнительно</h3>
        <div className="link-row share-links-row">
          <Link to={`/results/${quizId}`}>Открыть результаты →</Link>
          <button
            type="button"
            onClick={onCopyResultsLink}
            className="copy-button btn btn-ghost"
          >
            Копировать ссылку на результаты
          </button>
        </div>
        <div className="link-row">
          <Link to={`/teacher/${quizId}`}>Режим учителя →</Link>
        </div>
        <div className="link-row share-export-row">
          <Button type="button" variant="secondary" onClick={onDownloadPdf}>
            Скачать PDF
          </Button>
          <Button type="button" variant="secondary" onClick={onDownloadDocx}>
            Скачать DOCX
          </Button>
          <Button type="button" variant="secondary" onClick={onDownloadPptx}>
            Скачать PPTX
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={onDownloadPptxClassroom}
          >
            PPTX для класса (без ответов)
          </Button>
        </div>
      </div>
    </section>
  )
}
