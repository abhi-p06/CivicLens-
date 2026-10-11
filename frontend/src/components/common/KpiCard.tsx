import React from 'react'
import { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'
import { GlareHover } from '../reactbits/GlareHover'

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
    <GlareHover
      data-cursor-target="true"
      onClick={onClick}
      variants={variants}
      whileHover={{ y: -2, transition: { duration: 0.18, ease: 'easeOut' } }}
      whileTap={{ scale: 0.99 }}
      glareColor="rgba(100, 87, 232, 0.12)"
      glareSize={260}
      className={cn(
        'group relative bg-white border border-[#E4E7F1] hover:border-slate-300 rounded-2xl p-4 transition-[border-color,background-color,box-shadow] duration-200 shadow-xs hover:shadow-md flex flex-col justify-between min-h-[122px] sm:min-h-[126px] h-full cursor-pointer',
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-1 shrink-0">
        <span className="text-xs sm:text-[13px] font-semibold text-[#11162A] truncate">
          {title}
        </span>
        {Icon && (
          <div className={cn('p-1.5 rounded-lg border shrink-0 transition-transform duration-200 group-hover:scale-105', iconContainer)}>
            <Icon className="w-3.5 h-3.5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline gap-2.5 my-1 shrink-0">
        <div className="text-2xl sm:text-[28px] lg:text-[32px] font-bold tracking-tight text-[#11162A] font-sans leading-none">
          {value}
        </div>
        {delta && (
          <span className={cn('text-[11px] px-2 py-0.5 rounded-full border', deltaClasses)}>
            {delta}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="text-[11px] sm:text-[12px] text-[#65708B] leading-snug font-normal mt-auto">
          {subtitle}
        </p>
      )}
    </GlareHover>
  )
}

export default KpiCard
