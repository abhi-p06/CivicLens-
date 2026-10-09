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
      // Display IST/Local operational timestamp
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
    overview: 'EXECUTIVE OVERVIEW // SITUATIONAL INTELLIGENCE',
    live: 'LIVE INCIDENT RADAR // MULTIMODAL INGESTION',
    analyze: 'COMPLAINT INGESTION & CROSS-VALIDATION LAB',
    explorer: 'MUNICIPAL INCIDENT CATALOG // QUERY ENGINE',
    map: 'TACTICAL GIS SPATIAL INTELLIGENCE MAP',
    hotspots: 'SPATIOTEMPORAL DBSCAN HOTSPOT CLUSTERS',
    recurring: 'CHRONIC DEFECT RECURRENCE MONITOR',
    unreported: 'AUTONOMOUS PATROL SURVEY DETECTIONS',
    resolution: 'WORK-ORDER VERIFICATION & LIFECYCLE',
    analytics: 'EMPIRICAL MODEL BENCHMARKS & EVALUATION',
  }

  const wards = [
    'ALL WARDS (MUMBAI REGION)',
    'N-Ward (Vidyavihar / Ghatkopar)',
    'L-Ward (Kurla)',
    'G/North (Dharavi / Dadar)',
    'K/West (Andheri West)',
  ]

  return (
    <header className="h-14 bg-[#0a0d14] border-b border-[#1a2130] px-4 flex items-center justify-between z-20 shrink-0 font-sans select-none">
      {/* View Title & Breadcrumb */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs font-mono text-cyan-400">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="font-bold tracking-wider">
            {viewTitles[activeView] || 'CIVIC INTELLIGENCE'}
          </span>
        </div>

        <div className="hidden lg:flex items-center gap-1 text-[11px] text-slate-400 font-mono">
          <span className="text-slate-400">|</span>
          <span className="text-slate-300 font-semibold">{totalIssuesCount} Active Records</span>
        </div>
      </div>

      {/* Center: Global Search & Command Palette trigger */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <button
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between px-3 py-1.5 bg-[#101420] hover:bg-[#131926] border border-slate-800 hover:border-slate-700 text-slate-400 rounded-lg text-xs font-mono transition group"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-400 transition-colors" />
            <span className="text-slate-400 group-hover:text-slate-300">
              Search commands, categories, coordinates...
            </span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-400">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* Right controls: Ward filter, Time, Actions */}
      <div className="flex items-center gap-2.5">
        {/* Ward Filter */}
        <div className="hidden xl:flex items-center gap-1.5 bg-[#101420] border border-slate-800 rounded px-2 py-1 text-xs font-mono">
          <Building2 className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedWard}
            onChange={(e) => onSelectWard(e.target.value)}
            className="bg-transparent text-slate-300 text-[11px] outline-none cursor-pointer"
          >
            {wards.map((w) => (
              <option key={w} value={w} className="bg-[#0e131d] text-slate-200">
                {w}
              </option>
            ))}
          </select>
        </div>

        {/* Live Clock */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#0f1420] border border-slate-800/80 rounded text-[11px] font-mono text-slate-300">
          <Clock className="w-3 h-3 text-cyan-400" />
          <span>{currentTime || 'SYNCHRONIZING...'}</span>
        </div>

        {/* Dedicated Demo Mode Trigger */}
        {onStartDemo && (
          <button
            onClick={onStartDemo}
            title="Launch Guided Presentation Demo (Alt+D)"
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold tracking-wider transition active:scale-95 cursor-pointer ${
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
            <span>DEMO MODE</span>
          </button>
        )}

        {/* Reset Demo button */}
        <button
          onClick={onResetDemo}
          title="Reset sample database to default seed state (Alt+R)"
          className="p-1.5 bg-[#101420] hover:bg-[#151c2a] border border-slate-800 text-slate-400 hover:text-slate-200 rounded transition cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>

        {/* Primary Action: Ingest Complaint */}
        <button
          onClick={onOpenNewComplaint}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-medium font-mono tracking-wide shadow-lg shadow-cyan-950/40 transition active:scale-95"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>INTAKE COMPLAINT</span>
        </button>
      </div>
    </header>
  )
}
