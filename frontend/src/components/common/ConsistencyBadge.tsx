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

  let label = 'Verified'
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 font-medium'
  let Icon = HelpCircle

  if (norm.includes('CONSISTENT') && !norm.includes('PARTIAL') && !norm.includes('INCONSISTENT')) {
    label = 'Vision Verified'
    colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200 font-medium'
    Icon = CheckCircle2
  } else if (norm.includes('PARTIAL')) {
    label = 'Partial Match'
    colorClasses = 'bg-amber-50 text-amber-800 border-amber-200 font-medium'
    Icon = AlertTriangle
  } else if (norm.includes('INCONSISTENT')) {
    label = 'Inconsistent'
    colorClasses = 'bg-rose-50 text-rose-800 border-rose-200 font-medium'
    Icon = AlertCircle
  } else if (norm.includes('MANUAL') || norm.includes('REVIEW')) {
    label = 'Review Needed'
    colorClasses = 'bg-[#F0F2F9] text-[#6457E8] border-[#E4E7F1] font-medium'
    Icon = HelpCircle
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border shrink-0',
        colorClasses,
        className
      )}
    >
      {showIcon && <Icon className="w-3.5 h-3.5 shrink-0" />}
      <span>{label}</span>
      {score !== undefined && (
        <span className="opacity-80 text-[11px] font-mono">({(score * 100).toFixed(0)}%)</span>
      )}
    </span>
  )
}

export default ConsistencyBadge
