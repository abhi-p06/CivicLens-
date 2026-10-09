import React, { useState } from 'react'
import {
  Flame,
  TrendingUp,
  MapPin,
  AlertCircle,
  Layers,
  ArrowUpDown,
  BarChart2,
} from 'lucide-react'
import { HotspotInfo, Issue } from '../../types'
import { CivicMap } from '../map/CivicMap'
import { cn } from '../../lib/utils'

interface HotspotsViewProps {
  hotspots: HotspotInfo[]
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const HotspotsView: React.FC<HotspotsViewProps> = ({ hotspots, issues, onSelectIssue }) => {
  const [selectedHotspot, setSelectedHotspot] = useState<HotspotInfo | null>(
    hotspots[0] || null
  )

  // Rank hotspots by issueCount and averagePriority
  const rankedHotspots = [...hotspots].sort((a, b) => {
    return b.issueCount * b.averagePriority - a.issueCount * a.averagePriority
  })

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-rose-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500 animate-pulse" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
              FEATURE 16 // SPATIOTEMPORAL HOTSPOT DETECTION & CLUSTERS
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-0.5">
            DBSCAN spatial density analysis identifying micro-geographic corridors with anomalous defect concentration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 bg-rose-950/80 border border-rose-800 text-rose-300 rounded font-bold">
            {hotspots.length} ACTIVE CLUSTERS DETECTED
          </span>
        </div>
      </div>

      {/* Main Grid: Ranking & Trends vs Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1 min-h-[500px]">
        {/* Left: Top Hotspots Ranking & Trends */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-xl space-y-3">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>Hotspot Risk Ranking & Period Growth</span>
            <span className="text-slate-500 text-[10px]">Haversine DBSCAN (R=500m)</span>
          </div>

          <div className="space-y-3 overflow-y-auto flex-1 pr-1 max-h-[560px]">
            {rankedHotspots.map((h, index) => {
              const isSelected = selectedHotspot?.hotspotId === h.hotspotId
              const densityVal = (h as any).densityPerKm2 || (h.issueCount / (Math.PI * 0.25)).toFixed(1)

              return (
                <div
                  key={h.hotspotId}
                  onClick={() => setSelectedHotspot(h)}
                  className={cn(
                    'p-4 rounded-xl border transition cursor-pointer shadow space-y-2.5',
                    isSelected
                      ? 'bg-[#151c2d] border-rose-600 shadow-rose-950/40'
                      : 'bg-[#111724] border-slate-800 hover:border-slate-700'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-500 font-mono">
                        #{index + 1}
                      </span>
                      <span className="font-bold text-rose-400 text-xs">{h.hotspotId}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-950 border border-rose-800 text-rose-300">
                        {h.hotspotLevel}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-rose-300 font-bold">
                      <TrendingUp className="w-3.5 h-3.5" />
                      <span>{h.growthRate > 0 ? `+${h.growthRate}%` : `${h.growthRate}%`} Growth</span>
                    </div>
                  </div>

                  {/* Density, Dominant Category, Avg Priority */}
                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                      <div className="text-slate-500 text-[10px]">ISSUE DENSITY</div>
                      <div className="text-sm font-bold text-slate-100 mt-0.5">
                        {h.issueCount} Reports ({densityVal}/km²)
                      </div>
                    </div>

                    <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                      <div className="text-slate-500 text-[10px]">DOMINANT CATEGORY</div>
                      <div className="text-xs font-bold text-cyan-400 mt-1 truncate">
                        {h.dominantCategory}
                      </div>
                    </div>

                    <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                      <div className="text-slate-500 text-[10px]">AVG PRIORITY</div>
                      <div className="text-sm font-bold text-amber-400 mt-0.5">
                        {h.averagePriority.toFixed(1)}/100
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-slate-800/80">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      Center: {h.center.lat.toFixed(4)}, {h.center.lng.toFixed(4)} (Radius: {h.radiusMeters}m)
                    </span>
                    <span className="text-cyan-400 font-mono">Click to center map</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: Map with Hotspot Rings */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-3 flex flex-col shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 pb-2 mb-2 border-b border-slate-800 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>DBSCAN Geographic Concentration</span>
            </span>
            <span className="text-rose-400 text-[10px]">CLUSTER OVERLAY</span>
          </div>

          <div className="flex-1 w-full min-h-[420px] rounded-lg overflow-hidden border border-slate-800">
            <CivicMap
              issues={issues}
              hotspots={hotspots}
              showHotspotCircles={true}
              onSelectIssue={onSelectIssue}
              className="h-full w-full"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
