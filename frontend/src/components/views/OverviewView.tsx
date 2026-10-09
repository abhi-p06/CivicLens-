import React from 'react'
import {
  ShieldAlert,
  Flame,
  RotateCcw,
  Sparkles,
  MapPin,
  Camera,
  CheckCircle2,
  Clock,
  Layers,
  Activity,
  AlertCircle,
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { KpiCard } from '../common/KpiCard'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { CivicMap } from '../map/CivicMap'
import { AnimatedCounter } from '../common/AnimatedCounter'

interface OverviewViewProps {
  issues: Issue[]
  hotspots: HotspotInfo[]
  recurringIssues: RecurrenceInfo[]
  onSelectIssue: (issue: Issue) => void
  onNavigate: (viewId: string) => void
  onStartDemo?: () => void
  loading?: boolean
  error?: string | null
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  issues,
  hotspots,
  recurringIssues,
  onSelectIssue,
  onNavigate,
  onStartDemo,
  loading = false,
  error = null,
}) => {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center p-8 font-mono text-xs">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
          <span className="text-slate-400">Loading Civic Intelligence Command Center...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8 font-mono text-xs">
        <div className="p-4 bg-rose-950/40 border border-rose-800 rounded-xl text-rose-300 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 shrink-0" />
          <span>Error loading command center: {error}</span>
        </div>
      </div>
    )
  }

  const totalIssues = issues.length
  const highPriorityCount = issues.filter(
    (i) => i.priorityLevel === 'CRITICAL' || i.priorityLevel === 'HIGH' || i.priorityScore >= 65
  ).length
  const unreportedCount = issues.filter(
    (i) => i.metadata?.isAutoDrafted || i.source === 'patrol_camera' || i.source === 'camera_survey'
  ).length
  const hotspotsCount = hotspots.length
  const recurringCount = recurringIssues.filter((r) => r.recurringIssue).length
  const pendingResolutionCount = issues.filter(
    (i) => i.status !== 'RESOLVED'
  ).length

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* 1. Header Banner */}
      <div className="p-5 bg-[#0e131d] border border-slate-800/90 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-cyan-500" />
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-wider text-slate-100 flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <span>CIVIC INTELLIGENCE</span>
          </h1>
          <p className="text-slate-400 font-sans text-xs sm:text-sm mt-1">
            AI-powered detection, prioritization and verification of civic issues.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (onStartDemo) onStartDemo()
              else onNavigate('analyze')
            }}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-bold font-mono tracking-wide shadow-lg shadow-cyan-950/60 transition active:scale-95 cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-cyan-200" />
            <span>ANALYZE CIVIC ISSUE</span>
          </button>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#121824] border border-slate-700/80 text-emerald-400 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>REAL-TIME INFERENCE ONLINE</span>
          </div>
        </div>
      </div>

      {/* 2. KPI Cards (Animated Numbers on Entry) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <KpiCard
          title="TOTAL ISSUES"
          value={<AnimatedCounter value={totalIssues} />}
          subtitle="Monitored repository"
          accentColor="slate"
          icon={Layers}
        />

        <KpiCard
          title="HIGH PRIORITY"
          value={<AnimatedCounter value={highPriorityCount} />}
          subtitle="Critical & High risk"
          accentColor="red"
          icon={ShieldAlert}
          delta={highPriorityCount > 0 ? 'CRITICAL' : 'NOMINAL'}
          deltaType={highPriorityCount > 0 ? 'critical' : 'positive'}
        />

        <KpiCard
          title="UNREPORTED"
          value={<AnimatedCounter value={unreportedCount} />}
          subtitle="Patrol survey detections"
          accentColor="cyan"
          icon={Camera}
          onClick={() => onNavigate('unreported')}
        />

        <KpiCard
          title="HOTSPOTS"
          value={<AnimatedCounter value={hotspotsCount} />}
          subtitle="DBSCAN spatial clusters"
          accentColor="orange"
          icon={Flame}
          onClick={() => onNavigate('hotspots')}
        />

        <KpiCard
          title="RECURRING"
          value={<AnimatedCounter value={recurringCount} />}
          subtitle="Chronic failure sites"
          accentColor="yellow"
          icon={RotateCcw}
          onClick={() => onNavigate('recurring')}
        />

        <KpiCard
          title="PENDING RESOLUTION"
          value={<AnimatedCounter value={pendingResolutionCount} />}
          subtitle="Active work orders"
          accentColor="green"
          icon={Clock}
          onClick={() => onNavigate('resolution')}
        />
      </div>

      {/* 3. Below: Large Interactive Map & Live Priority Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-[500px]">
        {/* Large Interactive Map */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-3 flex flex-col shadow-2xl">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-cyan-400" />
              <span className="font-bold text-slate-100 text-xs tracking-wider uppercase">
                Large Interactive Map (Tactical GIS)
              </span>
            </div>
            <button
              onClick={() => onNavigate('map')}
              className="text-cyan-400 hover:text-cyan-300 text-[11px] font-mono hover:underline"
            >
              Open Workspace &rarr;
            </button>
          </div>

          <div className="flex-1 w-full min-h-[400px] rounded-lg overflow-hidden border border-slate-800/80">
            <CivicMap
              issues={issues}
              hotspots={hotspots}
              onSelectIssue={onSelectIssue}
              className="h-full w-full"
            />
          </div>
        </div>

        {/* Live Priority Feed */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-2xl">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-rose-500 animate-pulse" />
              <span className="font-bold text-slate-100 text-xs tracking-wider uppercase">
                Live Priority Feed
              </span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Click issue for intelligence
            </span>
          </div>

          {issues.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-center p-6">
              No priority issues in intake queue.
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-2.5 max-h-[480px] pr-1">
              {issues.map((issue) => (
                <div
                  key={issue.issueId}
                  onClick={() => onSelectIssue(issue)}
                  className="p-3 bg-[#111724] hover:bg-[#151c2e] border border-slate-800 hover:border-cyan-800/80 rounded-lg cursor-pointer transition shadow-md group"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-bold border uppercase ${
                          issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
                            ? 'bg-rose-950/80 border-rose-700 text-rose-300'
                            : issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
                            ? 'bg-orange-950/80 border-orange-700 text-orange-300'
                            : 'bg-amber-950/80 border-amber-700 text-amber-300'
                        }`}
                      >
                        {issue.priorityLevel}
                      </span>
                      <span className="font-bold text-slate-100 group-hover:text-cyan-300 transition-colors truncate max-w-[180px]">
                        {issue.category}
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-xs font-bold text-cyan-400 font-mono">
                        Priority {issue.priorityScore.toFixed(0)}
                      </span>
                    </div>
                  </div>

                  <div className="text-slate-300 font-sans text-xs line-clamp-2 leading-relaxed my-1.5">
                    {issue.complaintText}
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-slate-800/80">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      {issue.location}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                      <StatusBadge status={issue.status} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
