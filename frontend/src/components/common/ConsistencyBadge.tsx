import React from 'react'
import { ConsistencyLevel } from '../../types'
import { cn } from '../../lib/utils'
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react'

interface ConsistencyBadgeProps {
  level: ConsistencyLevel | string
  score?: number
  className?: string
  showIcon?: boolean
}

export const ConsistencyBadge: React.FC<ConsistencyBadgeProps> = ({
  level,
  score,
  className,
  showIcon = true,
}) => {
  const norm = (level || '').toUpperCase()

  let colorClasses = 'bg-slate-900/80 text-slate-300 border-slate-700'
  let Icon = HelpCircle

  if (norm.includes('CONSISTENT') && !norm.includes('PARTIAL') && !norm.includes('INCONSISTENT')) {
    colorClasses = 'bg-emerald-950/60 text-emerald-300 border-emerald-800'
    Icon = CheckCircle2
  } else if (norm.includes('PARTIAL')) {
    colorClasses = 'bg-amber-950/60 text-amber-300 border-amber-800'
    Icon = AlertTriangle
  } else if (norm.includes('INCONSISTENT')) {
    colorClasses = 'bg-rose-950/60 text-rose-300 border-rose-800'
    Icon = AlertCircle
  } else if (norm.includes('MANUAL') || norm.includes('REVIEW')) {
    colorClasses = 'bg-cyan-950/60 text-cyan-300 border-cyan-800'
    Icon = HelpCircle
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] font-mono font-medium border tracking-wide uppercase',
        colorClasses,
        className
      )}
    >
      {showIcon && <Icon className="w-3 h-3 shrink-0" />}
      <span>{norm}</span>
      {score !== undefined && (
        <span className="opacity-80 text-[9px]">({(score * 100).toFixed(0)}%)</span>
      )}
    </span>
  )
}
