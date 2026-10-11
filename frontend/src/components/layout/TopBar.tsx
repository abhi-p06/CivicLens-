import React, { useState, useEffect } from 'react'
import {
  Search,
  PlusCircle,
  RotateCcw,
  Command,
  Building2,
  Sparkles,
  Zap,
  ChevronRight,
} from 'lucide-react'
import { useCivicMotion } from '../../lib/motionContext'
import { cn } from '../../lib/utils'

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
  const { motionMode, toggleMotionMode, isReduced } = useCivicMotion()
  const [isScrolled, setIsScrolled] = useState(false)

  useEffect(() => {
    const handleScroll = (e: Event) => {
      const target = e.target as HTMLElement
      if (target && typeof target.scrollTop === 'number') {
        setIsScrolled(target.scrollTop > 8)
      }
    }
    window.addEventListener('scroll', handleScroll, { capture: true, passive: true })
    return () => window.removeEventListener('scroll', handleScroll, { capture: true })
  }, [])

  const viewCategories: Record<string, string> = {
    overview: 'Operations',
    live: 'Operations',
    analyze: 'Operations',
    explorer: 'Operations',
    map: 'Operations',
    hotspots: 'Spatial Intelligence',
    recurring: 'Spatial Intelligence',
    unreported: 'Spatial Intelligence',
    resolution: 'Verification',
    analytics: 'Verification',
    intelligence: 'Operations',
  }

  const viewTitles: Record<string, string> = {
    overview: 'Command Center',
    live: 'Live Radar',
    analyze: 'Analyze Complaint',
    explorer: 'Issue Catalog',
    map: 'Tactical GIS Map',
    hotspots: 'Spatiotemporal Hotspots',
    recurring: 'Recurring Infrastructure',
    unreported: 'Patrol Detections',
    resolution: 'Resolution Center',
    analytics: 'Model Benchmarks',
    intelligence: 'Issue Dossier',
  }

  const wards = [
    'ALL WARDS (MUMBAI REGION)',
    'N-Ward (Vidyavihar / Ghatkopar)',
    'L-Ward (Kurla)',
    'G/North (Dharavi / Dadar)',
    'K/West (Andheri West)',
  ]

  const currentCategory = viewCategories[activeView] || 'Operations'
  const currentTitle = viewTitles[activeView] || 'Command Center'

  return (
    <header
      className={cn(
        'sticky top-0 h-14 px-6 sm:px-8 flex items-center justify-between z-30 shrink-0 font-sans select-none gap-4 transition-[background-color,box-shadow,border-color] duration-200 border-b border-[#E4E7F1]',
        isScrolled
          ? 'bg-white/95 backdrop-blur-md shadow-sm'
          : 'bg-white shadow-[0_1px_2px_rgba(17,22,42,0.02)]'
      )}
    >
      {/* 1. Left: Breadcrumb Context & Incident Count */}
      <div className="flex items-center gap-2.5 shrink-0">
        <span className="text-xs font-medium text-[#65708B]">
          {currentCategory}
        </span>
        <ChevronRight className="w-3.5 h-3.5 text-[#65708B]/60" />
        <span className="text-sm font-semibold text-[#11162A] tracking-tight">
          {currentTitle}
        </span>

        <span className="hidden sm:inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#F0F2F9] border border-[#E4E7F1] text-[#65708B] ml-1">
          {totalIssuesCount} Active Incidents
        </span>
      </div>

      {/* 2. Center: Linear-style Search / Command Palette Trigger */}
      <div className="hidden md:flex items-center justify-center flex-1 max-w-sm lg:max-w-md mx-2">
        <button
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between px-3.5 py-1.5 bg-[#F0F2F9] hover:bg-[#E4E7F1]/70 border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] rounded-xl text-xs sm:text-sm transition cursor-pointer shadow-xs"
        >
          <div className="flex items-center gap-2.5 truncate">
            <Search className="w-4 h-4 text-[#65708B] shrink-0" />
            <span className="text-[#65708B] text-xs sm:text-sm truncate">
              Search issues, wards, actions...
            </span>
          </div>
          <div className="flex items-center gap-0.5 px-1.5 py-0.5 bg-white border border-[#E4E7F1] rounded text-[11px] text-[#65708B] font-mono shrink-0 ml-2">
            <Command className="w-3 h-3" />
            <span>K</span>
          </div>
        </button>
      </div>

      {/* 3. Right: Clean Controls */}
      <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
        {/* Ward Filter */}
        <div className="hidden lg:flex items-center gap-2 bg-white border border-[#E4E7F1] hover:border-slate-300 rounded-xl px-3 py-1.5 text-xs text-[#11162A] transition shadow-xs">
          <Building2 className="w-3.5 h-3.5 text-[#65708B] shrink-0" />
          <select
            value={selectedWard}
            onChange={(e) => onSelectWard(e.target.value)}
            className="bg-transparent text-[#11162A] text-xs font-medium outline-none cursor-pointer"
          >
            {wards.map((w) => (
              <option key={w} value={w} className="bg-white text-[#11162A]">
                {w}
              </option>
            ))}
          </select>
        </div>

        {/* Motion Preference Toggle */}
        <button
          onClick={toggleMotionMode}
          title={`Animation Mode: ${isReduced ? 'REDUCED' : 'FULL'} (Click to toggle)`}
          className={cn(
            'hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer border shadow-xs',
            !isReduced
              ? 'bg-[#6457E8]/10 border-[#6457E8]/30 text-[#6457E8] hover:bg-[#6457E8]/15'
              : 'bg-slate-100 border-slate-300 text-slate-700 hover:bg-slate-200/70'
          )}
        >
          <Zap className={cn('w-3.5 h-3.5', !isReduced ? 'text-[#6457E8]' : 'text-slate-500')} />
          <span className="text-[11px] font-mono font-semibold tracking-tight">
            {isReduced ? 'MOTION: REDUCED' : 'MOTION: FULL'}
          </span>
        </button>

        {/* Demo Mode Button */}
        {onStartDemo && (
          <button
            onClick={onStartDemo}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer border shadow-xs ${
              isDemoMode
                ? 'bg-amber-50 border-amber-300 text-amber-800'
                : 'bg-white hover:bg-slate-50 border-[#E4E7F1] text-[#11162A]'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isDemoMode ? 'bg-[#F97316] animate-pulse' : 'bg-slate-400'
              }`}
            />
            <span>Demo</span>
          </button>
        )}

        {/* Reset Demo Button */}
        <button
          onClick={onResetDemo}
          title="Reset database (Alt+R)"
          className="p-1.5 bg-white hover:bg-slate-50 border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] rounded-xl transition cursor-pointer shadow-xs"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        {/* Primary Action: New Complaint (Violet with restrained subtle hover) */}
        <button
          onClick={onOpenNewComplaint}
          className="flex items-center gap-2 px-3.5 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs sm:text-sm font-semibold transition active:scale-95 cursor-pointer shadow-sm"
        >
          <PlusCircle className="w-4 h-4" />
          <span className="hidden sm:inline">New Complaint</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>
    </header>
  )
}

export default TopBar
