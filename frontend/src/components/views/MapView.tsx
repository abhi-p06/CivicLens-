import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Layers,
  Flame,
  ShieldAlert,
  MapPin,
  Filter,
  Calendar,
  X,
  Eye,
  CheckCircle2,
  Radar,
  Activity,
  ArrowRight,
  TrendingUp,
  Building,
  RotateCcw,
  Sparkles,
  Compass,
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { CivicMap, MapLayerMode } from '../map/CivicMap'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { cn } from '../../lib/utils'

interface MapViewProps {
  issues: Issue[]
  hotspots: HotspotInfo[]
  recurringIssues: RecurrenceInfo[]
  onSelectIssue: (issue: Issue) => void
}

export const MapView: React.FC<MapViewProps> = ({
  issues,
  hotspots,
  recurringIssues,
  onSelectIssue,
}) => {
  // Layer & Display Controls
  const [layerMode, setLayerMode] = useState<MapLayerMode>('markers')
  const [showHotspotBoundaries, setShowHotspotBoundaries] = useState(true)

  // Multi-Filter State
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL')
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL')
  const [selectedDateHorizon, setSelectedDateHorizon] = useState<string>('ALL')

  // Selected Entities
  const [inspectingIssue, setInspectingIssue] = useState<Issue | null>(null)
  const [inspectingHotspot, setInspectingHotspot] = useState<HotspotInfo | null>(null)

  // Categories list
  const categories = [
    'ALL',
    'Roads & Footpaths',
    'Sanitation & Garbage',
    'Water Supply & Drainage',
    'Street Lighting',
    'Storm Water Drains',
    'Traffic & Safety',
  ]

  // Filtered Issues Calculation
  const filteredIssues = useMemo(() => {
    const now = new Date().getTime()

    return issues.filter((i) => {
      // 1. Category Filter
      const matchCat = selectedCategory === 'ALL' || i.category === selectedCategory

      // 2. Priority Filter
      let matchPri = true
      if (selectedPriority === 'CRITICAL') {
        matchPri = i.priorityLevel === 'CRITICAL' || i.priorityScore >= 80
      } else if (selectedPriority === 'HIGH') {
        matchPri = i.priorityLevel === 'HIGH' || (i.priorityScore >= 65 && i.priorityScore < 80)
      } else if (selectedPriority === 'MEDIUM') {
        matchPri = i.priorityLevel === 'MEDIUM' || (i.priorityScore >= 40 && i.priorityScore < 65)
      } else if (selectedPriority === 'LOW') {
        matchPri = i.priorityLevel === 'LOW' || i.priorityScore < 40
      }

      // 3. Status Filter
      const matchStat = selectedStatus === 'ALL' || i.status === selectedStatus

      // 4. Date Filter
      let matchDate = true
      if (selectedDateHorizon !== 'ALL') {
        const issueTime = new Date(i.timestamp).getTime()
        const diffHours = (now - issueTime) / (1000 * 60 * 60)
        if (selectedDateHorizon === '24H') matchDate = diffHours <= 24
        if (selectedDateHorizon === '7D') matchDate = diffHours <= 24 * 7
        if (selectedDateHorizon === '30D') matchDate = diffHours <= 24 * 30
      }

      return matchCat && matchPri && matchStat && matchDate
    })
  }, [issues, selectedCategory, selectedPriority, selectedStatus, selectedDateHorizon])

  // Reset all filters
  const resetFilters = () => {
    setSelectedCategory('ALL')
    setSelectedPriority('ALL')
    setSelectedStatus('ALL')
    setSelectedDateHorizon('ALL')
  }

  const isFiltered =
    selectedCategory !== 'ALL' ||
    selectedPriority !== 'ALL' ||
    selectedStatus !== 'ALL' ||
    selectedDateHorizon !== 'ALL'

  // Handling Issue Selection
  const handleMarkerClick = (issue: Issue) => {
    setInspectingHotspot(null)
    setInspectingIssue(issue)
  }

  // Handling Hotspot Selection
  const handleHotspotClick = (hotspot: HotspotInfo) => {
    setInspectingIssue(null)
    setInspectingHotspot(hotspot)
  }

  // Find recurrence info for inspectingIssue if available
  const activeRecurrence = useMemo(() => {
    if (!inspectingIssue) return null
    return (
      recurringIssues.find(
        (r) =>
          r.location.toLowerCase().includes(inspectingIssue.location.toLowerCase()) ||
          inspectingIssue.location.toLowerCase().includes(r.location.toLowerCase())
      ) || null
    )
  }, [inspectingIssue, recurringIssues])

  return (
    <div className="relative h-full w-full flex flex-col font-sans text-sm select-none overflow-hidden bg-[#10162A]">
      {/* ------------------------------------------------------------- */}
      {/* TOP FLOATING HUD: LAYER CONTROLS & MULTI-FILTERS             */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute top-4 left-4 right-4 z-30 flex flex-wrap items-center justify-between gap-3 bg-[#13152E]/95 backdrop-blur-md px-4 py-3 rounded-2xl border border-[#212348] shadow-xl">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Brand & Workspace Badge */}
          <div className="flex items-center gap-2 px-2.5 py-1 bg-[#1D1B48] rounded-lg border border-[#2C2964] text-white font-semibold text-xs">
            <Compass className="w-3.5 h-3.5 text-[#8B5CF6]" />
            <span>GIS Map</span>
          </div>

          {/* Layer Mode Switcher */}
          <div className="flex items-center gap-1 bg-[#1D1B48] p-0.5 rounded-lg border border-[#2C2964]">
            <button
              onClick={() => setLayerMode('markers')}
              className={cn(
                'px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition cursor-pointer',
                layerMode === 'markers'
                  ? 'bg-[#6457E8] text-white shadow-xs'
                  : 'text-slate-300 hover:text-white'
              )}
              title="Individual incident pins"
            >
              <MapPin className="w-3 h-3" />
              <span>Pins</span>
            </button>

            <button
              onClick={() => setLayerMode('clusters')}
              className={cn(
                'px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition cursor-pointer',
                layerMode === 'clusters'
                  ? 'bg-[#6457E8] text-white shadow-xs'
                  : 'text-slate-300 hover:text-white'
              )}
              title="Marker proximity clustering"
            >
              <Layers className="w-3 h-3" />
              <span>Clusters</span>
            </button>

            <button
              onClick={() => setLayerMode('heatmap')}
              className={cn(
                'px-2.5 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition cursor-pointer',
                layerMode === 'heatmap'
                  ? 'bg-[#F97316] text-white shadow-xs'
                  : 'text-slate-300 hover:text-white'
              )}
              title="Priority density heatmap"
            >
              <Flame className="w-3 h-3" />
              <span>Heatmap</span>
            </button>
          </div>

          {/* Hotspot Boundaries Layer Toggle */}
          <button
            onClick={() => setShowHotspotBoundaries(!showHotspotBoundaries)}
            className={cn(
              'px-2.5 py-1.5 rounded-lg text-xs font-medium border flex items-center gap-1.5 transition cursor-pointer',
              showHotspotBoundaries
                ? 'bg-[#EF4444]/20 border-[#EF4444]/40 text-[#FCA5A5]'
                : 'bg-[#1D1B48] border-[#2C2964] text-slate-300'
            )}
            title="Toggle DBSCAN Hotspot circles"
          >
            <Radar className="w-3.5 h-3.5 text-[#EF4444]" />
            <span>Hotspots ({hotspots.length})</span>
          </button>

          {/* Separator */}
          <div className="h-4 w-px bg-[#212348] hidden md:block" />

          {/* Category Dropdown */}
          <div className="flex items-center gap-1 bg-[#1D1B48] border border-[#2C2964] rounded-lg px-2.5 py-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Cat:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer max-w-[120px] truncate"
            >
              {categories.map((c) => (
                <option key={c} value={c} className="bg-[#13152E]">
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Toggle Pills */}
          <div className="flex items-center gap-1">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => {
              const isActive = selectedPriority === lvl
              return (
                <button
                  key={lvl}
                  onClick={() => setSelectedPriority(lvl)}
                  className={cn(
                    'px-2 py-0.5 rounded-md text-[10px] font-semibold border transition cursor-pointer',
                    isActive
                      ? lvl === 'CRITICAL'
                        ? 'bg-[#EF4444] border-[#EF4444] text-white'
                        : lvl === 'HIGH'
                        ? 'bg-[#F97316] border-[#F97316] text-white'
                        : lvl === 'MEDIUM'
                        ? 'bg-[#EAB308] border-[#EAB308] text-white'
                        : lvl === 'LOW'
                        ? 'bg-[#10B981] border-[#10B981] text-white'
                        : 'bg-[#6457E8] border-[#6457E8] text-white'
                      : 'bg-[#1D1B48] border-[#2C2964] text-slate-300 hover:text-white'
                  )}
                >
                  {lvl}
                </button>
              )
            })}
          </div>

          {/* Status Dropdown */}
          <div className="flex items-center gap-1 bg-[#1D1B48] border border-[#2C2964] rounded-lg px-2.5 py-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer"
            >
              {['ALL', 'OPEN', 'ANALYZED', 'PRIORITIZED', 'ASSIGNED', 'ACTION IN PROGRESS', 'VERIFICATION', 'RESOLVED'].map((s) => (
                <option key={s} value={s} className="bg-[#13152E]">
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Date Horizon Filter */}
          <div className="flex items-center gap-1 bg-[#1D1B48] border border-[#2C2964] rounded-lg px-2.5 py-1">
            <Calendar className="w-3 h-3 text-slate-400" />
            <select
              value={selectedDateHorizon}
              onChange={(e) => setSelectedDateHorizon(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-[#13152E]">All Time</option>
              <option value="24H" className="bg-[#13152E]">Past 24 Hours</option>
              <option value="7D" className="bg-[#13152E]">Past 7 Days</option>
              <option value="30D" className="bg-[#13152E]">Past 30 Days</option>
            </select>
          </div>
        </div>

        {/* Counter & Filter Reset */}
        <div className="flex items-center gap-2">
          {isFiltered && (
            <button
              onClick={resetFilters}
              className="px-2.5 py-1 rounded-lg bg-[#1D1B48] hover:bg-[#2C2964] text-slate-200 text-[11px] border border-[#2C2964] flex items-center gap-1 transition cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}

          <div className="px-3 py-1 bg-[#1D1B48] rounded-lg border border-[#2C2964] text-[11px] font-mono text-[#A5B4FC]">
            <strong className="text-white">{filteredIssues.length}</strong> / {issues.length} Visible
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* FULL-VIEWPORT PRIMARY MAP CANVAS                              */}
      {/* ------------------------------------------------------------- */}
      <div className="flex-1 w-full h-full relative">
        <CivicMap
          issues={filteredIssues}
          hotspots={hotspots}
          layerMode={layerMode}
          showHotspotBoundaries={showHotspotBoundaries}
          selectedIssue={inspectingIssue}
          onSelectIssue={handleMarkerClick}
          selectedHotspot={inspectingHotspot}
          onSelectHotspot={handleHotspotClick}
          className="h-full w-full"
        />
      </div>

      {/* ------------------------------------------------------------- */}
      {/* RIGHT SIDE PANEL: ISSUE INTELLIGENCE DOSSIER                   */}
      {/* ------------------------------------------------------------- */}
      <AnimatePresence>
        {inspectingIssue && (
          <motion.div
            initial={{ opacity: 0, x: 80 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 80 }}
            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
            className="absolute top-16 bottom-12 right-4 w-96 z-30 bg-[#13152E]/95 backdrop-blur-md rounded-2xl border border-[#212348] shadow-2xl flex flex-col overflow-hidden font-mono text-xs"
          >
            {/* Header */}
            <div className="p-3.5 bg-[#1D1B48] border-b border-[#212348] flex items-center justify-between shrink-0">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-[#8B5CF6] text-sm">
                    {inspectingIssue.issueId}
                  </span>
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded text-[10px] font-bold border uppercase',
                      inspectingIssue.priorityLevel === 'CRITICAL'
                        ? 'bg-[#EF4444]/20 border-[#EF4444]/50 text-[#FCA5A5]'
                        : inspectingIssue.priorityLevel === 'HIGH'
                        ? 'bg-[#F97316]/20 border-[#F97316]/50 text-[#FDBA74]'
                        : inspectingIssue.priorityLevel === 'MEDIUM'
                        ? 'bg-[#EAB308]/20 border-[#EAB308]/50 text-[#FDE047]'
                        : 'bg-[#10B981]/20 border-[#10B981]/50 text-[#6EE7B7]'
                    )}
                  >
                    {inspectingIssue.priorityLevel}
                  </span>
                </div>
                <div className="text-[10px] text-slate-300 mt-0.5 font-sans">
                  {inspectingIssue.location} &bull; {inspectingIssue.ward}
                </div>
              </div>

              <button
                onClick={() => setInspectingIssue(null)}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#212348] transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 font-sans">
              {/* 1. Category */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964]">
                <div className="text-[9px] uppercase font-bold text-slate-400">1. Category</div>
                <div className="font-bold text-white text-sm mt-0.5">
                  {inspectingIssue.category}
                </div>
              </div>

              {/* 2. Priority & 3. Severity */}
              <div className="p-3 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964]">
                <PriorityGauge
                  score={inspectingIssue.priorityScore}
                  level={inspectingIssue.priorityLevel}
                  breakdown={inspectingIssue.priorityBreakdown}
                />
              </div>

              {/* 4. Status */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] flex items-center justify-between">
                <div>
                  <div className="text-[9px] uppercase font-bold text-slate-400">4. Status</div>
                  <div className="mt-1">
                    <StatusBadge status={inspectingIssue.status} />
                  </div>
                </div>
                <div className="text-right font-mono">
                  <div className="text-[9px] uppercase text-slate-400">SLA Target</div>
                  <div className="font-bold text-[#8B5CF6] text-xs mt-0.5">
                    {inspectingIssue.slaHours} Hours
                  </div>
                </div>
              </div>

              {/* 5. Nearby Reports */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">5. Nearby Reports</div>
                <div className="flex items-center justify-between text-slate-200">
                  <span className="text-xs">Spatial Duplicate Cluster:</span>
                  <span className="font-bold text-[#F97316] text-xs">
                    {inspectingIssue.isDuplicate ? 'Merged' : 'Isolated Incident'}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  {inspectingIssue.duplicateGroupId
                    ? `Cluster ID: ${inspectingIssue.duplicateGroupId}`
                    : 'No adjacent duplicate reports registered.'}
                </div>
              </div>

              {/* 6. Recurrence */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">6. Recurrence</div>
                <div className="flex items-center justify-between text-slate-200">
                  <span className="text-xs">Chronic Site Index:</span>
                  <span className="font-bold text-[#8B5CF6] text-xs">
                    {activeRecurrence ? `${activeRecurrence.recurrenceScore.toFixed(0)}/100` : 'None / 0'}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400">
                  {activeRecurrence
                    ? `Reported ${activeRecurrence.reportCount} times historically &bull; Trend: ${activeRecurrence.trend}`
                    : 'No repeated chronic pattern recorded at this coordinate.'}
                </div>
              </div>

              {/* 7. Department */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">7. Department</div>
                <div className="flex items-center gap-2 text-white font-bold text-xs">
                  <Building className="w-3.5 h-3.5 text-[#8B5CF6]" />
                  <span>{inspectingIssue.department}</span>
                </div>
                <div className="text-[10px] text-slate-300 font-sans mt-1">
                  {inspectingIssue.recommendedAction}
                </div>
              </div>

              {/* Complaint Excerpt */}
              <div className="p-2.5 bg-[#10162A] rounded-xl border border-[#2C2964] font-sans text-xs text-slate-200 leading-relaxed">
                "{inspectingIssue.complaintText}"
              </div>
            </div>

            {/* Footer Action */}
            <div className="p-3 bg-[#1D1B48] border-t border-[#212348] shrink-0 font-sans">
              <button
                onClick={() => onSelectIssue(inspectingIssue)}
                className="w-full py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
              >
                <span>Open Intelligence Dossier</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ------------------------------------------------------------- */}
      {/* RIGHT SIDE PANEL: HOTSPOT INTELLIGENCE DOSSIER                */}
      {/* ------------------------------------------------------------- */}
      <AnimatePresence>
        {inspectingHotspot && (
          <motion.div
            initial={{ opacity: 0, x: 80 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 80 }}
            transition={{ type: 'spring', damping: 28, stiffness: 350 }}
            className="absolute top-16 bottom-12 right-4 w-96 z-30 bg-[#13152E]/95 backdrop-blur-md rounded-2xl border border-[#EF4444]/40 shadow-2xl flex flex-col overflow-hidden font-mono text-xs"
          >
            {/* Header */}
            <div className="p-3.5 bg-[#1D1B48] border-b border-[#EF4444]/30 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Radar className="w-4 h-4 text-[#EF4444] animate-spin" style={{ animationDuration: '6s' }} />
                <div>
                  <span className="font-bold text-[#FCA5A5] text-sm">
                    {inspectingHotspot.hotspotId}
                  </span>
                  <div className="text-[10px] text-[#EF4444] font-bold">
                    DBSCAN SPATIAL CLUSTER &bull; {inspectingHotspot.hotspotLevel}
                  </div>
                </div>
              </div>

              <button
                onClick={() => setInspectingHotspot(null)}
                className="p-1 rounded text-slate-400 hover:text-white hover:bg-[#212348] transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5 font-sans">
              {/* 1. Hotspot Boundary */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">1. Hotspot Boundary</div>
                <div className="font-bold text-white text-xs">
                  Radius: {inspectingHotspot.radiusMeters} Meters
                </div>
                <div className="text-[10px] text-slate-300 font-mono">
                  Centroid: {(typeof inspectingHotspot.center?.lat === 'number' ? inspectingHotspot.center.lat : Array.isArray(inspectingHotspot.center) ? Number(inspectingHotspot.center[0]) : 19.076).toFixed(4)}° N, {(typeof inspectingHotspot.center?.lng === 'number' ? inspectingHotspot.center.lng : Array.isArray(inspectingHotspot.center) ? Number(inspectingHotspot.center[1]) : 72.885).toFixed(4)}° E
                </div>
              </div>

              {/* 2. Issue Count */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] flex items-center justify-between">
                <div>
                  <div className="text-[9px] uppercase font-bold text-slate-400">2. Incident Count</div>
                  <div className="font-bold text-white text-lg mt-0.5 font-mono">
                    {inspectingHotspot.issueCount} <span className="text-xs text-slate-300 font-sans">Reports</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded bg-[#EF4444]/20 text-[#FCA5A5] border border-[#EF4444]/40 text-[10px] font-bold uppercase">
                    Active Density
                  </span>
                </div>
              </div>

              {/* 3. Dominant Issue */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">3. Dominant Issue</div>
                <div className="font-bold text-white text-sm">
                  {inspectingHotspot.dominantCategory}
                </div>
                <div className="text-[10px] text-slate-300">
                  Accounts for the majority of citizen grievances in this zone.
                </div>
              </div>

              {/* 4. Growth */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] flex items-center justify-between">
                <div>
                  <div className="text-[9px] uppercase font-bold text-slate-400">4. Period Growth Rate</div>
                  <div className="font-bold text-[#FCA5A5] text-lg mt-0.5 font-mono">
                    {inspectingHotspot.growthRate > 0 ? '+' : ''}{inspectingHotspot.growthRate}%
                  </div>
                </div>
                <TrendingUp className="w-5 h-5 text-[#EF4444]" />
              </div>

              {/* 5. Priority */}
              <div className="p-2.5 bg-[#1D1B48]/80 rounded-xl border border-[#2C2964] space-y-1">
                <div className="text-[9px] uppercase font-bold text-slate-400">5. Average Cluster Priority</div>
                <div className="font-bold text-[#8B5CF6] text-lg font-mono">
                  {inspectingHotspot.averagePriority.toFixed(1)} / 100
                </div>
                <div className="text-[10px] text-slate-300">
                  High civic urgency requires ward officer taskforce mobilization.
                </div>
              </div>
            </div>

            {/* Action */}
            <div className="p-3 bg-[#1D1B48] border-t border-[#212348] shrink-0 font-sans">
              <button
                onClick={() => {
                  setSelectedCategory(inspectingHotspot.dominantCategory)
                  setInspectingHotspot(null)
                }}
                className="w-full py-2 bg-[#EF4444] hover:bg-[#DC2626] text-white rounded-xl font-bold text-xs flex items-center justify-center gap-1.5 shadow-md transition cursor-pointer"
              >
                <span>Filter Cluster Incidents</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ------------------------------------------------------------- */}
      {/* BOTTOM FLOATING MAP LEGEND BAR                                */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute bottom-3 left-3 z-20 flex items-center gap-3 bg-[#13152E]/95 backdrop-blur-md px-3.5 py-2 rounded-xl border border-[#212348] text-[11px] text-slate-300 shadow-xl">
        <span className="font-bold text-white uppercase text-[10px]">LEGEND:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444] animate-ping inline-block" />
          <span className="text-[#FCA5A5] font-semibold">Critical (≥80)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#F97316] inline-block" />
          <span className="text-slate-300">High (≥65)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#EAB308] inline-block" />
          <span className="text-slate-300">Medium (≥40)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-[#10B981] inline-block" />
          <span className="text-slate-300">Low (&lt;40)</span>
        </div>
        <div className="flex items-center gap-1.5 border-l border-[#212348] pl-2.5">
          <span className="w-2.5 h-2.5 rounded-full border border-dashed border-[#EF4444] inline-block" />
          <span className="text-[#FCA5A5]">DBSCAN Hotspot Boundary</span>
        </div>
      </div>
    </div>
  )
}

export default MapView
