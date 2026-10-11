import React, { useEffect, useRef, useState } from 'react'
import { useCivicMotion } from '../../lib/motionContext'

export interface CountUpProps {
  from?: number
  to: number
  duration?: number // in seconds
  delay?: number // in seconds
  decimals?: number
  separator?: string
  prefix?: string
  suffix?: string
  className?: string
  onEnd?: () => void
}

/**
 * React Bits Count Up Component
 * Smooth, lightweight, high-performance numerical counter with easing
 */
export const CountUp: React.FC<CountUpProps> = ({
  from = 0,
  to,
  duration = 1.2,
  delay = 0,
  decimals = 0,
  separator = ',',
  prefix = '',
  suffix = '',
  className,
  onEnd,
}) => {
  const { isReduced } = useCivicMotion()
  const [value, setValue] = useState(from)
  const previousToRef = useRef(from)
  const isFirstRender = useRef(true)

  useEffect(() => {
    if (isReduced) {
      setValue(to)
      previousToRef.current = to
      onEnd?.()
      return
    }

    const startValue = isFirstRender.current ? from : previousToRef.current
    isFirstRender.current = false
    const endValue = to
    previousToRef.current = to

    if (startValue === endValue && endValue !== 0) {
      setValue(endValue)
      return
    }

    let animationFrameId: number
    let timeoutId: ReturnType<typeof setTimeout>

    const startAnimation = () => {
      let startTime: number | null = null
      const durationMs = duration * 1000

      const step = (timestamp: number) => {
        if (!startTime) startTime = timestamp
        const progress = Math.min((timestamp - startTime) / durationMs, 1)

        // Ease-out cubic curve: 1 - (1 - progress)^3
        const easeOut = 1 - Math.pow(1 - progress, 3)
        const current = startValue + (endValue - startValue) * easeOut

        setValue(current)

        if (progress < 1) {
          animationFrameId = window.requestAnimationFrame(step)
        } else {
          setValue(endValue)
          onEnd?.()
        }
      }

      animationFrameId = window.requestAnimationFrame(step)
    }

    if (delay > 0) {
      timeoutId = setTimeout(startAnimation, delay * 1000)
    } else {
      startAnimation()
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId)
      if (animationFrameId) window.cancelAnimationFrame(animationFrameId)
    }
  }, [to, from, duration, delay, isReduced, onEnd])

  const formatNumber = (num: number) => {
    const fixed = num.toFixed(decimals)
    const [intPart, decPart] = fixed.split('.')
    const formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, separator)
    return decPart !== undefined ? `${formattedInt}.${decPart}` : formattedInt
  }

  return (
    <span className={className}>
      {prefix}
      {formatNumber(value)}
      {suffix}
    </span>
  )
}

export default CountUp
