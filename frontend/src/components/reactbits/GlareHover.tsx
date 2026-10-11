import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '../../lib/utils'
import { useCivicMotion } from '../../lib/motionContext'

export interface GlareHoverProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  glareColor?: string
  glareSize?: number
  glareOpacity?: number
  className?: string
  disabled?: boolean
}

/**
 * React Bits Glare Hover Component
 * High-performance interactive card spotlight with restrained violet optics.
 * Directly updates DOM overlay in requestAnimationFrame to eliminate React re-renders.
 * Automatically integrates with Framer Motion props and Target Cursor detection.
 */
export const GlareHover = forwardRef<HTMLDivElement, GlareHoverProps>(
  (
    {
      children,
      glareColor = 'rgba(100, 87, 232, 0.12)', // Subtle Aurora Indigo spotlight
      glareSize = 280,
      glareOpacity = 1,
      className,
      disabled = false,
      ...props
    },
    forwardedRef
  ) => {
    const { isReduced } = useCivicMotion()
    const containerRef = useRef<HTMLDivElement>(null)
    const overlayRef = useRef<HTMLDivElement>(null)
    const rectRef = useRef<DOMRect | null>(null)
    const rafIdRef = useRef<number | null>(null)

    useImperativeHandle(forwardedRef, () => containerRef.current as HTMLDivElement)

    useEffect(() => {
      return () => {
        if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current)
      }
    }, [])

    const updatePosition = (clientX: number, clientY: number) => {
      if (!overlayRef.current || disabled) return
      if (!rectRef.current && containerRef.current) {
        rectRef.current = containerRef.current.getBoundingClientRect()
      }
      const rect = rectRef.current
      if (!rect) return

      const x = Math.round(clientX - rect.left)
      const y = Math.round(clientY - rect.top)

      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current)
      rafIdRef.current = requestAnimationFrame(() => {
        if (overlayRef.current) {
          overlayRef.current.style.background = `radial-gradient(${glareSize}px circle at ${x}px ${y}px, ${glareColor}, transparent 75%)`
        }
      })
    }

    const handlePointerEnter = (e: React.PointerEvent<HTMLDivElement>) => {
      props.onPointerEnter?.(e)
      if (isReduced || disabled || !containerRef.current) return
      rectRef.current = containerRef.current.getBoundingClientRect()
      if (overlayRef.current) {
        overlayRef.current.style.opacity = `${glareOpacity}`
      }
      updatePosition(e.clientX, e.clientY)
    }

    const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
      props.onPointerMove?.(e)
      if (isReduced || disabled) return
      updatePosition(e.clientX, e.clientY)
    }

    const handlePointerLeave = (e: React.PointerEvent<HTMLDivElement>) => {
      props.onPointerLeave?.(e)
      rectRef.current = null
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current)
        rafIdRef.current = null
      }
      if (overlayRef.current) {
        overlayRef.current.style.opacity = '0'
      }
    }

    return (
      <motion.div
        ref={containerRef}
        data-glare-card="true"
        data-cursor-target="true"
        onPointerEnter={handlePointerEnter}
        onPointerMove={handlePointerMove}
        onPointerLeave={handlePointerLeave}
        className={cn('relative overflow-hidden', className)}
        {...props}
      >
        {children}
        {!isReduced && !disabled && (
          <div
            ref={overlayRef}
            data-glare-overlay="true"
            className="pointer-events-none absolute inset-0 z-20 rounded-[inherit] overflow-hidden transition-opacity duration-200 ease-out"
            style={{
              opacity: 0,
            }}
          />
        )}
      </motion.div>
    )
  }
)

GlareHover.displayName = 'GlareHover'

export default GlareHover
