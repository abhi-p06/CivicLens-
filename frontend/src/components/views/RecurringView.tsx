import React from 'react'
import {
  RotateCcw,
  TrendingUp,
  TrendingDown,
  Minus,
  MapPin,
  Calendar,
  Clock,
  Layers,
  ArrowRight,
} from 'lucide-react'
import { RecurrenceInfo, Issue } from '../../types'
import { cn } from '../../lib/utils'

interface RecurringViewProps {
  recurringIssues: RecurrenceInfo[]
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const RecurringView: React.FC<RecurringViewProps> = ({
  recurringIssues,
  issues,
  onSelectIssue,
}) => {
  return (
    <div className="h-full flex flex-col overflow-y-auto p-5 sm:p-7 space-y-6 font-sans">
      {/* Header */}
      <div className="p-6 bg-[#0c1018] border border-slate-800/90 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-2 h-full bg-amber-500 shadow-[0_0_12px_#f59e0b]" />
        
        <div className="space-y-1 pl-2">
          <div className="flex items-center gap-2.5">
            <RotateCcw className="w-6 h-6 text-amber-400" />
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Chronic Defect Recurrence Monitor
            </h1>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-mono font-bold bg-amber-950/80 border border-amber-700 text-amber-300">
              FEATURE 17
            </span>
          </div>
          <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
            Distinguishes simultaneous duplicates from chronic failure corridors where municipal defects repeatedly reoccur over time.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pl-2 md:pl-0">
          <div className="px-4 py-2 bg-[#101622] border border-slate-800 rounded-xl text-right">
            <div className="text-xs text-slate-400 font-mono">Chronic Sites</div>
            <div className="text-base font-bold font-mono text-amber-400">
              {recurringIssues.filter((r) => r.recurringIssue).length} Monitored
            </div>
          </div>
        </div>
      </div>

      {/* Recurrence Cards with Timeline Visualization */}
      <div className="space-y-4">
        {recurringIssues.map((r, idx) => {
          let TrendIcon = Minus
          let trendBadge = 'text-slate-300 bg-slate-900 border-slate-700'
          if (r.trend === 'INCREASING') {
            TrendIcon = TrendingUp
            trendBadge = 'text-rose-300 bg-rose-950/80 border-rose-700'
          } else if (r.trend === 'DECREASING') {
            TrendIcon = TrendingDown
            trendBadge = 'text-emerald-300 bg-emerald-950/80 border-emerald-700'
          }

          const firstDate = new Date(r.firstReported).toLocaleDateString()
          const lastDate = new Date(r.lastReported).toLocaleDateString()

          return (
            <div
              key={`${r.location}-${idx}`}
              className="p-6 bg-[#0c1018] border border-slate-800/90 rounded-2xl shadow-xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-950/50 border border-amber-800 text-amber-400 shrink-0">
                    <MapPin className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-bold text-white text-base flex items-center gap-2.5">
                      <span>{r.location}</span>
                      <span className="text-slate-400 font-medium text-xs">({r.category})</span>
                    </div>
                    <div className="text-xs text-slate-500 font-mono mt-0.5">
                      Corridor monitoring radius: 300m
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <span
                    className={cn(
                      'px-3 py-1 rounded-md text-xs font-semibold font-mono border flex items-center gap-1.5',
                      trendBadge
                    )}
                  >
                    <TrendIcon className="w-4 h-4" />
                    <span>TREND: {r.trend}</span>
                  </span>

                  <span className="px-2.5 py-1 rounded-md bg-[#111724] border border-slate-800 text-slate-300 text-xs font-mono">
                    Status: <strong className="text-amber-400">{r.recurringIssue ? 'RECURRING' : 'ISOLATED'}</strong>
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-[#080b11] rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-xs font-semibold uppercase font-mono">Total Reports</div>
                  <div className="text-lg font-bold text-amber-400 mt-1 font-mono">
                    {r.reportCount} Incidents
                  </div>
                </div>

                <div className="p-3 bg-[#080b11] rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-xs font-semibold uppercase font-mono">Recurrence Score</div>
                  <div className="text-lg font-bold text-rose-400 mt-1 font-mono">
                    {(r.recurrenceScore * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-3 bg-[#080b11] rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-xs font-semibold uppercase font-mono">First Incident</div>
                  <div className="text-sm font-bold text-slate-200 mt-1 font-mono truncate">
                    {firstDate}
                  </div>
                </div>

                <div className="p-3 bg-[#080b11] rounded-xl border border-slate-800">
                  <div className="text-slate-400 text-xs font-semibold uppercase font-mono">Latest Incident</div>
                  <div className="text-sm font-bold text-slate-200 mt-1 font-mono truncate">
                    {lastDate}
                  </div>
                </div>
              </div>

              {/* Timeline Visualization */}
              <div className="p-4 bg-[#080b11] rounded-xl border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-1.5 font-medium">
                    <Calendar className="w-4 h-4 text-cyan-400" />
                    <span>Incident Recurrence Timeline</span>
                  </span>
                  <span className="font-mono text-slate-500">
                    Span: {firstDate} &rarr; {lastDate}
                  </span>
                </div>

                {/* Progress track with event markers */}
                <div className="relative h-8 flex items-center">
                  <div className="w-full h-1.5 bg-slate-800 rounded-full" />
                  {/* Start Point */}
                  <div className="absolute left-0 flex flex-col items-center">
                    <div className="w-3.5 h-3.5 rounded-full bg-cyan-500 border-2 border-slate-900 shadow" />
                    <span className="text-[10px] text-slate-400 mt-1 font-mono">Initial</span>
                  </div>

                  {/* Mid Points if multiple reports */}
                  {r.reportCount > 2 && (
                    <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-amber-500 border-2 border-slate-900" />
                      <span className="text-[10px] text-amber-400 mt-1 font-mono">Re-emergence</span>
                    </div>
                  )}

                  {/* Latest Point */}
                  <div className="absolute right-0 flex flex-col items-center">
                    <div className="w-4 h-4 rounded-full bg-rose-500 border-2 border-slate-900 shadow-lg shadow-rose-950 animate-pulse" />
                    <span className="text-[10px] text-rose-400 mt-1 font-mono font-bold">Latest</span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {recurringIssues.length === 0 && (
          <div className="p-12 text-center bg-[#0c1018] border border-slate-800 rounded-2xl text-slate-400">
            No recurring infrastructure defects detected.
          </div>
        )}
      </div>
    </div>
  )
}

export default RecurringView
