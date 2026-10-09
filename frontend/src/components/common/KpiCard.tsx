import React from 'react'
import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'

interface KpiCardProps {
  title: string
  value: React.ReactNode
  delta?: string
  deltaType?: 'positive' | 'negative' | 'neutral' | 'critical'
  icon?: LucideIcon
  subtitle?: string
  accentColor?: 'cyan' | 'green' | 'yellow' | 'orange' | 'red' | 'slate'
  className?: string
  onClick?: () => void
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  delta,
  deltaType = 'neutral',
  icon: Icon,
  subtitle,
  accentColor = 'slate',
  className,
  onClick,
}) => {
  let accentBorder = 'border-slate-800'
  let topHighlight = 'bg-slate-700/40'
  let iconColor = 'text-slate-400'

  if (accentColor === 'cyan') {
    accentBorder = 'border-cyan-900/40 hover:border-cyan-600/70'
    topHighlight = 'bg-cyan-500'
    iconColor = 'text-cyan-400'
  } else if (accentColor === 'red') {
    accentBorder = 'border-rose-900/40 hover:border-rose-600/70'
    topHighlight = 'bg-rose-500'
    iconColor = 'text-rose-400'
  } else if (accentColor === 'orange') {
    accentBorder = 'border-orange-900/40 hover:border-orange-600/70'
    topHighlight = 'bg-orange-500'
    iconColor = 'text-orange-400'
  } else if (accentColor === 'yellow') {
    accentBorder = 'border-amber-900/40 hover:border-amber-600/70'
    topHighlight = 'bg-amber-500'
    iconColor = 'text-amber-400'
  } else if (accentColor === 'green') {
    accentBorder = 'border-emerald-900/40 hover:border-emerald-600/70'
    topHighlight = 'bg-emerald-500'
    iconColor = 'text-emerald-400'
  }

  let deltaClasses = 'text-slate-400'
  if (deltaType === 'positive') deltaClasses = 'text-emerald-400 bg-emerald-950/40 border-emerald-900/60'
  if (deltaType === 'negative') deltaClasses = 'text-rose-400 bg-rose-950/40 border-rose-900/60'
  if (deltaType === 'critical') deltaClasses = 'text-rose-300 bg-rose-950/80 border-rose-800 animate-pulse'

  return (
    <motion.div
      onClick={onClick}
      whileHover={onClick ? { y: -2, transition: { duration: 0.15, ease: 'easeOut' } } : undefined}
      className={cn(
        'relative bg-[#10141e]/90 border rounded-lg p-3.5 transition-colors duration-200 overflow-hidden group shadow-lg',
        accentBorder,
        onClick && 'cursor-pointer hover:bg-[#131926]',
        className
      )}
    >
      {/* Subtle top edge indicator */}
      <div className={cn('absolute top-0 left-0 right-0 h-[2px]', topHighlight)} />

      <div className="flex items-start justify-between gap-2 mb-1.5">
        <span className="text-[11px] font-mono tracking-wider uppercase text-slate-400 font-medium truncate">
          {title}
        </span>
        {Icon && (
          <div className={cn('p-1.5 rounded bg-slate-900/90 border border-slate-800 shrink-0 group-hover:scale-105 transition-transform duration-200', iconColor)}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-2xl font-bold font-mono tracking-tight text-slate-100">
          {value}
        </span>
        {delta && (
          <span className={cn('text-[11px] font-mono px-1.5 py-0.5 rounded border', deltaClasses)}>
            {delta}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="text-[11px] text-slate-400 font-sans truncate">
          {subtitle}
        </div>
      )}
    </motion.div>
  )
}

export default KpiCard
