import React, { useState } from 'react'
import { PriorityLevel, PriorityBreakdown } from '../../types'
import { cn } from '../../lib/utils'
import { Info } from 'lucide-react'

interface PriorityGaugeProps {
  score: number // 0 to 100
  level: PriorityLevel | string
  breakdown?: PriorityBreakdown
  reasoning?: string
  compact?: boolean
  showDetails?: boolean
}

export const PriorityGauge: React.FC<PriorityGaugeProps> = ({
  score,
  level,
  breakdown,
  reasoning,
  compact = false,
  showDetails = false,
}) => {
  const [open, setOpen] = useState(false)
  const normLevel = (level || 'LOW').toUpperCase()

  // Color mapping
  let barColor = 'bg-emerald-500'
  let textColor = 'text-emerald-400'
  let badgeBg = 'bg-emerald-950/60 text-emerald-300 border-emerald-800'

  if (normLevel === 'CRITICAL' || score >= 80) {
    barColor = 'bg-rose-500'
    textColor = 'text-rose-400'
    badgeBg = 'bg-rose-950/60 text-rose-300 border-rose-800'
  } else if (normLevel === 'HIGH' || score >= 65) {
    barColor = 'bg-orange-500'
    textColor = 'text-orange-400'
    badgeBg = 'bg-orange-950/60 text-orange-300 border-orange-800'
  } else if (normLevel === 'MEDIUM' || score >= 40) {
    barColor = 'bg-amber-500'
    textColor = 'text-amber-400'
    badgeBg = 'bg-amber-950/60 text-amber-300 border-amber-800'
  }

  if (compact) {
    return (
      <div className="inline-flex items-center gap-1.5 font-mono text-xs">
        <div className="w-12 h-1.5 bg-slate-800 rounded-full overflow-hidden shrink-0">
          <div
            className={cn('h-full transition-all duration-500', barColor)}
            style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
          />
        </div>
        <span className={cn('font-semibold', textColor)}>{score.toFixed(0)}</span>
      </div>
    )
  }

  return (
    <div className="relative font-mono text-xs">
      <div className="flex items-center justify-between gap-2 mb-1">
        <div className="flex items-center gap-1.5">
          <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-bold border tracking-wider', badgeBg)}>
            {normLevel}
          </span>
          <span className="text-slate-400 text-[11px]">PRIORITY</span>
        </div>
        <div className="flex items-center gap-1">
          <span className={cn('text-sm font-bold', textColor)}>{score.toFixed(1)}</span>
          <span className="text-slate-500 text-[10px]">/ 100</span>
          {(breakdown || reasoning) && (
            <button
              onClick={() => setOpen(!open)}
              className="text-slate-400 hover:text-cyan-400 transition ml-0.5"
              title="Explain priority factors"
            >
              <Info className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Segmented bar */}
      <div className="h-2 w-full bg-slate-900 border border-slate-800 rounded overflow-hidden flex">
        <div
          className={cn('h-full transition-all duration-700 rounded-sm', barColor)}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>

      {/* Explanatory Breakdown Modal/Card */}
      {(open || showDetails) && breakdown && (
        <div className="mt-2.5 p-2.5 bg-slate-950/95 border border-slate-800 rounded text-[11px] space-y-1.5 shadow-2xl z-20">
          <div className="text-[10px] uppercase tracking-wider text-slate-400 border-b border-slate-800 pb-1 font-semibold flex justify-between">
            <span>Explainable Scoring Vectors</span>
            <span className="text-cyan-400">Total: {score.toFixed(1)}/100</span>
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Urgency:</span>
              <span className="font-semibold text-slate-200">{breakdown.urgency.toFixed(1)}/20</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Text Severity:</span>
              <span className="font-semibold text-slate-200">{breakdown.textSeverity.toFixed(1)}/20</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Visual Severity:</span>
              <span className="font-semibold text-slate-200">{breakdown.visualSeverity.toFixed(1)}/20</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Related Reports:</span>
              <span className="font-semibold text-slate-200">{breakdown.relatedReports.toFixed(1)}/15</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Recency:</span>
              <span className="font-semibold text-slate-200">{breakdown.recency.toFixed(1)}/10</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Location Risk:</span>
              <span className="font-semibold text-slate-200">{breakdown.locationRisk.toFixed(1)}/15</span>
            </div>
          </div>
          {reasoning && (
            <div className="pt-1 text-[10px] text-slate-400 border-t border-slate-900 leading-relaxed font-sans">
              {reasoning}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
