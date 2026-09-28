import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { IconCheck, IconX, IconAlertTriangle } from '@tabler/icons-react'

const ToastContext = createContext(null)
let idSeq = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const timers = useRef({})

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id))
    clearTimeout(timers.current[id])
    delete timers.current[id]
  }, [])

  const push = useCallback((message, type = 'info', duration = 4200) => {
    const id = ++idSeq
    setToasts((t) => [...t, { id, message, type }])
    timers.current[id] = setTimeout(() => dismiss(id), duration)
    return id
  }, [dismiss])

  const toast = {
    success: (msg) => push(msg, 'success'),
    error: (msg) => push(msg, 'error', 6000),
    info: (msg) => push(msg, 'info'),
  }

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="fixed top-4 right-4 z-[1000] flex flex-col gap-2 w-[calc(100%-2rem)] max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="animate-slide-in-right bg-ink text-page rounded-xl shadow-panel border border-ink-line px-4 py-3 flex items-start gap-2.5 text-[12.5px]"
          >
            <div
              className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                t.type === 'success' ? 'bg-malachite-bright/20 text-malachite-bright'
                : t.type === 'error' ? 'bg-garnet-bright/20 text-garnet-bright'
                : 'bg-gold/20 text-gold'
              }`}
            >
              {t.type === 'success' ? <IconCheck size={12} /> : t.type === 'error' ? <IconAlertTriangle size={12} /> : <IconCheck size={12} />}
            </div>
            <div className="flex-1 leading-snug pt-0.5">{t.message}</div>
            <button onClick={() => dismiss(t.id)} className="text-[#8FA095] hover:text-page transition-colors flex-shrink-0">
              <IconX size={13} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
