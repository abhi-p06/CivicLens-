import React from 'react'
import {
  ShieldAlert,
  Flame,
  Clock,
  RotateCcw,
  Sparkles,
  MapPin,
  ChevronRight,
  TrendingUp,
  BarChart2,
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { KpiCard } from '../common/KpiCard'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { CivicMap } from '../map/CivicMap'

interface OverviewViewProps {
  issues: Issue[]
  hotspots: HotspotInfo[]
  recurringIssues: RecurrenceInfo[]
  onSelectIssue: (issue: Issue) => void
  onNavigate: (viewId: string) => void
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  issues,
  hotspots,
  recurringIssues,
  onSelectIssue,
  onNavigate,
}) => {
  const criticalCount = issues.filter((i) => i.priorityLevel === 'CRITICAL' || i.priorityScore >= 80).length
  const highCount = issues.filter((i) => i.priorityLevel === 'HIGH' && i.priorityScore < 80).length
  const recurringCount = recurringIssues.filter((r) => r.recurringIssue).length
  const avgPriority =
    issues.length > 0
      ? (issues.reduce((acc, i) => acc + (i.priorityScore || 0), 0) / issues.length).toFixed(1)
      : '0'

  // Category breakdown
  const categoryCounts: Record<string, number> = {}
  issues.forEach((i) => {
    categoryCounts[i.category] = (categoryCounts[i.category] || 0) + 1
  })

  // Ward breakdown
  const wardCounts: Record<string, number> = {}
  issues.forEach((i) => {
    const w = i.ward || 'Central'
    wardCounts[w] = (wardCounts[w] || 0) + 1
  })

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* KPI Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3.5">
        <KpiCard
          title="ACTIVE INCIDENTS"
          value={issues.length}
          subtitle="Real-time intake queue"
          accentColor="cyan"
          icon={ShieldAlert}
          delta="+4 today"
          deltaType="neutral"
        />

        <KpiCard
          title="CRITICAL / HIGH RISK"
          value={criticalCount + highCount}
          subtitle={`${criticalCount} require immediate dispatch`}
          accentColor="red"
          icon={Flame}
          delta={criticalCount > 0 ? 'CRITICAL' : 'STABLE'}
          deltaType={criticalCount > 0 ? 'critical' : 'positive'}
        />

        <KpiCard
          title="DBSCAN HOTSPOTS"
          value={hotspots.length}
          subtitle="Clusters identified (R=500m)"
          accentColor="orange"
          icon={Flame}
          delta={hotspots.length > 0 ? '+100% Growth' : 'Nominal'}
          deltaType="negative"
          onClick={() => onNavigate('hotspots')}
        />

        <KpiCard
          title="CHRONIC RECURRENCE"
          value={recurringCount}
          subtitle="Sites with repetitive failures"
          accentColor="yellow"
          icon={RotateCcw}
          delta="Monitoring"
          deltaType="neutral"
          onClick={() => onNavigate('recurring')}
        />

        <KpiCard
          title="AVG COMPOSITE PRIORITY"
          value={`${avgPriority}/100`}
          subtitle="Weighted risk index"
          accentColor="green"
          icon={TrendingUp}
          delta="Explainable"
          deltaType="positive"
        />
      </div>

      {/* Main Grid: Tactical Map & High-Risk Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-[460px]">
        {/* Map Panel */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-3 flex flex-col shadow-xl">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-cyan-400" />
              <span className="font-bold text-slate-100 text-xs tracking-wider uppercase">
                Tactical GIS Spatial Overview
              </span>
            </div>
            <button
              onClick={() => onNavigate('map')}
              className="text-cyan-400 hover:text-cyan-300 text-[11px] flex items-center gap-1 font-mono"
            >
              <span>Full Screen</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 w-full min-h-[360px] rounded-lg overflow-hidden border border-slate-800/80">
            <CivicMap
              issues={issues}
              hotspots={hotspots}
              onSelectIssue={onSelectIssue}
              className="h-full w-full"
            />
          </div>
        </div>

        {/* High-Risk Queue Panel */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-xl">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" />
              <span className="font-bold text-slate-100 text-xs tracking-wider uppercase">
                Priority Dispatch Queue
              </span>
            </div>
            <button
              onClick={() => onNavigate('explorer')}
              className="text-slate-400 hover:text-slate-200 text-[11px] flex items-center gap-1"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2.5 max-h-[420px] pr-1">
            {issues.map((issue) => (
              <div
                key={issue.issueId}
                onClick={() => onSelectIssue(issue)}
                className="p-3 bg-[#111724] hover:bg-[#151c2e] border border-slate-800 hover:border-slate-700 rounded-lg cursor-pointer transition shadow group"
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2 truncate">
                    <span className="font-bold text-cyan-400 group-hover:underline">
                      {issue.issueId}
                    </span>
                    <StatusBadge status={issue.status} />
                  </div>
                  <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                </div>

                <div className="text-slate-200 font-sans text-xs line-clamp-2 leading-relaxed">
                  {issue.complaintText}
                </div>

                <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                  <span className="truncate">
                    {issue.location} &bull; {issue.department.slice(0, 24)}
                  </span>
                  <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Analytics Breakdown Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Category Breakdown */}
        <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-cyan-400" />
              <span>Incident Category Distribution</span>
            </span>
            <span className="text-slate-500">{issues.length} Total</span>
          </div>

          <div className="space-y-2.5">
            {Object.entries(categoryCounts).map(([cat, count]) => {
              const pct = ((count / issues.length) * 100).toFixed(0)
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span className="font-sans truncate">{cat}</span>
                    <span className="font-mono text-cyan-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Municipal Ward Distribution */}
        <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-emerald-400" />
              <span>Administrative Ward Load</span>
            </span>
            <span className="text-slate-500">Mumbai Region</span>
          </div>

          <div className="space-y-2.5">
            {Object.entries(wardCounts).map(([ward, count]) => {
              const pct = ((count / issues.length) * 100).toFixed(0)
              return (
                <div key={ward} className="space-y-1">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span className="font-sans truncate">{ward}</span>
                    <span className="font-mono text-emerald-400">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 rounded-full"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
