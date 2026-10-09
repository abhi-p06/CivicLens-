import React, { useState } from 'react'
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
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { CivicMap } from '../map/CivicMap'
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
  const [showHotspots, setShowHotspots] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL')
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL')
  const [inspectingIssue, setInspectingIssue] = useState<Issue | null>(null)

  const categories = [
    'ALL',
    'Roads & Footpaths',
    'Sanitation & Garbage',
    'Water Supply & Drainage',
    'Street Lighting',
    'Storm Water Drains',
    'Traffic & Safety',
  ]

  const filteredIssues = issues.filter((i) => {
    const matchCat = selectedCategory === 'ALL' || i.category === selectedCategory
    const matchPri = selectedPriority === 'ALL' || i.priorityLevel === selectedPriority
    const matchStat = selectedStatus === 'ALL' || i.status === selectedStatus
    return matchCat && matchPri && matchStat
  })

  const handleMarkerClick = (issue: Issue) => {
    setInspectingIssue(issue)
  }

  return (
    <div className="relative h-full w-full flex flex-col font-mono text-xs overflow-hidden">
      {/* Floating HUD Filter Bar */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 bg-[#0e131d]/95 backdrop-blur-md p-3 rounded-xl border border-slate-700/80 shadow-2xl">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-2 text-slate-200 font-bold text-[11px]">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span>GIS WORKSPACE</span>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-1 bg-[#121824] border border-slate-800 rounded px-2 py-1">
            <span className="text-[10px] text-slate-400">CAT:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-slate-200 text-xs outline-none cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c} value={c} className="bg-[#0e131d]">
                  {c}
                </option>
              ))}
            </select>
          </div>

          {/* Priority Toggles */}
          <div className="flex items-center gap-1">
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setSelectedPriority(lvl)}
                className={cn(
                  'px-2 py-1 rounded text-[10px] font-bold border transition',
                  selectedPriority === lvl
                    ? 'bg-cyan-950 border-cyan-500 text-cyan-300'
                    : 'bg-[#121824] border-slate-800 text-slate-400 hover:text-slate-200'
                )}
              >
                {lvl}
              </button>
            ))}
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-1 bg-[#121824] border border-slate-800 rounded px-2 py-1">
            <span className="text-[10px] text-slate-400">STATUS:</span>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-transparent text-slate-200 text-xs outline-none cursor-pointer"
            >
              {['ALL', 'OPEN', 'ANALYZED', 'PRIORITIZED', 'ASSIGNED', 'ACTION IN PROGRESS', 'VERIFICATION', 'RESOLVED'].map((s) => (
                <option key={s} value={s} className="bg-[#0e131d]">
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Hotspots Layer Toggle & Count */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowHotspots(!showHotspots)}
            className={cn(
              'flex items-center gap-1.5 px-3 py-1 rounded text-[11px] font-bold border transition',
              showHotspots
                ? 'bg-rose-950/80 border-rose-700 text-rose-300'
                : 'bg-slate-900 border-slate-800 text-slate-500'
            )}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Hotspot Radii ({hotspots.length})</span>
          </button>

          <span className="text-[11px] text-slate-400 font-mono px-2 py-1 bg-slate-900/80 rounded border border-slate-800">
            {filteredIssues.length} Pins Visible
          </span>
        </div>
      </div>

      {/* Primary Workspace Map */}
      <div className="flex-1 w-full h-full">
        <CivicMap
          issues={filteredIssues}
          hotspots={hotspots}
          showHotspotCircles={showHotspots}
          onSelectIssue={handleMarkerClick}
          selectedIssue={inspectingIssue}
          className="h-full w-full"
        />
      </div>

      {/* Detail Slide-Over Card upon clicking marker */}
      {inspectingIssue && (
        <div className="absolute bottom-5 left-5 right-5 max-w-xl mx-auto z-20 bg-[#0e131d]/95 backdrop-blur-md p-4 rounded-xl border border-cyan-800/80 shadow-2xl animate-in slide-in-from-bottom duration-200">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1 flex-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-cyan-400 text-sm">
                  {inspectingIssue.issueId}
                </span>
                <StatusBadge status={inspectingIssue.status} />
                <ConsistencyBadge level={inspectingIssue.consistencyFlag || 'CONSISTENT'} />
              </div>

              <div className="font-bold text-slate-100 text-xs font-sans mt-0.5">
                {inspectingIssue.category} &bull; {inspectingIssue.location} ({inspectingIssue.ward})
              </div>

              <p className="text-slate-300 text-xs font-sans line-clamp-2 leading-relaxed">
                {inspectingIssue.complaintText}
              </p>
            </div>

            <button
              onClick={() => setInspectingIssue(null)}
              className="text-slate-400 hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-800">
            <PriorityGauge
              score={inspectingIssue.priorityScore}
              level={inspectingIssue.priorityLevel}
              compact
            />

            <button
              onClick={() => onSelectIssue(inspectingIssue)}
              className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-bold shadow transition"
            >
              Open Intelligence Dossier &rarr;
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
