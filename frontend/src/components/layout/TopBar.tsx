import React, { useState, useEffect } from 'react'
import {
  Search,
  PlusCircle,
  RotateCcw,
  Clock,
  Command,
  Building2,
  Sparkles,
  Activity,
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
      })
      setCurrentTime(`${timeStr} IST`)
    }
    updateTime()
    const timer = setInterval(updateTime, 1000)
    return () => clearInterval(timer)
  }, [])

  const viewTitles: Record<string, string> = {
    overview: 'Command Center Overview',
    live: 'Live Incident Radar',
    analyze: 'Analyze Complaint Pipeline',
    explorer: 'Complaint Catalog',
    map: 'Tactical GIS Spatial Map',
    hotspots: 'Spatiotemporal Hotspot Detection',
    recurring: 'Recurring Infrastructure Defects',
    unreported: 'Autonomous Patrol Detections',
    resolution: 'Work-Order Resolution Center',
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
    <header className="h-16 bg-[#090c13] border-b border-slate-800/90 px-6 flex items-center justify-between z-20 shrink-0 font-sans select-none gap-5">
      {/* 1. Left: View Title & Record Counter */}
      <div className="flex items-center gap-3.5 min-w-0 shrink">
        <div className="flex items-center gap-2.5 truncate">
          <Sparkles className="w-5 h-5 text-cyan-400 shrink-0" />
          <h1 className="text-base sm:text-lg font-bold text-slate-100 tracking-tight truncate">
            {viewTitles[activeView] || 'Civic Intelligence'}
          </h1>
        </div>

        <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400 font-mono shrink-0">
          <span className="text-slate-600">&bull;</span>
          <span className="px-2 py-0.5 rounded bg-[#111724] border border-slate-800 text-slate-300 font-medium">
            {totalIssuesCount} Active Issues
          </span>
        </div>
      </div>

      {/* 2. Center: Global Search & Command Palette trigger */}
      <div className="hidden md:flex items-center justify-center flex-1 max-w-xs lg:max-w-md mx-2">
        <button
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between px-3.5 py-2 bg-[#101622] hover:bg-[#141b2a] border border-slate-800 hover:border-slate-700 text-slate-400 rounded-lg text-sm transition group cursor-pointer shadow-inner"
        >
          <div className="flex items-center gap-2.5 truncate">
            <Search className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors shrink-0" />
            <span className="text-slate-400 group-hover:text-slate-200 text-xs sm:text-sm truncate">
              Search issues, categories, wards...
            </span>
          </div>
          <div className="flex items-center gap-1 px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-xs text-slate-400 font-mono shrink-0 ml-2">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* 3. Right: Filters & Action Controls */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Ward Filter */}
        <div className="hidden xl:flex items-center gap-2 bg-[#101622] border border-slate-800 rounded-lg px-3 py-1.5 text-xs">
          <Building2 className="w-4 h-4 text-slate-400 shrink-0" />
          <select
            value={selectedWard}
            onChange={(e) => onSelectWard(e.target.value)}
            className="bg-transparent text-slate-200 text-xs font-medium outline-none cursor-pointer"
          >
            {wards.map((w) => (
              <option key={w} value={w} className="bg-[#0e131d] text-slate-200">
                {w}
              </option>
            ))}
          </select>
        </div>

        {/* Guided Demo Mode Trigger */}
        {onStartDemo && (
          <button
            onClick={onStartDemo}
            title="Launch Guided Presentation Demo (Alt+D)"
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono tracking-wider transition active:scale-95 cursor-pointer ${
              isDemoMode
                ? 'bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-400/40'
                : 'bg-gradient-to-r from-cyan-950 to-blue-950 hover:from-cyan-900 hover:to-blue-900 border border-cyan-700/80 text-cyan-300 shadow-md shadow-cyan-950/40'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isDemoMode ? 'bg-black animate-ping' : 'bg-cyan-400 animate-pulse'
              }`}
            />
            <span>DEMO MODE</span>
          </button>
        )}

        {/* Reset Demo State Button */}
        <button
          onClick={onResetDemo}
          title="Reset database to seed baseline (Alt+R)"
          className="p-2 bg-[#101622] hover:bg-[#151c2a] border border-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition cursor-pointer"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Primary CTA: New Complaint */}
        <button
          onClick={onOpenNewComplaint}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-cyan-950/50 transition active:scale-95 cursor-pointer"
        >
          <PlusCircle className="w-4 h-4" />
          <span>New Complaint</span>
        </button>
      </div>
    </header>
  )
}

export default TopBar
