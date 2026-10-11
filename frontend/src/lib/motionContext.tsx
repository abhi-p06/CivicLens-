import React, { createContext, useContext, useState, useEffect } from 'react'

export type MotionMode = 'full' | 'reduced' | 'system'

interface MotionContextValue {
  motionMode: MotionMode
  setMotionMode: (mode: MotionMode) => void
  isReduced: boolean
  toggleMotionMode: () => void
}

const MotionContext = createContext<MotionContextValue>({
  motionMode: 'full',
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
    // Default to 'full' for presentation-grade animated experience
    return 'full'
  })

  const [systemReduced, setSystemReduced] = useState<boolean>(() => {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    }
    return false
  })

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handler = (e: MediaQueryListEvent) => setSystemReduced(e.matches)
    mq.addEventListener?.('change', handler)
    return () => mq.removeEventListener?.('change', handler)
  }, [])

  const setMotionMode = (mode: MotionMode) => {
    setMotionModeState(mode)
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, mode)
    }
  }

  const toggleMotionMode = () => {
    if (motionMode === 'full') setMotionMode('system')
    else if (motionMode === 'system') setMotionMode('reduced')
    else setMotionMode('full')
  }

  const isReduced = motionMode === 'reduced' || (motionMode === 'system' && systemReduced)

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
