import React, { useState } from 'react'
import { motion, Variants } from 'framer-motion'
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
  TrendingUp,
  ArrowRight,
  ExternalLink,
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { KpiCard } from '../common/KpiCard'
import { StatusBadge } from '../common/StatusBadge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { CivicMap, MapLayerMode } from '../map/CivicMap'
import { AnimatedCounter } from '../common/AnimatedCounter'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { cn } from '../../lib/utils'

const kpiContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
}

const kpiItemVariants: Variants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: 'easeOut' },
  },
}

const feedContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.06,
    },
  },
}

const feedItemVariants: Variants = {
  hidden: { opacity: 0, x: -8 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.22, ease: 'easeOut' },
  },
}

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
  const [mapLayer, setMapLayer] = useState<MapLayerMode>('markers')

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center p-8 font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 rounded-full border-2 border-cyan-500 border-t-transparent animate-spin" />
          <span className="text-slate-400 text-sm">Loading Civic Intelligence Command Center...</span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center p-8 font-sans">
        <div className="p-5 bg-rose-950/40 border border-rose-800 rounded-xl text-rose-300 flex items-center gap-3 max-w-md">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <span className="text-sm">Error initializing command center: {error}</span>
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
  const pendingResolutionCount = issues.filter((i) => i.status !== 'RESOLVED').length

  return (
    <div className="h-full flex flex-col overflow-y-auto p-5 sm:p-7 space-y-6 font-sans">
      {/* 1. Executive Operations Header */}
      <div className="p-6 bg-[#0c1018] border border-slate-800/90 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-5 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-2 h-full bg-cyan-500 shadow-[0_0_15px_#06b6d4]" />
        
        <div className="space-y-1.5 pl-2">
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Sparkles className="w-6 h-6 text-cyan-400" />
            <span>Civic Intelligence Operations</span>
          </h1>
          <p className="text-slate-400 text-sm sm:text-base max-w-3xl leading-relaxed">
            AI-powered multi-modal issue detection, dynamic priority advisory, and computer vision cross-validation.
          </p>
        </div>

        <div className="flex items-center gap-3.5 shrink-0 pl-2 md:pl-0">
          <button
            onClick={() => {
              if (onStartDemo) onStartDemo()
              else onNavigate('analyze')
            }}
            className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold tracking-wide shadow-lg shadow-cyan-950/60 transition active:scale-95 cursor-pointer"
          >
            <Sparkles className="w-4 h-4 text-cyan-200" />
            <span>Analyze Issue</span>
          </button>

          <div className="hidden sm:flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#101622] border border-slate-800 text-emerald-400 text-xs font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Inference Engine Online</span>
          </div>
        </div>
      </div>

      {/* 2. Four Prominent Primary KPI Cards with Staggered Entrance */}
      <motion.div
        variants={kpiContainerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5"
      >
        <KpiCard
          variants={kpiItemVariants}
          title="Total Monitored Issues"
          value={<AnimatedCounter value={totalIssues} />}
          subtitle="Active civic complaints & sensor detections"
          accentColor="slate"
          icon={Layers}
        />

        <KpiCard
          variants={kpiItemVariants}
          title="High & Critical Priority"
          value={<AnimatedCounter value={highPriorityCount} />}
          subtitle="Require urgent municipal dispatch"
          accentColor="red"
          icon={ShieldAlert}
          delta={highPriorityCount > 0 ? 'CRITICAL DISPATCH' : 'NOMINAL'}
          deltaType={highPriorityCount > 0 ? 'critical' : 'positive'}
        />

        <KpiCard
          variants={kpiItemVariants}
          title="Unreported Discoveries"
          value={<AnimatedCounter value={unreportedCount} />}
          subtitle="Proactive patrol camera survey detections"
          accentColor="cyan"
          icon={Camera}
          onClick={() => onNavigate('unreported')}
        />

        <KpiCard
          variants={kpiItemVariants}
          title="Active Spatiotemporal Hotspots"
          value={<AnimatedCounter value={hotspotsCount} />}
          subtitle="High-density Haversine DBSCAN clusters"
          accentColor="orange"
          icon={Flame}
          onClick={() => onNavigate('hotspots')}
        />
      </motion.div>

      {/* Secondary Operational Metrics Bar */}
      <div className="px-5 py-3.5 bg-[#0b0f17] border border-slate-800/80 rounded-xl flex flex-wrap items-center justify-between gap-4 text-xs shadow-md">
        <div className="flex items-center gap-6 flex-wrap">
          <div className="flex items-center gap-2 cursor-pointer hover:text-white transition" onClick={() => onNavigate('recurring')}>
            <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-slate-400">Recurring Chronic Sites:</span>
            <strong className="text-slate-200 font-mono">{recurringCount} Locations</strong>
          </div>

          <div className="flex items-center gap-2 cursor-pointer hover:text-white transition" onClick={() => onNavigate('resolution')}>
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">Pending Resolution:</span>
            <strong className="text-slate-200 font-mono">{pendingResolutionCount} Work Orders</strong>
          </div>

          <div className="hidden md:flex items-center gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400">AI Inspection Pass Rate:</span>
            <strong className="text-cyan-300 font-mono">94.2%</strong>
          </div>
        </div>

        <div className="flex items-center gap-2 text-slate-400">
          <span>Mean Response SLA:</span>
          <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-200 font-mono font-bold">4.0 Hours</span>
        </div>
      </div>

      {/* 3. Main Stage: Large Tactical Map & Live Priority Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[580px]">
        {/* Large Interactive Map (Tactical GIS) */}
        <div className="lg:col-span-7 bg-[#0b0f17] border border-slate-800 rounded-2xl p-4 sm:p-5 flex flex-col shadow-2xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 mb-3 border-b border-slate-800/80 gap-3">
            <div className="flex items-center gap-2.5">
              <MapPin className="w-5 h-5 text-cyan-400" />
              <div>
                <h2 className="font-bold text-slate-100 text-sm sm:text-base tracking-wide">
                  Tactical GIS Spatial Intelligence
                </h2>
                <p className="text-slate-400 text-xs">
                  Real-time municipal incident map with priority heat & hotspot boundaries
                </p>
              </div>
            </div>

            {/* Layer Toggles & Workspace Link */}
            <div className="flex items-center gap-2 shrink-0">
              <div className="flex items-center bg-[#101622] p-0.5 rounded-lg border border-slate-800 text-xs">
                {(['markers', 'clusters', 'hotspots', 'heatmap'] as MapLayerMode[]).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setMapLayer(mode)}
                    className={cn(
                      'px-2.5 py-1 rounded-md capitalize font-medium transition cursor-pointer',
                      mapLayer === mode
                        ? 'bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800/60 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200'
                    )}
                  >
                    {mode}
                  </button>
                ))}
              </div>

              <button
                onClick={() => onNavigate('map')}
                className="text-cyan-400 hover:text-cyan-300 text-xs font-semibold px-2.5 py-1 hover:bg-[#101622] rounded-lg transition flex items-center gap-1 cursor-pointer"
              >
                <span>Full View</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="flex-1 w-full min-h-[460px] rounded-xl overflow-hidden border border-slate-800/90 relative">
            <ErrorBoundary fallbackTitle="Tactical GIS Spatial Layer Loading">
              <CivicMap
                issues={issues}
                hotspots={hotspots}
                layerMode={mapLayer}
                onSelectIssue={onSelectIssue}
                className="h-full w-full"
              />
            </ErrorBoundary>
          </div>
        </div>

        {/* Live Priority Feed */}
        <div className="lg:col-span-5 bg-[#0b0f17] border border-slate-800 rounded-2xl p-4 sm:p-5 flex flex-col shadow-2xl">
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-800/80">
            <div className="flex items-center gap-2.5">
              <Activity className="w-5 h-5 text-rose-500 animate-pulse" />
              <div>
                <h2 className="font-bold text-slate-100 text-sm sm:text-base tracking-wide">
                  Live Priority Incident Feed
                </h2>
                <p className="text-slate-400 text-xs">
                  Ranked by multimodal urgency, severity, and risk score
                </p>
              </div>
            </div>

            <span className="text-xs text-slate-400 font-mono">
              Top {Math.min(6, issues.length)} Ranked
            </span>
          </div>

          {/* Feed List */}
          <div className="flex-1 overflow-y-auto space-y-3.5 pr-1">
            {issues.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm text-center p-8">
                No priority incidents in intake queue.
              </div>
            ) : (
              <motion.div
                variants={feedContainerVariants}
                initial="hidden"
                animate="visible"
                className="space-y-3.5"
              >
                {issues.slice(0, 6).map((issue) => {
                  const isCritical = issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
                  const isHigh = issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
                  const isMedium = issue.priorityLevel === 'MEDIUM' || issue.priorityScore >= 40

                  let priorityBadgeBg = 'bg-emerald-950/80 text-emerald-300 border-emerald-800'
                  if (isCritical) {
                    priorityBadgeBg = 'bg-rose-950/90 text-rose-200 border-rose-700 shadow-sm'
                  } else if (isHigh) {
                    priorityBadgeBg = 'bg-orange-950/80 text-orange-200 border-orange-700'
                  } else if (isMedium) {
                    priorityBadgeBg = 'bg-amber-950/80 text-amber-200 border-amber-700'
                  }

                  return (
                    <motion.div
                      key={issue.issueId}
                      variants={feedItemVariants}
                      whileHover={{ y: -2, x: 2, transition: { duration: 0.15 } }}
                      whileTap={{ scale: 0.99 }}
                      onClick={() => onSelectIssue(issue)}
                      className={cn(
                        'p-4 rounded-xl border transition-all duration-200 cursor-pointer shadow-md group relative overflow-hidden',
                        isCritical
                          ? 'bg-[#121622] hover:bg-[#161c2c] border-rose-900/60 hover:border-rose-500/80'
                          : 'bg-[#0f1420] hover:bg-[#131928] border-slate-800/90 hover:border-slate-700'
                      )}
                    >
                      {/* Left Accent indicator */}
                      <div
                        className={cn(
                          'absolute top-0 bottom-0 left-0 w-1',
                          isCritical ? 'bg-rose-500 shadow-[0_0_8px_#f43f5e]' : isHigh ? 'bg-orange-500' : 'bg-cyan-500'
                        )}
                      />

                      {/* Card Header: Priority Level, Score, Category, Status */}
                      <div className="flex items-start justify-between gap-3 mb-2 pl-1.5">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span
                            className={cn(
                              'text-xs font-bold font-mono px-2.5 py-0.5 rounded-md border tracking-wider uppercase',
                              priorityBadgeBg
                            )}
                          >
                            {issue.priorityLevel}
                          </span>

                          <span className="text-sm font-bold text-slate-100">
                            {issue.category}
                          </span>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          <div className="text-right">
                            <span className="text-xs font-mono font-bold text-cyan-400">
                              Priority {issue.priorityScore.toFixed(0)}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Body: Complaint Description (High legibility 14px text) */}
                      <p className="text-sm text-slate-300 leading-relaxed font-sans mb-3 pl-1.5 line-clamp-2 group-hover:text-white transition-colors">
                        {issue.complaintText}
                      </p>

                      {/* Card Footer: Location, Evidence Consistency, Workflow Status */}
                      <div className="flex flex-wrap items-center justify-between gap-2.5 pt-2.5 border-t border-slate-800/80 pl-1.5 text-xs text-slate-400">
                        <div className="flex items-center gap-1.5 truncate max-w-[240px]">
                          <MapPin className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                          <span className="truncate">{issue.location}</span>
                          {issue.ward && (
                            <span className="text-slate-500 font-mono shrink-0">({issue.ward})</span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {issue.consistencyDetail ? (
                            <ConsistencyBadge
                              level={issue.consistencyDetail.consistencyLevel}
                              score={issue.consistencyDetail.consistencyScore}
                            />
                          ) : issue.consistencyFlag ? (
                            <ConsistencyBadge
                              level={issue.consistencyFlag}
                              score={issue.evidenceConsistency}
                            />
                          ) : null}
                          <StatusBadge status={issue.status} />
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default OverviewView
