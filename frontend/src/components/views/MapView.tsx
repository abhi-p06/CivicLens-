import React, { useState } from 'react'
import {
  Layers,
  Flame,
  RotateCcw,
  ShieldAlert,
  MapPin,
  Filter,
} from 'lucide-react'
import { Issue, HotspotInfo, RecurrenceInfo } from '../../types'
import { CivicMap } from '../map/CivicMap'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'

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
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL')
  const [inspectingIssue, setInspectingIssue] = useState<Issue | null>(null)

  const filteredIssues = issues.filter(
    (i) => selectedPriority === 'ALL' || i.priorityLevel === selectedPriority
  )

  const handleMarkerClick = (issue: Issue) => {
    setInspectingIssue(issue)
  }

  return (
    <div className="relative h-full w-full flex flex-col font-mono text-xs overflow-hidden">
      {/* Floating Tactical Map Filter Bar */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap items-center gap-2 bg-[#0e131d]/90 backdrop-blur-md p-2.5 rounded-xl border border-slate-700/80 shadow-2xl">
        <div className="flex items-center gap-1.5 px-2 text-slate-300 font-bold text-[11px]">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>GIS LAYERS:</span>
        </div>

        <button
          onClick={() => setShowHotspots(!showHotspots)}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-bold border transition ${
            showHotspots
              ? 'bg-rose-950/80 border-rose-700 text-rose-300'
              : 'bg-slate-900 border-slate-800 text-slate-500'
          }`}
        >
          <Flame className="w-3 h-3" />
          <span>DBSCAN Hotspots ({hotspots.length})</span>
        </button>

        <div className="h-4 w-px bg-slate-700 mx-1" />

        <div className="flex items-center gap-1">
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setSelectedPriority(lvl)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold border transition ${
                selectedPriority === lvl
                  ? 'bg-cyan-950 border-cyan-600 text-cyan-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Full-bleed Map */}
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

      {/* Floating Bottom Drawer on Inspecting Issue */}
      {inspectingIssue && (
        <div className="absolute bottom-4 left-4 right-4 max-w-2xl mx-auto z-20 bg-[#0e131d]/95 backdrop-blur-md p-4 rounded-xl border border-cyan-800/80 shadow-2xl animate-in slide-in-from-bottom duration-200">
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold text-cyan-400 text-sm">
                  {inspectingIssue.issueId}
                </span>
                <StatusBadge status={inspectingIssue.status} />
                <ConsistencyBadge level={inspectingIssue.consistencyFlag || 'CONSISTENT'} />
              </div>
              <div className="font-bold text-slate-200 text-xs font-sans">
                {inspectingIssue.category} &bull; {inspectingIssue.location}
              </div>
              <p className="text-slate-300 text-xs font-sans line-clamp-2 leading-relaxed">
                {inspectingIssue.complaintText}
              </p>
            </div>

            <div className="flex flex-col items-end gap-2 shrink-0">
              <PriorityGauge
                score={inspectingIssue.priorityScore}
                level={inspectingIssue.priorityLevel}
                compact
              />
              <button
                onClick={() => onSelectIssue(inspectingIssue)}
                className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[11px] font-bold shadow transition"
              >
                Inspect Full Audit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
