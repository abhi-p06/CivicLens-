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
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-amber-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <RotateCcw className="w-5 h-5 text-amber-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
              FEATURE 17 // RECURRING CIVIC DEFECT ANALYSIS
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-0.5">
            Differentiating simultaneous duplicates from chronic infrastructure points where defects repeatedly reappear over time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 bg-amber-950/80 border border-amber-800 text-amber-300 rounded font-bold">
            {recurringIssues.filter((r) => r.recurringIssue).length} CHRONIC FAILURE SITES
          </span>
        </div>
      </div>

      {/* Recurrence Cards with Timeline Visualization */}
      <div className="space-y-4">
        {recurringIssues.map((r, idx) => {
          let TrendIcon = Minus
          let trendBadge = 'text-slate-300 bg-slate-900 border-slate-700'
          if (r.trend === 'INCREASING') {
            TrendIcon = TrendingUp
            trendBadge = 'text-rose-400 bg-rose-950/60 border-rose-800'
          } else if (r.trend === 'DECREASING') {
            TrendIcon = TrendingDown
            trendBadge = 'text-emerald-400 bg-emerald-950/60 border-emerald-800'
          }

          // Generate simulated timeline event intervals between firstReported and lastReported
          const firstDate = new Date(r.firstReported).toLocaleDateString()
          const lastDate = new Date(r.lastReported).toLocaleDateString()

          return (
            <div
              key={`${r.location}-${idx}`}
              className="p-5 bg-[#0e131d] border border-slate-800 rounded-xl shadow-xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded bg-amber-950/50 border border-amber-800 text-amber-400">
                    <MapPin className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-100 text-sm flex items-center gap-2">
                      <span>{r.location}</span>
                      <span className="text-slate-400 font-sans text-xs">({r.category})</span>
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                      Corridor monitoring radius: 300m
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'px-2.5 py-1 rounded text-[11px] font-bold border flex items-center gap-1.5',
                      trendBadge
                    )}
                  >
                    <TrendIcon className="w-3.5 h-3.5" />
                    <span>TREND: {r.trend}</span>
                  </span>

                  <span className="px-2 py-1 rounded bg-[#121824] border border-slate-800 text-slate-300 text-[11px]">
                    Status: <strong className="text-amber-400">{r.recurringIssue ? 'RECURRING' : 'ISOLATED'}</strong>
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-[11px]">
                <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase">REPORT COUNT</div>
                  <div className="text-base font-bold text-amber-400 mt-0.5">
                    {r.reportCount} Incidents
                  </div>
                </div>

                <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase">RECURRENCE SCORE</div>
                  <div className="text-base font-bold text-rose-400 mt-0.5">
                    {(r.recurrenceScore * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase">FIRST REPORTED</div>
                  <div className="text-xs font-bold text-slate-200 mt-1 truncate">
                    {firstDate}
                  </div>
                </div>

                <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                  <div className="text-slate-500 text-[10px] uppercase">LATEST REPORTED</div>
                  <div className="text-xs font-bold text-slate-200 mt-1 truncate">
                    {lastDate}
                  </div>
                </div>
              </div>

              {/* Timeline Visualization */}
              <div className="p-3.5 bg-[#0a0d14] rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-[10px] text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Incident Timeline Recurrence Trace</span>
                  </span>
                  <span className="text-slate-500">
                    Span: {firstDate} &rarr; {lastDate}
                  </span>
                </div>

                {/* Progress track with event markers */}
                <div className="relative h-6 flex items-center">
                  <div className="w-full h-1 bg-slate-800 rounded-full" />
                  {/* Start Point */}
                  <div className="absolute left-0 flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-cyan-500 border-2 border-slate-900 shadow" />
                    <span className="text-[9px] text-slate-400 mt-0.5">Initial</span>
                  </div>

                  {/* Mid Points if multiple reports */}
                  {r.reportCount > 2 && (
                    <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center">
                      <div className="w-2.5 h-2.5 rounded-full bg-amber-500 border-2 border-slate-900" />
                      <span className="text-[9px] text-amber-400 mt-0.5">Re-emergence</span>
                    </div>
                  )}

                  {/* Latest Point */}
                  <div className="absolute right-0 flex flex-col items-center">
                    <div className="w-3.5 h-3.5 rounded-full bg-rose-500 border-2 border-slate-900 shadow-lg shadow-rose-950 animate-pulse" />
                    <span className="text-[9px] text-rose-400 mt-0.5 font-bold">Latest</span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {recurringIssues.length === 0 && (
          <div className="p-8 text-center bg-[#0e131d] border border-slate-800 rounded-xl text-slate-500">
            No recurring infrastructure defects detected.
          </div>
        )}
      </div>
    </div>
  )
}
