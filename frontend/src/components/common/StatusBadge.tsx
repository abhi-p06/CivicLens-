import React from 'react'
import { IssueStatus } from '../../types'
import { cn } from '../../lib/utils'

interface StatusBadgeProps {
  status: IssueStatus | string
  className?: string
  showDot?: boolean
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className, showDot = true }) => {
  const norm = (status || '').toUpperCase()

  let colorClasses = 'bg-slate-800/80 text-slate-300 border-slate-700'
  let dotColor = 'bg-slate-400'

  switch (norm) {
    case 'OPEN':
    case 'REPORTED':
      colorClasses = 'bg-sky-950/60 text-sky-300 border-sky-800/70'
      dotColor = 'bg-sky-400'
      break
    case 'ANALYZED':
    case 'TRIAGED':
      colorClasses = 'bg-cyan-950/60 text-cyan-300 border-cyan-800/70'
      dotColor = 'bg-cyan-400'
      break
    case 'PRIORITIZED':
      colorClasses = 'bg-amber-950/60 text-amber-300 border-amber-800/70'
      dotColor = 'bg-amber-400'
      break
    case 'ASSIGNED':
      colorClasses = 'bg-blue-950/60 text-blue-300 border-blue-800/70'
      dotColor = 'bg-blue-400'
      break
    case 'ACTION IN PROGRESS':
    case 'IN_PROGRESS':
      colorClasses = 'bg-purple-950/60 text-purple-300 border-purple-800/70'
      dotColor = 'bg-purple-400 animate-pulse'
      break
    case 'VERIFICATION':
      colorClasses = 'bg-indigo-950/60 text-indigo-300 border-indigo-800/70'
      dotColor = 'bg-indigo-400 animate-pulse'
      break
    case 'RESOLVED':
      colorClasses = 'bg-emerald-950/60 text-emerald-300 border-emerald-800/70'
      dotColor = 'bg-emerald-400'
      break
    case 'DUPLICATE':
      colorClasses = 'bg-zinc-800/70 text-zinc-400 border-zinc-700'
      dotColor = 'bg-zinc-500'
      break
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[11px] font-medium tracking-wide uppercase font-mono border backdrop-blur-sm',
        colorClasses,
        className
      )}
    >
      {showDot && <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColor)} />}
      <span>{norm}</span>
    </span>
  )
}
