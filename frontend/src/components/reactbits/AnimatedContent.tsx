import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { useCivicMotion } from '../../lib/motionContext'

export interface AnimatedContentProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  distance?: number
  direction?: 'vertical' | 'horizontal'
  reverse?: boolean
  duration?: number
  delay?: number
  scale?: number
  initialOpacity?: number
  className?: string
}

/**
 * React Bits Animated Content Component
 * Choreographed directional entrance with configurable scale, distance, and opacity.
 */
export const AnimatedContent: React.FC<AnimatedContentProps> = ({
  children,
  distance = 24,
  direction = 'vertical',
  reverse = false,
  duration = 0.55,
  delay = 0,
  scale = 1,
  initialOpacity = 0,
  className,
  ...props
}) => {
  const { isReduced } = useCivicMotion()

  if (isReduced) {
    return <div className={className}>{children}</div>
  }

  const offset = reverse ? -distance : distance
  const initialX = direction === 'horizontal' ? offset : 0
  const initialY = direction === 'vertical' ? offset : 0

  return (
    <motion.div
      initial={{
        opacity: initialOpacity,
        x: initialX,
        y: initialY,
        scale: scale !== 1 ? scale : 1,
      }}
      animate={{
        opacity: 1,
        x: 0,
        y: 0,
        scale: 1,
      }}
      transition={{
        duration,
        delay,
        ease: [0.16, 1, 0.3, 1], // Apple / Linear crisp ease-out
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default AnimatedContent
