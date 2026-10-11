import React, { useRef, useState, useCallback } from 'react'
import { motion, useMotionTemplate, useMotionValue } from 'framer-motion'
import { cn } from '../../lib/utils'

export interface CardSpotlightProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  radius?: number
  color?: string
  className?: string
}

/**
 * Aceternity UI Card Spotlight Component
 * Applied selectively to one featured risk / intelligence element
 * Projects a smooth radial spotlight tracking the user's cursor.
 */
export const CardSpotlight: React.FC<CardSpotlightProps> = ({
  children,
  radius = 280,
  color = '#6457E8', // Aurora Indigo focus accent
  className,
  ...props
}) => {
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseMove = useCallback(
    ({ currentTarget, clientX, clientY }: React.MouseEvent<HTMLDivElement>) => {
      const { left, top } = currentTarget.getBoundingClientRect()
      mouseX.set(clientX - left)
      mouseY.set(clientY - top)
    },
    [mouseX, mouseY]
  )

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true)
  }, [])

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false)
  }, [])

  return (
    <div
      className={cn(
        'group relative overflow-hidden rounded-2xl border border-[#E4E7F1] bg-white p-6 transition-all duration-300 shadow-xs hover:shadow-md',
        className
      )}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      {...props}
    >
      {/* Background Spotlight Layer */}
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate`
            radial-gradient(
              ${radius}px circle at ${mouseX}px ${mouseY}px,
              rgba(100, 87, 232, 0.09),
              transparent 80%
            )
          `,
        }}
      />

      {/* Subtle border highlight on spotlight proximity */}
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate`
            radial-gradient(
              ${radius * 0.7}px circle at ${mouseX}px ${mouseY}px,
              rgba(139, 92, 246, 0.35),
              transparent 70%
            )
          `,
          maskImage: 'linear-gradient(black, black)',
          WebkitMaskImage: 'linear-gradient(black, black)',
          maskComposite: 'exclude',
          WebkitMaskComposite: 'xor',
          padding: '1px',
        }}
      />

      {/* Card Content */}
      <div className="relative z-10">{children}</div>
    </div>
  )
}

export default CardSpotlight
