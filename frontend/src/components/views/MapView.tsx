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
    <div className="relative h-full w-full flex flex-col font-mono text-xs select-none overflow-hidden bg-[#080a0f]">
      {/* ------------------------------------------------------------- */}
      {/* TOP FLOATING HUD: LAYER CONTROLS & MULTI-FILTERS             */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute top-3 left-3 right-3 z-30 flex flex-wrap items-center justify-between gap-2.5 bg-[#0b0f19]/90 backdrop-blur-md px-3 py-2.5 rounded-xl border border-slate-800 shadow-2xl">
        <div className="flex flex-wrap items-center gap-2">
          {/* Brand & Workspace Badge */}
          <div className="flex items-center gap-1.5 px-2 py-1 bg-[#121824] rounded border border-cyan-900/60 text-cyan-300 font-bold text-[11px]">
            <Compass className="w-3.5 h-3.5 text-cyan-400 animate-spin" style={{ animationDuration: '12s' }} />
            <span>TACTICAL GIS</span>
          </div>

          {/* Layer Mode Switcher */}
          <div className="flex items-center gap-1 bg-[#121824] p-0.5 rounded border border-slate-800">
            <button
              onClick={() => setLayerMode('markers')}
              className={cn(
                'px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition',
                layerMode === 'markers'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              )}
              title="Individual incident pins"
            >
              <MapPin className="w-3 h-3" />
              <span>Pins</span>
            </button>

            <button
              onClick={() => setLayerMode('clusters')}
              className={cn(
                'px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition',
                layerMode === 'clusters'
                  ? 'bg-cyan-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
              )}
              title="Marker proximity clustering"
            >
              <Layers className="w-3 h-3" />
              <span>Clusters</span>
            </button>

            <button
              onClick={() => setLayerMode('heatmap')}
              className={cn(
                'px-2 py-1 rounded text-[10px] font-bold flex items-center gap-1 transition',
                layerMode === 'heatmap'
                  ? 'bg-orange-600 text-white shadow'
                  : 'text-slate-400 hover:text-slate-200'
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
              'px-2.5 py-1 rounded text-[10px] font-bold border flex items-center gap-1 transition',
              showHotspotBoundaries
                ? 'bg-rose-950/70 border-rose-800 text-rose-300'
                : 'bg-[#121824] border-slate-800 text-slate-500'
            )}
            title="Toggle DBSCAN Hotspot circles"
          >
            <Radar className="w-3 h-3 text-rose-400" />
            <span>Hotspots ({hotspots.length})</span>
          </button>

          {/* Separator */}
          <div className="h-4 w-px bg-slate-800 hidden md:block" />

          {/* Category Dropdown */}
          <div className="flex items-center gap-1 bg-[#121824] border border-slate-800 rounded px-2 py-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Cat:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer max-w-[120px] truncate"
            >
              {categories.map((c) => (
                <option key={c} value={c} className="bg-[#0e131d]">
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Toggle Pills */}
          <div className="flex items-center gap-1">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedPriority(lvl)}
                className={cn(
                  'px-1.5 py-0.5 rounded text-[10px] font-bold border transition',
                  selectedPriority === lvl
                    ? lvl === 'CRITICAL'
                      ? 'bg-rose-950 border-rose-600 text-rose-300'
                      : lvl === 'HIGH'
                      ? 'bg-orange-950 border-orange-600 text-orange-300'
                      : 'bg-cyan-950 border-cyan-500 text-cyan-300'
                    : 'bg-[#121824] border-slate-800 text-slate-400 hover:text-slate-200'
                )}
              >
                {lvl}
              </button>
            ))}
          </div>

          {/* Status Dropdown */}
          <div className="flex items-center gap-1 bg-[#121824] border border-slate-800 rounded px-2 py-1">
            <span className="text-[10px] text-slate-500 uppercase font-bold">Status:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer"
            >
              {['ALL', 'OPEN', 'ANALYZED', 'PRIORITIZED', 'ASSIGNED', 'ACTION IN PROGRESS', 'VERIFICATION', 'RESOLVED'].map((s) => (
                <option key={s} value={s} className="bg-[#0e131d]">
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Date Horizon Filter */}
          <div className="flex items-center gap-1 bg-[#121824] border border-slate-800 rounded px-2 py-1">
            <Calendar className="w-3 h-3 text-slate-500" />
            <select
              value={selectedDateHorizon}
              onChange={(e) => setSelectedDateHorizon(e.target.value)}
              className="bg-transparent text-slate-200 text-[11px] outline-none cursor-pointer"
            >
              <option value="ALL" className="bg-[#0e131d]">All Time</option>
              <option value="24H" className="bg-[#0e131d]">Past 24 Hours</option>
              <option value="7D" className="bg-[#0e131d]">Past 7 Days</option>
              <option value="30D" className="bg-[#0e131d]">Past 30 Days</option>
            </select>
          </div>
        </div>

        {/* Counter & Filter Reset */}
        <div className="flex items-center gap-2">
          {isFiltered && (
            <button
              onClick={resetFilters}
              className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] border border-slate-700 flex items-center gap-1 transition"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}

          <div className="px-2.5 py-1 bg-[#101622] rounded border border-slate-800 text-[10px] font-mono text-cyan-400">
            <strong>{filteredIssues.length}</strong> / {issues.length} Visible
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
            className="absolute top-16 bottom-12 right-4 w-96 z-30 bg-[#0c1018]/95 backdrop-blur-md rounded-xl border border-cyan-800/80 shadow-2xl flex flex-col overflow-hidden font-mono text-xs"
          >
            {/* Header */}
            <div className="p-3.5 bg-[#0f1422] border-b border-slate-800 flex items-center justify-between shrink-0">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-bold text-cyan-400 text-sm">
                    {inspectingIssue.issueId}
                  </span>
                  <span
                    className={cn(
                      'px-1.5 py-0.5 rounded text-[10px] font-bold border uppercase',
                      inspectingIssue.priorityLevel === 'CRITICAL'
                        ? 'bg-rose-950 border-rose-700 text-rose-300'
                        : inspectingIssue.priorityLevel === 'HIGH'
                        ? 'bg-orange-950 border-orange-700 text-orange-300'
                        : 'bg-amber-950 border-amber-700 text-amber-300'
                    )}
                  >
                    {inspectingIssue.priorityLevel}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {inspectingIssue.location} &bull; {inspectingIssue.ward}
                </div>
              </div>

              <button
                onClick={() => setInspectingIssue(null)}
                className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {/* 1. Category */}
            <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
              <div className="text-[9px] uppercase font-bold text-slate-400">1. Category</div>
              <div className="font-bold text-slate-100 text-sm mt-0.5">
                {inspectingIssue.category}
              </div>
            </div>

            {/* 2. Priority & 3. Severity */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                <div className="text-[9px] uppercase font-bold text-slate-400">2. Priority Score</div>
                <div className="font-bold text-cyan-300 text-base mt-0.5">
                  {inspectingIssue.priorityScore.toFixed(0)} <span className="text-[10px] text-slate-500">/ 100</span>
                </div>
              </div>

              <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800">
                <div className="text-[9px] uppercase font-bold text-slate-400">3. Severity</div>
                <div className="font-bold text-rose-400 text-base mt-0.5">
                  {(inspectingIssue.severity * 100).toFixed(0)}% <span className="text-[10px] text-slate-500">Score</span>
                </div>
              </div>
            </div>

            {/* 4. Status */}
            <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-[9px] uppercase font-bold text-slate-400">4. Status</div>
                <div className="mt-1">
                  <StatusBadge status={inspectingIssue.status} />
                </div>
              </div>
              <div className="text-right">
                <div className="text-[9px] uppercase text-slate-400">SLA Target</div>
                <div className="font-bold text-cyan-400 text-xs mt-0.5">
                  {inspectingIssue.slaHours} Hours
                </div>
              </div>
            </div>

            {/* 5. Nearby Reports */}
            <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-bold text-slate-400">5. Nearby Reports</div>
              <div className="flex items-center justify-between text-slate-200">
                <span>Spatial Duplicate Cluster:</span>
                <span className="font-bold text-amber-400">
                  {inspectingIssue.isDuplicate ? 'Merged' : 'Isolated Incident'}
                </span>
              </div>
              <div className="text-[10px] text-slate-400">
                {inspectingIssue.duplicateGroupId
                  ? `Cluster ID: ${inspectingIssue.duplicateGroupId}`
                  : 'No adjacent duplicate reports registered.'}
              </div>
            </div>

            {/* 6. Recurrence */}
            <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-bold text-slate-400">6. Recurrence</div>
              <div className="flex items-center justify-between text-slate-200">
                <span>Chronic Site Index:</span>
                <span className="font-bold text-purple-400">
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
            <div className="p-2.5 bg-[#121824] rounded-lg border border-slate-800 space-y-1">
              <div className="text-[9px] uppercase font-bold text-slate-400">7. Department</div>
              <div className="flex items-center gap-2 text-slate-100 font-bold text-xs">
                <Building className="w-3.5 h-3.5 text-cyan-400" />
                <span>{inspectingIssue.department}</span>
              </div>
              <div className="text-[10px] text-slate-400 font-sans mt-1">
                {inspectingIssue.recommendedAction}
              </div>
            </div>

            {/* Complaint Excerpt */}
            <div className="p-2.5 bg-[#090d14] rounded border border-slate-800/80 font-sans text-xs text-slate-300 leading-relaxed">
              "{inspectingIssue.complaintText}"
            </div>
          </div>

          {/* Footer Action */}
          <div className="p-3 bg-[#0f1422] border-t border-slate-800 shrink-0">
            <button
              onClick={() => onSelectIssue(inspectingIssue)}
              className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1.5 shadow transition cursor-pointer"
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
            className="absolute top-16 bottom-12 right-4 w-96 z-30 bg-[#0c1018]/95 backdrop-blur-md rounded-xl border border-rose-800/80 shadow-2xl flex flex-col overflow-hidden font-mono text-xs"
          >
            {/* Header */}
            <div className="p-3.5 bg-[#140e16] border-b border-rose-950 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2">
                <Radar className="w-4 h-4 text-rose-400 animate-spin" style={{ animationDuration: '6s' }} />
                <div>
                  <span className="font-bold text-rose-300 text-sm">
                    {inspectingHotspot.hotspotId}
                  </span>
                <div className="text-[10px] text-rose-400 font-bold">
                  DBSCAN SPATIAL CLUSTER &bull; {inspectingHotspot.hotspotLevel}
                </div>
              </div>
            </div>

            <button
              onClick={() => setInspectingHotspot(null)}
              className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Content Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {/* 1. Hotspot Boundary */}
            <div className="p-2.5 bg-[#15101a] rounded-lg border border-rose-900/60 space-y-1">
              <div className="text-[9px] uppercase font-bold text-rose-400">1. Hotspot Boundary</div>
              <div className="font-bold text-slate-100 text-xs">
                Radius: {inspectingHotspot.radiusMeters} Meters
              </div>
              <div className="text-[10px] text-slate-400">
                Centroid: {(typeof inspectingHotspot.center?.lat === 'number' ? inspectingHotspot.center.lat : Array.isArray(inspectingHotspot.center) ? Number(inspectingHotspot.center[0]) : 19.076).toFixed(4)}° N, {(typeof inspectingHotspot.center?.lng === 'number' ? inspectingHotspot.center.lng : Array.isArray(inspectingHotspot.center) ? Number(inspectingHotspot.center[1]) : 72.885).toFixed(4)}° E
              </div>
            </div>

            {/* 2. Issue Count */}
            <div className="p-2.5 bg-[#15101a] rounded-lg border border-rose-900/60 flex items-center justify-between">
              <div>
                <div className="text-[9px] uppercase font-bold text-rose-400">2. Incident Count</div>
                <div className="font-bold text-slate-100 text-lg mt-0.5">
                  {inspectingHotspot.issueCount} <span className="text-xs text-slate-400">Reports</span>
                </div>
              </div>
              <div className="text-right">
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-700 text-[10px] font-bold uppercase">
                  Active Density
                </span>
              </div>
            </div>

            {/* 3. Dominant Issue */}
            <div className="p-2.5 bg-[#15101a] rounded-lg border border-rose-900/60 space-y-1">
              <div className="text-[9px] uppercase font-bold text-rose-400">3. Dominant Issue</div>
              <div className="font-bold text-slate-100 text-sm">
                {inspectingHotspot.dominantCategory}
              </div>
              <div className="text-[10px] text-slate-400">
                Accounts for the majority of citizen grievances in this zone.
              </div>
            </div>

            {/* 4. Growth */}
            <div className="p-2.5 bg-[#15101a] rounded-lg border border-rose-900/60 flex items-center justify-between">
              <div>
                <div className="text-[9px] uppercase font-bold text-rose-400">4. Period Growth Rate</div>
                <div className="font-bold text-rose-300 text-lg mt-0.5">
                  {inspectingHotspot.growthRate > 0 ? '+' : ''}{inspectingHotspot.growthRate}%
                </div>
              </div>
              <TrendingUp className="w-5 h-5 text-rose-400" />
            </div>

            {/* 5. Priority */}
            <div className="p-2.5 bg-[#15101a] rounded-lg border border-rose-900/60 space-y-1">
              <div className="text-[9px] uppercase font-bold text-rose-400">5. Average Cluster Priority</div>
              <div className="font-bold text-cyan-300 text-lg">
                {inspectingHotspot.averagePriority.toFixed(1)} / 100
              </div>
              <div className="text-[10px] text-slate-400">
                High civic urgency requires ward officer taskforce mobilization.
              </div>
            </div>
          </div>

          {/* Action */}
          <div className="p-3 bg-[#140e16] border-t border-rose-950 shrink-0">
            <button
              onClick={() => {
                setSelectedCategory(inspectingHotspot.dominantCategory)
                setInspectingHotspot(null)
              }}
              className="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white rounded font-bold text-xs flex items-center justify-center gap-1.5 shadow transition"
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
      <div className="absolute bottom-3 left-3 z-20 flex items-center gap-3 bg-[#0b0f19]/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800 text-[10px] text-slate-400 shadow-xl">
        <span className="font-bold text-slate-300 uppercase">LEGEND:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping inline-block" />
          <span className="text-rose-300 font-bold">Critical (≥80)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-orange-500 inline-block" />
          <span>High (≥65)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-yellow-500 inline-block" />
          <span>Medium (≥40)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
          <span>Low (&lt;40)</span>
        </div>
        <div className="flex items-center gap-1.5 border-l border-slate-800 pl-2">
          <span className="w-2.5 h-2.5 rounded-full border border-dashed border-rose-500 inline-block" />
          <span className="text-rose-400">DBSCAN Hotspot Boundary</span>
        </div>
      </div>
    </div>
  )
}

export default MapView
