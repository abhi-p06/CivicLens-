import React, { createContext, useContext, useState, useEffect } from 'react'

export type MotionMode = 'full' | 'reduced' | 'system'

interface MotionContextValue {
  motionMode: MotionMode
  setMotionMode: (mode: MotionMode) => void
  isReduced: boolean
  toggleMotionMode: () => void
}

const MotionContext = createContext<MotionContextValue>({
  motionMode: 'system',
  setMotionMode: () => {},
  isReduced: false,
  toggleMotionMode: () => {},
})

const STORAGE_KEY = 'civic_motion_preference'

export const MotionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [motionMode, setMotionModeState] = useState<MotionMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY) as MotionMode | null
      if (saved && (saved === 'full' || saved === 'reduced' || saved === 'system')) {
        return saved
      }
    }
    return 'system'
  })

  const [systemReduced, setSystemReduced] = useState<boolean>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }
    return false
  })

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = (e: MediaQueryListEvent) => setSystemReduced(e.matches)
    mediaQuery.addEventListener?.('change', handler)
    return () => mediaQuery.removeEventListener?.('change', handler)
  }, [])

  const setMotionMode = (mode: MotionMode) => {
    setMotionModeState(mode)
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, mode)
    }
  }

  const isReduced = motionMode === 'reduced' || (motionMode === 'system' && systemReduced)

  const toggleMotionMode = () => {
    const nextMode: MotionMode = isReduced ? 'full' : 'reduced'
    setMotionMode(nextMode)
  }

  return (
    <MotionContext.Provider
      value={{
        motionMode,
        setMotionMode,
        isReduced,
        toggleMotionMode,
      }}
    >
      {children}
    </MotionContext.Provider>
  )
}

export const useCivicMotion = () => useContext(MotionContext)

export default MotionProvider
