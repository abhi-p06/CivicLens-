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

  let colorClasses = 'bg-slate-900 text-slate-300 border-slate-700'
  let dotColor = 'bg-slate-400'
  let IconComponent = Clock

  switch (norm) {
    case 'OPEN':
    case 'REPORTED':
      colorClasses = 'bg-sky-950/80 text-sky-200 border-sky-700/80'
      dotColor = 'bg-sky-400'
      IconComponent = AlertCircle
      break
    case 'ANALYZED':
    case 'TRIAGED':
      colorClasses = 'bg-cyan-950/80 text-cyan-200 border-cyan-700/80'
      dotColor = 'bg-cyan-400'
      IconComponent = Sparkles
      break
    case 'PRIORITIZED':
      colorClasses = 'bg-amber-950/80 text-amber-200 border-amber-700/80'
      dotColor = 'bg-amber-400'
      IconComponent = Clock
      break
    case 'ASSIGNED':
      colorClasses = 'bg-blue-950/80 text-blue-200 border-blue-700/80'
      dotColor = 'bg-blue-400'
      IconComponent = UserCheck
      break
    case 'ACTION IN PROGRESS':
    case 'IN_PROGRESS':
      colorClasses = 'bg-purple-950/80 text-purple-200 border-purple-700/80'
      dotColor = 'bg-purple-400'
      IconComponent = Activity
      break
    case 'VERIFICATION':
      colorClasses = 'bg-indigo-950/80 text-indigo-200 border-indigo-700/80'
      dotColor = 'bg-indigo-400'
      IconComponent = FileCheck
      break
    case 'RESOLVED':
      colorClasses = 'bg-emerald-950/80 text-emerald-200 border-emerald-700/80'
      dotColor = 'bg-emerald-400'
      IconComponent = CheckCircle2
      break
    case 'DUPLICATE':
      colorClasses = 'bg-zinc-900 text-zinc-300 border-zinc-700'
      dotColor = 'bg-zinc-400'
      IconComponent = Copy
      break
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold tracking-wide font-mono border backdrop-blur-sm shadow-sm shrink-0',
        colorClasses,
        className
      )}
    >
      <IconComponent className="w-3 h-3 shrink-0" />
      {showDot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColor)} />}
      <span>{norm}</span>
    </span>
  )
}

export default StatusBadge
