import React from 'react'
import { Flame, TrendingUp, MapPin, AlertCircle, Layers } from 'lucide-react'
import { HotspotInfo, Issue } from '../../types'
import { CivicMap } from '../map/CivicMap'
import { cn } from '../../lib/utils'

interface HotspotsViewProps {
  hotspots: HotspotInfo[]
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const HotspotsView: React.FC<HotspotsViewProps> = ({ hotspots, issues, onSelectIssue }) => {
  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-rose-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-rose-500 animate-pulse" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              FEATURE 16: SPATIOTEMPORAL DBSCAN HOTSPOT ENGINE
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Detecting micro-geographic clusters with high issue concentration, dominant defect types, and period-over-period growth rates.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-rose-950/80 border border-rose-800 text-rose-300 rounded font-bold">
            {hotspots.length} ACTIVE CLUSTERS
          </div>
        </div>
      </div>

      {/* Grid: Hotspot Table & Geographic Map */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
        {/* Table List */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3 flex items-center justify-between">
            <span>DBSCAN Spatial Cluster Registry</span>
            <span className="text-slate-500">Haversine Radian Metric &bull; R=500m</span>
          </div>

          <div className="space-y-3 overflow-y-auto flex-1 pr-1">
            {hotspots.map((h) => {
              const isCrit = h.hotspotLevel === 'CRITICAL'
              return (
                <div
                  key={h.hotspotId}
                  className="p-3.5 bg-[#111724] border border-slate-800 rounded-lg space-y-2.5 shadow"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-rose-400 text-xs">{h.hotspotId}</span>
                      <span
                        className={cn(
                          'px-2 py-0.5 rounded text-[10px] font-bold border uppercase',
                          isCrit
                            ? 'bg-rose-950 border-rose-700 text-rose-300'
                            : 'bg-amber-950 border-amber-700 text-amber-300'
                        )}
                      >
                        {h.hotspotLevel} RISK
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs">
                      <TrendingUp className="w-3.5 h-3.5 text-rose-400" />
                      <span className="font-bold text-rose-300">
                        {h.growthRate > 0 ? `+${h.growthRate}%` : `${h.growthRate}%`} Growth
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 text-[11px]">
                    <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                      <div className="text-slate-500 text-[10px]">INCIDENT DENSITY</div>
                      <div className="text-sm font-bold text-slate-200 mt-0.5">
                        {h.issueCount} Reports
                      </div>
                    </div>

                    <div className="p-2 bg-[#0a0d14] rounded border border-slate-800">
                      <div className="text-slate-500 text-[10px]">DOMINANT CATEGORY</div>
                      <div className="text-xs font-bold text-cyan-300 mt-1 truncate">
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

                  <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-2">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-slate-500" />
                      Center: {h.center.lat.toFixed(4)}, {h.center.lng.toFixed(4)} (Radius: {h.radiusMeters}m)
                    </span>
                    <span className="text-slate-500">Period: Current vs Previous</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Map Visualizer */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-3 flex flex-col shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 pb-2 mb-2 border-b border-slate-800 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Hotspot Spatial Bounds</span>
            </span>
            <span className="text-rose-400 text-[10px]">TRANSLUCENT RINGS</span>
          </div>

          <div className="flex-1 w-full min-h-[380px] rounded-lg overflow-hidden border border-slate-800">
            <CivicMap
              issues={issues.filter((i) => i.isHotspot)}
              hotspots={hotspots}
              onSelectIssue={onSelectIssue}
              className="h-full w-full"
            />
          </div>
        </div>
      </div>
    </div>
  )
}
