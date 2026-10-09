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

  let colorClasses = 'bg-slate-900 text-slate-300 border-slate-700'
  let Icon = HelpCircle

  if (norm.includes('CONSISTENT') && !norm.includes('PARTIAL') && !norm.includes('INCONSISTENT')) {
    colorClasses = 'bg-emerald-950/80 text-emerald-200 border-emerald-700/80'
    Icon = CheckCircle2
  } else if (norm.includes('PARTIAL')) {
    colorClasses = 'bg-amber-950/80 text-amber-200 border-amber-700/80'
    Icon = AlertTriangle
  } else if (norm.includes('INCONSISTENT')) {
    colorClasses = 'bg-rose-950/80 text-rose-200 border-rose-700/80'
    Icon = AlertCircle
  } else if (norm.includes('MANUAL') || norm.includes('REVIEW')) {
    colorClasses = 'bg-cyan-950/80 text-cyan-200 border-cyan-700/80'
    Icon = HelpCircle
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold font-mono border tracking-wide uppercase shrink-0 shadow-sm',
        colorClasses,
        className
      )}
    >
      {showIcon && <Icon className="w-3.5 h-3.5 shrink-0" />}
      <span>{norm}</span>
      {score !== undefined && (
        <span className="opacity-90 text-[11px] font-bold">({(score * 100).toFixed(0)}%)</span>
      )}
    </span>
  )
}

export default ConsistencyBadge
