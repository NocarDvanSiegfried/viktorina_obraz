import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react"

type ToastVariant = "success" | "error" | "info"

type ToastItem = {
  id: number
  message: string
  variant: ToastVariant
}

type ToastContextValue = {
  showSuccess: (message: string) => void
  showError: (message: string) => void
  showInfo: (message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

const TOAST_DURATION_MS = 4000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const idRef = useRef(0)
  const timersRef = useRef<Map<number, number>>(new Map())

  const dismiss = useCallback((id: number) => {
    const timer = timersRef.current.get(id)
    if (timer) {
      window.clearTimeout(timer)
      timersRef.current.delete(id)
    }
    setItems((prev) => prev.filter((item) => item.id !== id))
  }, [])

  const show = useCallback(
    (message: string, variant: ToastVariant) => {
      const trimmed = message.trim()
      if (!trimmed) return

      const id = idRef.current + 1
      idRef.current = id

      setItems((prev) => [...prev, { id, message: trimmed, variant }].slice(-4))

      const timer = window.setTimeout(() => dismiss(id), TOAST_DURATION_MS)
      timersRef.current.set(id, timer)
    },
    [dismiss]
  )

  const value = useMemo<ToastContextValue>(
    () => ({
      showSuccess: (message) => show(message, "success"),
      showError: (message) => show(message, "error"),
      showInfo: (message) => show(message, "info"),
    }),
    [show]
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-viewport" role="region" aria-live="polite" aria-label="Уведомления">
        {items.map((item) => (
          <div
            key={item.id}
            className={`toast toast-${item.variant}`}
            role={item.variant === "error" ? "alert" : "status"}
          >
            <p className="toast-message">{item.message}</p>
            <button
              type="button"
              className="toast-close"
              aria-label="Закрыть"
              onClick={() => dismiss(item.id)}
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider")
  }
  return ctx
}
