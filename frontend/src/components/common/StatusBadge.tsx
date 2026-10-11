import React from 'react'
import {
  Clock,
  CheckCircle2,
  Activity,
  AlertCircle,
  FileCheck,
  UserCheck,
  Copy,
  Sparkles,
} from 'lucide-react'
import { IssueStatus } from '../../types'
import { cn } from '../../lib/utils'

interface StatusBadgeProps {
  status: IssueStatus | string
  className?: string
  showDot?: boolean
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, showDot = true }) => {
  const norm = (status || '').toUpperCase()

  let label = norm
  let colorClasses = 'bg-slate-100 text-slate-700 border-slate-200'
  let dotColor = 'bg-slate-400'

  switch (norm) {
    case 'OPEN':
    case 'REPORTED':
      label = 'Open'
      colorClasses = 'bg-sky-50 text-sky-700 border-sky-200 font-medium'
      dotColor = 'bg-sky-500'
      break
    case 'ANALYZED':
    case 'TRIAGED':
      label = 'Analyzed'
      colorClasses = 'bg-[#F0F2F9] text-[#6457E8] border-[#E4E7F1] font-medium'
      dotColor = 'bg-[#6457E8]'
      break
    case 'PRIORITIZED':
      label = 'Prioritized'
      colorClasses = 'bg-amber-50 text-amber-800 border-amber-200 font-medium'
      dotColor = 'bg-amber-500'
      break
    case 'ASSIGNED':
      label = 'Assigned'
      colorClasses = 'bg-blue-50 text-blue-800 border-blue-200 font-medium'
      dotColor = 'bg-blue-500'
      break
    case 'ACTION IN PROGRESS':
    case 'IN_PROGRESS':
      label = 'In Progress'
      colorClasses = 'bg-purple-50 text-purple-800 border-purple-200 font-medium'
      dotColor = 'bg-purple-500'
      break
    case 'VERIFICATION':
      label = 'Verification'
      colorClasses = 'bg-indigo-50 text-indigo-800 border-indigo-200 font-medium'
      dotColor = 'bg-indigo-500'
      break
    case 'RESOLVED':
      label = 'Resolved'
      colorClasses = 'bg-emerald-50 text-emerald-800 border-emerald-200 font-medium'
      dotColor = 'bg-emerald-500'
      break
    case 'DUPLICATE':
      label = 'Duplicate'
      colorClasses = 'bg-slate-100 text-slate-700 border-slate-200 font-medium'
      dotColor = 'bg-slate-400'
      break
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border shrink-0',
        colorClasses,
        className
      )}
    >
      {showDot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColor)} />}
      <span>{label}</span>
    </span>
  )
}

export default StatusBadge
