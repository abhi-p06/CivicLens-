import React from 'react'
import { RotateCcw, TrendingUp, TrendingDown, Minus, MapPin, Calendar, AlertCircle } from 'lucide-react'
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
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              FEATURE 17: RECURRING ISSUE DETECTION ENGINE
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Isolates structural deterioration where the same problem repeatedly recurs at an infrastructure point over time (distinct from duplicate reports of a single event).
          </p>
        </div>

        <div className="px-3 py-1.5 bg-amber-950/80 border border-amber-800 text-amber-300 rounded font-bold">
          {recurringIssues.filter((r) => r.recurringIssue).length} RECURRING SITES
        </div>
      </div>

      {/* Distinction explanation banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="font-bold text-slate-300 uppercase text-[10px] mb-1">
            DUPLICATE DETECTION (FEATURE 5 & 6)
          </div>
          <p className="text-slate-400 text-xs font-sans leading-relaxed">
            Multiple citizens independently reporting the <strong className="text-slate-200">same single incident</strong> (e.g. 5 calls about one pothole on Monday morning). Aggregated into single work order.
          </p>
        </div>

        <div className="p-3 bg-[#111724] border border-amber-900/60 rounded-lg">
          <div className="font-bold text-amber-400 uppercase text-[10px] mb-1">
            RECURRING ISSUE DETECTION (FEATURE 17)
          </div>
          <p className="text-slate-400 text-xs font-sans leading-relaxed">
            The same defect category <strong className="text-amber-300">repeatedly re-occurring</strong> over weeks/months after prior closures, indicating underlying structural or utility sub-base failure.
          </p>
        </div>
      </div>

      {/* Recurrence Table */}
      <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
        <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
          <span>Chronic Failure Registry</span>
          <span className="text-slate-500">Spatial radius 300m &bull; Time series</span>
        </div>

        <div className="space-y-3">
          {recurringIssues.map((r, idx) => {
            let TrendIcon = Minus
            let trendColor = 'text-slate-400 bg-slate-900 border-slate-700'
            if (r.trend === 'INCREASING') {
              TrendIcon = TrendingUp
              trendColor = 'text-rose-400 bg-rose-950/60 border-rose-800'
            } else if (r.trend === 'DECREASING') {
              TrendIcon = TrendingDown
              trendColor = 'text-emerald-400 bg-emerald-950/60 border-emerald-800'
            }

            return (
              <div
                key={`${r.location}-${idx}`}
                className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-3 shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-cyan-400 text-sm">{r.location}</span>
                    <span className="text-slate-400 font-sans text-xs">({r.category})</span>
                    {r.recurringIssue && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 border border-amber-800 text-amber-300">
                        RECURRING DEFECT
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-[11px] font-bold border flex items-center gap-1',
                        trendColor
                      )}
                    >
                      <TrendIcon className="w-3.5 h-3.5" />
                      <span>TREND: {r.trend}</span>
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                  <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                    <div className="text-slate-500 text-[10px]">HISTORICAL INCIDENTS</div>
                    <div className="text-base font-bold text-amber-400 mt-0.5">
                      {r.reportCount} Reports
                    </div>
                  </div>

                  <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                    <div className="text-slate-500 text-[10px]">RECURRENCE SCORE</div>
                    <div className="text-base font-bold text-rose-400 mt-0.5">
                      {(r.recurrenceScore * 100).toFixed(0)}%
                    </div>
                  </div>

                  <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                    <div className="text-slate-500 text-[10px]">FIRST RECORDED</div>
                    <div className="text-xs font-bold text-slate-300 mt-1 truncate">
                      {new Date(r.firstReported).toLocaleDateString()}
                    </div>
                  </div>

                  <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                    <div className="text-slate-500 text-[10px]">LATEST REPORT</div>
                    <div className="text-xs font-bold text-slate-300 mt-1 truncate">
                      {new Date(r.lastReported).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
