type ErrorAlertProps = {
  message: string
}

export function ErrorAlert({ message }: ErrorAlertProps) {
  if (!message.trim()) {
    return null
  }

  return (
    <div className="error-alert" role="alert">
      {message}
    </div>
  )
}
