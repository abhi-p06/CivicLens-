import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { useCivicMotion } from '../../lib/motionContext'

export interface FadeContentProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  blur?: boolean
  duration?: number
  delay?: number
  initialOpacity?: number
  className?: string
}

/**
 * React Bits Fade Content Component
 * Clean, GPU-friendly opacity & subtle transform reveal.
 * Avoids heavy full-element blur filters that cause rasterization stutter.
 */
export const FadeContent: React.FC<FadeContentProps> = ({
  children,
  blur = false,
  duration = 0.35,
  delay = 0,
  initialOpacity = 0,
  className,
  ...props
}) => {
  const { isReduced } = useCivicMotion()

  if (isReduced) {
    return <div className={className}>{children}</div>
  }

  return (
    <motion.div
      initial={{
        opacity: initialOpacity,
        y: 8,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      exit={{
        opacity: 0,
        y: -4,
      }}
      transition={{
        duration,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default FadeContent
