import React, { useEffect, useState } from 'react'

export const AnimatedCounter: React.FC<{
  value: number
  durationMs?: number
  suffix?: string
}> = ({ value, durationMs = 1000, suffix = '' }) => {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    let startTimestamp: number | null = null
    const startValue = 0
    const endValue = value

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / durationMs, 1)
      const easeOut = 1 - Math.pow(1 - progress, 3)
      const current = Math.floor(startValue + (endValue - startValue) * easeOut)
      setDisplayValue(current)
      if (progress < 1) {
        window.requestAnimationFrame(step)
      } else {
        setDisplayValue(endValue)
      }
    }

    const frameId = window.requestAnimationFrame(step)
    return () => window.cancelAnimationFrame(frameId)
  }, [value, durationMs])

  return (
    <span>
      {displayValue}
      {suffix}
    </span>
  )
}
