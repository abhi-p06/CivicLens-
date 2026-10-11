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
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-6 font-sans bg-[#F6F7FC]">
      {/* Header */}
      <div className="p-6 bg-white border border-[#E4E7F1] rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-[#EF4444]" />
        
        <div className="space-y-1 pl-2">
          <div className="flex items-center gap-2.5">
            <Flame className="w-6 h-6 text-[#EF4444]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#11162A] tracking-normal">
              Spatiotemporal Hotspot Detection
            </h1>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-rose-50 border border-rose-200 text-[#EF4444]">
              FEATURE 16
            </span>
          </div>
          <p className="text-[#65708B] text-sm max-w-2xl leading-relaxed">
            Haversine DBSCAN spatial clustering identifies micro-geographic corridors with anomalous defect density and rapid growth.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pl-2 md:pl-0">
          <div className="px-4 py-2 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl text-right">
            <div className="text-xs text-[#65708B]">Active Clusters</div>
            <div className="text-base font-bold font-mono text-[#EF4444]">
              {hotspots.length} Detected
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Ranking & Trends vs Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1 min-h-[520px]">
        {/* Left: Top Hotspots Ranking & Trends */}
        <div className="lg:col-span-7 bg-white border border-[#E4E7F1] rounded-2xl p-5 flex flex-col shadow-xs space-y-4">
          <div className="text-xs font-semibold text-[#11162A] border-b border-[#E4E7F1] pb-3 flex items-center justify-between">
            <span>Hotspot Risk Ranking & Temporal Growth</span>
            <span className="text-[#65708B] text-xs font-mono">Haversine DBSCAN (R=150m)</span>
          </div>

          <div className="space-y-3.5 overflow-y-auto flex-1 pr-1 max-h-[580px]">
            {rankedHotspots.map((h, index) => {
              const isSelected = selectedHotspot?.hotspotId === h.hotspotId
              const densityVal = (h as any).densityPerKm2 || (h.issueCount / (Math.PI * 0.25)).toFixed(1)

              return (
                <div
                  key={h.hotspotId}
                  onClick={() => setSelectedHotspot(h)}
                  className={cn(
                    'p-5 rounded-xl border transition cursor-pointer shadow-xs space-y-3',
                    isSelected
                      ? 'bg-rose-50/40 border-[#EF4444]'
                      : 'bg-[#F0F2F9] border-[#E4E7F1] hover:border-slate-300'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-bold text-[#65708B] font-mono">
                        #{index + 1}
                      </span>
                      <span className="font-bold text-[#EF4444] text-sm font-mono">{h.hotspotId}</span>
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-100 border border-rose-200 text-[#EF4444] font-mono">
                        {h.hotspotLevel}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-[#EF4444] font-semibold font-mono">
                      <TrendingUp className="w-4 h-4" />
                      <span>{h.growthRate > 0 ? `+${h.growthRate}%` : `${h.growthRate}%`} Period Growth</span>
                    </div>
                  </div>

                  {/* Density, Dominant Category, Avg Priority */}
                  <div className="grid grid-cols-3 gap-2.5 text-xs">
                    <div className="p-3 bg-white rounded-xl border border-[#E4E7F1]">
                      <div className="text-[#65708B] text-[11px] font-semibold">Incident Density</div>
                      <div className="text-sm font-bold text-[#11162A] mt-1 font-mono">
                        {h.issueCount} Reports ({densityVal}/km²)
                      </div>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-[#E4E7F1]">
                      <div className="text-[#65708B] text-[11px] font-semibold">Dominant Category</div>
                      <div className="text-sm font-bold text-[#6457E8] mt-1 truncate">
                        {h.dominantCategory}
                      </div>
                    </div>

                    <div className="p-3 bg-white rounded-xl border border-[#E4E7F1]">
                      <div className="text-[#65708B] text-[11px] font-semibold">Average Priority</div>
                      <div className="text-sm font-bold text-[#F97316] mt-1 font-mono">
                        {h.averagePriority.toFixed(1)} / 100
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-xs text-[#65708B] pt-2 border-t border-[#E4E7F1]">
                    <span className="flex items-center gap-1.5 font-mono">
                      <MapPin className="w-3.5 h-3.5 text-[#65708B]" />
                      Center: {(typeof h.center?.lat === 'number' ? h.center.lat : Array.isArray(h.center) ? Number(h.center[0]) : 19.076).toFixed(4)}, {(typeof h.center?.lng === 'number' ? h.center.lng : Array.isArray(h.center) ? Number(h.center[1]) : 72.885).toFixed(4)} (Radius: {h.radiusMeters || 300}m)
                    </span>
                    <span className="text-[#6457E8] font-semibold text-xs">Click to center map &rarr;</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right: Map with Hotspot Rings */}
        <div className="lg:col-span-5 bg-white border border-[#E4E7F1] rounded-2xl p-5 flex flex-col shadow-xs">
          <div className="text-xs font-semibold text-[#11162A] pb-3 mb-3 border-b border-[#E4E7F1] flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-[#6457E8]" />
              <span>DBSCAN Boundary & Centroid Visualizer</span>
            </span>
            <span className="text-[#EF4444] text-xs font-mono font-bold">CLUSTER RADAR</span>
          </div>

          <div className="flex-1 w-full min-h-[440px] rounded-xl overflow-hidden border border-[#212348] bg-[#10162A]">
            <CivicMap
              issues={issues}
              hotspots={hotspots}
              showHotspotCircles={true}
              selectedHotspot={selectedHotspot}
              onSelectIssue={onSelectIssue}
              className="h-full w-full"
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default HotspotsView
