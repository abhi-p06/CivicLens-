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
 * Subtle unblur and opacity reveal for page transitions and card updates
 */
export const FadeContent: React.FC<FadeContentProps> = ({
  children,
  blur = true,
  duration = 0.45,
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
        filter: blur ? 'blur(6px)' : 'none',
      }}
      animate={{
        opacity: 1,
        filter: 'blur(0px)',
      }}
      exit={{
        opacity: 0,
        filter: blur ? 'blur(4px)' : 'none',
      }}
      transition={{
        duration,
        delay,
        ease: 'easeOut',
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default FadeContent
