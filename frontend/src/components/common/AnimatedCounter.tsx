import React, { useEffect, useState, useRef } from 'react'
import { useCivicMotion } from '../../lib/motionContext'

export const AnimatedCounter: React.FC<{
  value: number
  durationMs?: number
  delayMs?: number
  suffix?: string
}> = ({ value, durationMs = 750, delayMs = 0, suffix = '' }) => {
  const { isReduced } = useCivicMotion()
  const [displayValue, setDisplayValue] = useState(0)
  const prevValueRef = useRef<number>(0)
  const isFirstRender = useRef<boolean>(true)

  useEffect(() => {
    if (isReduced) {
      setDisplayValue(value)
      prevValueRef.current = value
      return
    }

    const startValue = isFirstRender.current ? 0 : prevValueRef.current
    isFirstRender.current = false
    const endValue = value
    prevValueRef.current = value

    if (startValue === endValue && endValue !== 0) {
      setDisplayValue(endValue)
      return
    }

    let frameId: number
    let timeoutId: ReturnType<typeof setTimeout>

    const startAnimation = () => {
      let startTimestamp: number | null = null
      const step = (timestamp: number) => {
        if (!startTimestamp) startTimestamp = timestamp
        const elapsed = timestamp - startTimestamp
        const progress = Math.min(elapsed / durationMs, 1)
        // Smooth easeOutCubic
        const easeOut = 1 - Math.pow(1 - progress, 3)
        const current = Math.round(startValue + (endValue - startValue) * easeOut)
        setDisplayValue(current)
        if (progress < 1) {
          frameId = window.requestAnimationFrame(step)
        } else {
          setDisplayValue(endValue)
        }
      }
      frameId = window.requestAnimationFrame(step)
    }

    if (delayMs > 0) {
      timeoutId = setTimeout(startAnimation, delayMs)
    } else {
      startAnimation()
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId)
      if (frameId) window.cancelAnimationFrame(frameId)
    }
  }, [value, durationMs, delayMs, isReduced])

  return (
    <span>
      {displayValue}
      {suffix}
    </span>
  )
}

export default AnimatedCounter
