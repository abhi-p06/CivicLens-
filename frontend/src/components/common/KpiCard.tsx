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
  variants?: any
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
  variants,
}) => {
  let accentBorder = 'border-slate-800/80 hover:border-slate-700'
  let topHighlight = 'bg-slate-700/50'
  let iconBg = 'bg-slate-900/80 text-slate-400 border-slate-800'

  if (accentColor === 'cyan') {
    accentBorder = 'border-cyan-900/50 hover:border-cyan-500/80'
    topHighlight = 'bg-cyan-500'
    iconBg = 'bg-cyan-950/60 text-cyan-400 border-cyan-800/60'
  } else if (accentColor === 'red') {
    accentBorder = 'border-rose-900/50 hover:border-rose-500/80'
    topHighlight = 'bg-rose-500'
    iconBg = 'bg-rose-950/60 text-rose-400 border-rose-800/60'
  } else if (accentColor === 'orange') {
    accentBorder = 'border-orange-900/50 hover:border-orange-500/80'
    topHighlight = 'bg-orange-500'
    iconBg = 'bg-orange-950/60 text-orange-400 border-orange-800/60'
  } else if (accentColor === 'yellow') {
    accentBorder = 'border-amber-900/50 hover:border-amber-500/80'
    topHighlight = 'bg-amber-500'
    iconBg = 'bg-amber-950/60 text-amber-400 border-amber-800/60'
  } else if (accentColor === 'green') {
    accentBorder = 'border-emerald-900/50 hover:border-emerald-500/80'
    topHighlight = 'bg-emerald-500'
    iconBg = 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60'
  }

  let deltaClasses = 'text-slate-400 bg-slate-900/80 border-slate-800'
  if (deltaType === 'positive') deltaClasses = 'text-emerald-400 bg-emerald-950/50 border-emerald-800/80 font-bold'
  if (deltaType === 'negative') deltaClasses = 'text-rose-400 bg-rose-950/50 border-rose-800/80 font-bold'
  if (deltaType === 'critical') deltaClasses = 'text-rose-200 bg-rose-950/90 border-rose-700 font-bold shadow-[0_0_10px_rgba(244,63,94,0.3)] animate-pulse'

  return (
    <motion.div
      onClick={onClick}
      variants={variants}
      whileHover={{ y: -3, transition: { duration: 0.18, ease: 'easeOut' } }}
      className={cn(
        'relative bg-[#0d111a] border rounded-xl p-5 transition-all duration-200 overflow-hidden group shadow-lg',
        accentBorder,
        onClick && 'cursor-pointer hover:bg-[#111724] hover:shadow-cyan-950/20',
        className
      )}
    >
      {/* Subtle top edge accent */}
      <div className={cn('absolute top-0 left-0 right-0 h-[2px]', topHighlight)} />

      <div className="flex items-center justify-between gap-3 mb-2.5">
        <span className="text-xs font-semibold tracking-wider uppercase text-slate-300 truncate">
          {title}
        </span>
        {Icon && (
          <div className={cn('p-2 rounded-lg border shrink-0 transition-transform duration-200 group-hover:scale-110 shadow-sm', iconBg)}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2.5 mb-1.5">
        <span className="text-3xl sm:text-4xl font-bold font-mono tracking-tight text-white">
          {value}
        </span>
        {delta && (
          <span className={cn('text-xs px-2 py-0.5 rounded-md border font-mono tracking-wide', deltaClasses)}>
            {delta}
          </span>
        )}
      </div>

      {subtitle && (
        <div className="text-xs text-slate-400 font-sans leading-normal">
          {subtitle}
        </div>
      )}
    </motion.div>
  )
}

export default KpiCard
