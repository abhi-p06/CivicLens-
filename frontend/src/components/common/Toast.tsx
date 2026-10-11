import React, { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import { Portal } from './Portal'

export type ToastType = 'success' | 'error' | 'info'

export interface ToastMessage {
  id: string
  type: ToastType
  title: string
  description?: string
}

interface ToastContextType {
  showToast: (title: string, description?: string, type?: ToastType) => void
  success: (title: string, description?: string) => void
  error: (title: string, description?: string) => void
  info: (title: string, description?: string) => void
}

const ToastContext = createContext<ToastContextType | undefined>(undefined)

export const useToast = () => {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error('useToast must be used within ToastProvider')
  }
  return ctx
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const showToast = useCallback(
    (title: string, description?: string, type: ToastType = 'info') => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
      setToasts((prev) => [...prev, { id, title, description, type }])
      setTimeout(() => {
        removeToast(id)
      }, 4000)
    },
    [removeToast]
  )

  const success = useCallback(
    (title: string, description?: string) => showToast(title, description, 'success'),
    [showToast]
  )
  const error = useCallback(
    (title: string, description?: string) => showToast(title, description, 'error'),
    [showToast]
  )
  const info = useCallback(
    (title: string, description?: string) => showToast(title, description, 'info'),
    [showToast]
  )

  return (
    <ToastContext.Provider value={{ showToast, success, error, info }}>
      {children}
      {/* Toast Notification Container in Top-Right */}
      <Portal>
        <div className="fixed top-20 right-6 z-[9999] layer-toast flex flex-col gap-2.5 max-w-sm pointer-events-none select-none font-sans">
          <AnimatePresence>
            {toasts.map((t) => (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 15, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
                className={cn(
                  'pointer-events-auto p-3 rounded-lg border shadow-2xl backdrop-blur-md flex items-start gap-3 bg-[#0d121c]/95',
                  t.type === 'success' && 'border-emerald-800 text-slate-100 shadow-emerald-950/40',
                  t.type === 'error' && 'border-rose-800 text-slate-100 shadow-rose-950/40',
                  t.type === 'info' && 'border-cyan-800 text-slate-100 shadow-cyan-950/40'
                )}
              >
                <div className="shrink-0 mt-0.5">
                  {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  {t.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-400" />}
                  {t.type === 'info' && <Info className="w-4 h-4 text-cyan-400" />}
                </div>

                <div className="flex-1 space-y-0.5 min-w-0">
                  <div className="text-xs font-bold tracking-tight text-slate-100 truncate">
                    {t.title}
                  </div>
                  {t.description && (
                    <div className="text-[11px] text-slate-400 font-sans leading-relaxed">
                      {t.description}
                    </div>
                  )}
                </div>

                <button
                  onClick={() => removeToast(t.id)}
                  className="text-slate-500 hover:text-slate-300 p-0.5 shrink-0 transition"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </Portal>
    </ToastContext.Provider>
  )
}
