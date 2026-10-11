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
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-6 font-sans bg-[#F6F7FC]">
      {/* Header */}
      <div className="p-6 bg-white border border-[#E4E7F1] rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-[#F97316]" />
        
        <div className="space-y-1 pl-2">
          <div className="flex items-center gap-2.5">
            <RotateCcw className="w-6 h-6 text-[#F97316]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#11162A] tracking-normal">
              Chronic Defect Recurrence Monitor
            </h1>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-amber-50 border border-amber-200 text-amber-800">
              FEATURE 17
            </span>
          </div>
          <p className="text-[#65708B] text-sm max-w-2xl leading-relaxed">
            Distinguishes simultaneous duplicates from chronic failure corridors where municipal defects repeatedly reoccur over time.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pl-2 md:pl-0">
          <div className="px-4 py-2 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl text-right">
            <div className="text-xs text-[#65708B]">Chronic Sites</div>
            <div className="text-base font-bold font-mono text-[#F97316]">
              {recurringIssues.filter((r) => r.recurringIssue).length} Monitored
            </div>
          </div>
        </div>
      </div>

      {/* Recurrence Cards with Timeline Visualization */}
      <div className="space-y-4">
        {recurringIssues.map((r, idx) => {
          let TrendIcon = Minus
          let trendBadge = 'text-[#65708B] bg-[#F0F2F9] border-[#E4E7F1]'
          if (r.trend === 'INCREASING') {
            TrendIcon = TrendingUp
            trendBadge = 'text-rose-700 bg-rose-50 border-rose-200'
          } else if (r.trend === 'DECREASING') {
            TrendIcon = TrendingDown
            trendBadge = 'text-emerald-700 bg-emerald-50 border-emerald-200'
          }

          const firstDate = new Date(r.firstReported).toLocaleDateString()
          const lastDate = new Date(r.lastReported).toLocaleDateString()

          return (
            <div
              key={`${r.location}-${idx}`}
              className="p-6 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 shrink-0">
                    <MapPin className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="font-bold text-[#11162A] text-base flex items-center gap-2.5">
                      <span>{r.location}</span>
                      <span className="text-[#65708B] font-medium text-xs">({r.category})</span>
                    </div>
                    <div className="text-xs text-[#65708B] mt-0.5">
                      Corridor monitoring radius: 300m
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <span
                    className={cn(
                      'px-3 py-1 rounded-lg text-xs font-semibold border flex items-center gap-1.5',
                      trendBadge
                    )}
                  >
                    <TrendIcon className="w-4 h-4" />
                    <span>TREND: {r.trend}</span>
                  </span>

                  <span className="px-2.5 py-1 rounded-lg bg-[#F0F2F9] border border-[#E4E7F1] text-[#65708B] text-xs">
                    Status: <strong className="text-[#F97316] font-semibold">{r.recurringIssue ? 'RECURRING' : 'ISOLATED'}</strong>
                  </span>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-xs font-semibold">Total Reports</div>
                  <div className="text-lg font-bold text-[#F97316] mt-1 font-mono">
                    {r.reportCount} Incidents
                  </div>
                </div>

                <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-xs font-semibold">Recurrence Score</div>
                  <div className="text-lg font-bold text-[#EF4444] mt-1 font-mono">
                    {(r.recurrenceScore * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-xs font-semibold">First Incident</div>
                  <div className="text-sm font-bold text-[#11162A] mt-1 font-mono truncate">
                    {firstDate}
                  </div>
                </div>

                <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-xs font-semibold">Latest Incident</div>
                  <div className="text-sm font-bold text-[#11162A] mt-1 font-mono truncate">
                    {lastDate}
                  </div>
                </div>
              </div>

              {/* Timeline Visualization */}
              <div className="p-4 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-2.5">
                <div className="flex items-center justify-between text-xs text-[#65708B]">
                  <span className="flex items-center gap-1.5 font-medium text-[#11162A]">
                    <Calendar className="w-4 h-4 text-[#6457E8]" />
                    <span>Incident Recurrence Timeline</span>
                  </span>
                  <span className="font-mono text-[#65708B]">
                    Span: {firstDate} &rarr; {lastDate}
                  </span>
                </div>

                {/* Progress track with event markers */}
                <div className="relative h-8 flex items-center">
                  <div className="w-full h-1.5 bg-[#E4E7F1] rounded-full" />
                  {/* Start Point */}
                  <div className="absolute left-0 flex flex-col items-center">
                    <div className="w-3.5 h-3.5 rounded-full bg-[#6457E8] border-2 border-white shadow-xs" />
                    <span className="text-[10px] text-[#65708B] mt-1 font-mono">Initial</span>
                  </div>

                  {/* Mid Points if multiple reports */}
                  {r.reportCount > 2 && (
                    <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-[#F97316] border-2 border-white" />
                      <span className="text-[10px] text-[#F97316] mt-1 font-mono font-medium">Re-emergence</span>
                    </div>
                  )}

                  {/* Latest Point */}
                  <div className="absolute right-0 flex flex-col items-center">
                    <div className="w-4 h-4 rounded-full bg-[#EF4444] border-2 border-white shadow-xs animate-pulse" />
                    <span className="text-[10px] text-[#EF4444] mt-1 font-mono font-bold">Latest</span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {recurringIssues.length === 0 && (
          <div className="p-12 text-center bg-white border border-[#E4E7F1] rounded-2xl text-[#65708B] shadow-xs">
            No recurring infrastructure defects detected.
          </div>
        )}
      </div>
    </div>
  )
}

export default RecurringView
