import React, { useRef, useState } from 'react'
import { cn } from '../../lib/utils'

export interface GlareHoverProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  glareColor?: string
  glareSize?: number
  glareOpacity?: number
  className?: string
}

/**
 * React Bits Glare Hover Component
 * Smooth interactive cursor reflection glare
 */
export const GlareHover: React.FC<GlareHoverProps> = ({
  children,
  glareColor = 'rgba(8, 145, 178, 0.15)', // Refined teal reflection
  glareSize = 240,
  glareOpacity = 1,
  className,
  ...props
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState<{ x: number; y: number } | null>(null)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    setPosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    })
  }

  const handleMouseLeave = () => {
    setPosition(null)
  }

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn('relative overflow-hidden', className)}
      {...props}
    >
      {children}
      {position && (
        <div
          className="pointer-events-none absolute -inset-px transition-opacity duration-300"
          style={{
            opacity: glareOpacity,
            background: `radial-gradient(${glareSize}px circle at ${position.x}px ${position.y}px, ${glareColor}, transparent 80%)`,
          }}
        />
      )}
    </div>
  )
}

export default GlareHover
