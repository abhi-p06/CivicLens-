import React, { useEffect, useState, useRef } from 'react'
import { motion, useSpring, useMotionValue } from 'framer-motion'
import { useCivicMotion } from '../../lib/motionContext'

export interface TargetCursorProps {
  targetSelector?: string
  color?: string
  activeColor?: string
  size?: number
}

/**
 * React Bits Target Cursor Component
 * Refined precision reticle cursor tracking mouse position fluidly without
 * heavy bounding box overlays or React state re-rendering on mousemove.
 * Gracefully degrades on touch and reduced motion. Does not block pointer events.
 */
export const TargetCursor: React.FC<TargetCursorProps> = ({
  targetSelector = 'button, a, [data-cursor-target], [role="button"], [role="tab"], .cursor-interactive, .cursor-target',
  color = '#6457E8',
  activeColor = '#8B5CF6',
  size = 22,
}) => {
  const { isReduced } = useCivicMotion()
  const [mounted, setMounted] = useState(false)
  const [isTouch, setIsTouch] = useState(false)

  // Motion values for smooth cursor tracking without React state re-renders
  const mouseX = useMotionValue(-100)
  const mouseY = useMotionValue(-100)
  const cursorOpacity = useMotionValue(0)
  const targetScale = useMotionValue(1)

  // Spring physics: responsive and well-damped, avoiding oscillation or overshoot
  const springX = useSpring(mouseX, { stiffness: 480, damping: 36 })
  const springY = useSpring(mouseY, { stiffness: 480, damping: 36 })
  const springScale = useSpring(targetScale, { stiffness: 400, damping: 30 })
  const springOpacity = useSpring(cursorOpacity, { stiffness: 350, damping: 28 })

  const isInteractiveRef = useRef(false)

  useEffect(() => {
    setMounted(true)
    if (typeof window !== 'undefined') {
      const touchQuery = window.matchMedia('(pointer: coarse)')
      setIsTouch(touchQuery.matches)
      const handleTouchChange = (e: MediaQueryListEvent) => setIsTouch(e.matches)
      touchQuery.addEventListener?.('change', handleTouchChange)
      return () => touchQuery.removeEventListener?.('change', handleTouchChange)
    }
  }, [])

  useEffect(() => {
    if (!mounted || isTouch || isReduced) return

    const handleMouseMove = (e: MouseEvent) => {
      mouseX.set(e.clientX)
      mouseY.set(e.clientY)

      // Exclude text inputs, textareas, map canvas, and drag controls
      const target = e.target as HTMLElement | null
      if (
        !target ||
        target.closest('input') ||
        target.closest('textarea') ||
        target.closest('[contenteditable="true"]') ||
        target.closest('.leaflet-container') ||
        target.closest('.leaflet-control') ||
        target.closest('[data-exclude-cursor]')
      ) {
        cursorOpacity.set(0)
        targetScale.set(1)
        isInteractiveRef.current = false
        return
      }

      cursorOpacity.set(1)

      // Check if hovering over an intentional interactive element
      const interactiveEl = target.closest(targetSelector) as HTMLElement | null
      if (interactiveEl && !interactiveEl.hasAttribute('disabled')) {
        if (!isInteractiveRef.current) {
          isInteractiveRef.current = true
          targetScale.set(1.4)
        }
      } else {
        if (isInteractiveRef.current) {
          isInteractiveRef.current = false
          targetScale.set(1.0)
        }
      }
    }

    const handleMouseLeave = () => {
      cursorOpacity.set(0)
      targetScale.set(1)
      isInteractiveRef.current = false
    }

    const handleMouseEnter = () => {
      cursorOpacity.set(1)
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    document.addEventListener('mouseleave', handleMouseLeave)
    document.addEventListener('mouseenter', handleMouseEnter)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseleave', handleMouseLeave)
      document.removeEventListener('mouseenter', handleMouseEnter)
    }
  }, [mounted, isTouch, isReduced, targetSelector, mouseX, mouseY, cursorOpacity, targetScale])

  if (!mounted || isTouch || isReduced) return null

  return (
    <div className="pointer-events-none fixed inset-0 z-[9990] overflow-hidden select-none">
      <motion.div
        style={{
          x: springX,
          y: springY,
          scale: springScale,
          opacity: springOpacity,
          translateX: '-50%',
          translateY: '-50%',
        }}
        className="absolute pointer-events-none flex items-center justify-center will-change-transform"
      >
        {/* Subtle, restrained reticle ring */}
        <div
          className="rounded-full flex items-center justify-center transition-colors duration-150"
          style={{
            width: size,
            height: size,
            border: `1.5px solid ${color}66`,
            backgroundColor: `${color}10`,
            boxShadow: `0 0 10px ${color}22`,
          }}
        >
          {/* Inner focus dot */}
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: color }}
          />
        </div>
      </motion.div>
    </div>
  )
}

export default TargetCursor
