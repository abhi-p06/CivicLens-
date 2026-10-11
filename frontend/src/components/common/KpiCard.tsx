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
  accentColor?: 'cyan' | 'green' | 'yellow' | 'orange' | 'red' | 'slate' | 'violet' | 'indigo'
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
  // Refined semantic icon tinting
  let iconContainer = 'text-[#65708B] bg-[#F0F2F9] border-[#E4E7F1]'
  if (accentColor === 'cyan' || accentColor === 'violet' || (accentColor as string) === 'indigo') {
    iconContainer = 'text-[#6457E8] bg-[#6457E8]/10 border-[#6457E8]/20'
  } else if (accentColor === 'red') {
    iconContainer = 'text-[#EF4444] bg-rose-50 border-rose-200'
  } else if (accentColor === 'orange') {
    iconContainer = 'text-[#F97316] bg-orange-50 border-orange-200'
  } else if (accentColor === 'green') {
    iconContainer = 'text-[#10B981] bg-emerald-50 border-emerald-200'
  }

  let deltaClasses = 'text-[#65708B] bg-[#F0F2F9] border-[#E4E7F1]'
  if (deltaType === 'positive') deltaClasses = 'text-emerald-700 bg-emerald-50 border-emerald-200 font-semibold'
  if (deltaType === 'critical') deltaClasses = 'text-rose-700 bg-rose-50 border-rose-200 font-semibold'

  return (
    <motion.div
      onClick={onClick}
      variants={variants}
      whileHover={{ y: -2, transition: { duration: 0.16, ease: 'easeOut' } }}
      whileTap={{ scale: 0.99 }}
      className={cn(
        'group relative bg-white border border-[#E4E7F1] hover:border-slate-300 rounded-2xl p-5 sm:p-6 transition-all duration-200 overflow-hidden shadow-xs hover:shadow-md flex flex-col justify-between h-full min-h-[148px]',
        onClick && 'cursor-pointer hover:bg-slate-50/50',
        className
      )}
    >
      <div className="flex items-center justify-between gap-3 mb-3">
        <span className="text-sm font-semibold text-[#11162A] truncate">
          {title}
        </span>
        {Icon && (
          <div className={cn('p-2.5 rounded-xl border shrink-0 transition-transform duration-200 group-hover:scale-105', iconContainer)}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-3 mb-1.5">
        <div className="text-3xl sm:text-[34px] font-bold tracking-tight text-[#11162A] font-sans leading-none">
          {value}
        </div>
        {delta && (
          <span className={cn('text-xs px-2.5 py-0.5 rounded-full border', deltaClasses)}>
            {delta}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-xs sm:text-[13px] text-[#65708B] leading-relaxed mt-1 font-normal">
          {subtitle}
        </p>
      )}
    </motion.div>
  )
}

export default KpiCard
