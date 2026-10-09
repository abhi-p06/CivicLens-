import React, { useState, useEffect } from 'react'
import {
  Search,
  PlusCircle,
  RotateCcw,
  Clock,
  Command,
  Building2,
  Sparkles,
} from 'lucide-react'

interface TopBarProps {
  activeView: string
  onOpenCommandPalette: () => void
  onOpenNewComplaint: () => void
  onResetDemo: () => void
  onStartDemo?: () => void
  isDemoMode?: boolean
  selectedWard: string
  onSelectWard: (ward: string) => void
  totalIssuesCount: number
}

export const TopBar: React.FC<TopBarProps> = ({
  activeView,
  onOpenCommandPalette,
  onOpenNewComplaint,
  onResetDemo,
  onStartDemo,
  isDemoMode = false,
  selectedWard,
  onSelectWard,
  totalIssuesCount,
}) => {
  const [currentTime, setCurrentTime] = useState('')

  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      const timeStr = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
      const dateStr = now.toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
      })
      setCurrentTime(`${dateStr} ${timeStr} IST`)
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const viewTitles: Record<string, string> = {
    overview: 'Executive Overview',
    live: 'Live Incident Radar',
    analyze: 'Analyze Issue & Cross-Validation',
    explorer: 'Complaint Explorer',
    map: 'Tactical GIS Map',
    hotspots: 'Spatiotemporal Hotspots',
    recurring: 'Recurring Defects Monitor',
    unreported: 'Autonomous Patrol Detections',
    resolution: 'Resolution Verification Center',
    analytics: 'Model Benchmarks & Metrics',
    intelligence: 'Issue Intelligence Dossier',
  }

  const wards = [
    'ALL WARDS (MUMBAI REGION)',
    'N-Ward (Vidyavihar / Ghatkopar)',
    'L-Ward (Kurla)',
    'G/North (Dharavi / Dadar)',
    'K/West (Andheri West)',
  ]

  return (
    <header className="h-14 bg-[#0a0d14] border-b border-[#1a2130] px-4 sm:px-6 flex items-center justify-between z-20 shrink-0 font-sans select-none gap-4">
      {/* 1. Left: View Title & Record Count */}
      <div className="flex items-center gap-3 min-w-0 shrink">
        <div className="flex items-center gap-2 text-sm text-cyan-400 font-semibold truncate">
          <Sparkles className="w-4 h-4 text-cyan-400 shrink-0" />
          <span className="truncate text-slate-100 font-bold">
            {viewTitles[activeView] || 'Civic Intelligence'}
          </span>
        </div>

        <div className="hidden lg:flex items-center gap-1.5 text-xs text-slate-400 font-mono shrink-0">
          <span className="text-slate-600">&bull;</span>
          <span className="text-slate-300 font-medium">{totalIssuesCount} Active Records</span>
        </div>
      </div>

      {/* 2. Center: Global Search & Command Palette trigger */}
      <div className="hidden md:flex items-center justify-center flex-1 max-w-xs lg:max-w-sm mx-2">
        <button
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between px-3 py-1.5 bg-[#101420] hover:bg-[#131926] border border-slate-800 hover:border-slate-700 text-slate-400 rounded-lg text-xs transition group cursor-pointer"
        >
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 transition-colors shrink-0" />
            <span className="text-slate-400 group-hover:text-slate-200 truncate">
              Search issues, w-wards, codes...
            </span>
          </div>
          <div className="flex items-center gap-0.5 px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-400 font-mono shrink-0 ml-2">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* 3. Right: Filters & Action Controls */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Ward Filter */}
        <div className="hidden xl:flex items-center gap-1.5 bg-[#101420] border border-slate-800 rounded-lg px-2.5 py-1 text-xs">
          <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <select
            value={selectedWard}
            onChange={(e) => onSelectWard(e.target.value)}
            className="bg-transparent text-slate-300 text-xs outline-none cursor-pointer"
          >
            {wards.map((w) => (
              <option key={w} value={w} className="bg-[#0e131d] text-slate-200">
                {w}
              </option>
            ))}
          </select>
        </div>

        {/* Live Clock */}
        <div className="hidden 2xl:flex items-center gap-1.5 px-2.5 py-1 bg-[#0f1420] border border-slate-800/80 rounded-lg text-xs font-mono text-slate-400">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>{currentTime}</span>
        </div>

        {/* Dedicated Demo Mode Trigger */}
        {onStartDemo && (
          <button
            onClick={onStartDemo}
            title="Launch Guided Presentation Demo (Alt+D)"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold tracking-wider transition active:scale-95 cursor-pointer ${
              isDemoMode
                ? 'bg-cyan-500 text-black shadow-lg shadow-cyan-400/40'
                : 'bg-gradient-to-r from-cyan-950 to-blue-950 hover:from-cyan-900 hover:to-blue-900 border border-cyan-700/80 text-cyan-300 shadow-md shadow-cyan-950/40'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isDemoMode ? 'bg-black animate-ping' : 'bg-cyan-400 animate-pulse'
              }`}
            />
            <span className="font-mono">DEMO MODE</span>
          </button>
        )}

        {/* Reset Demo button */}
        <button
          onClick={onResetDemo}
          title="Reset database to seed baseline (Alt+R)"
          className="p-1.5 bg-[#101420] hover:bg-[#151c2a] border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Primary Action: Ingest Complaint */}
        <button
          onClick={onOpenNewComplaint}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold shadow-lg shadow-cyan-950/40 transition active:scale-95 cursor-pointer"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>New Complaint</span>
        </button>
      </div>
    </header>
  )
}

export default TopBar
