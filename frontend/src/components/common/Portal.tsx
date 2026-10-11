import React, { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'

interface PortalProps {
  children: React.ReactNode
}

/**
 * Universal Portal component that mounts children directly into document.body.
 * Guarantees that overlays, modals, and backdrops escape all parent stacking contexts,
 * transforms, and overflow boundaries.
 */
export const Portal: React.FC<PortalProps> = ({ children }) => {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted || typeof document === 'undefined') {
    return null
  }

  return createPortal(children, document.body)
}

export default Portal
