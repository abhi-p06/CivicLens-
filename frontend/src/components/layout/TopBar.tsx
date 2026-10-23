import React, { useState, useEffect, useRef } from 'react'
import {
  Search,
  PlusCircle,
  RotateCcw,
  Command,
  Building2,
  Zap,
  ChevronRight,
  ChevronDown,
  LogOut,
  Shield,
  User as UserIcon
} from 'lucide-react'
import { useCivicMotion } from '../../lib/motionContext'
import { useAuth } from '../../context/AuthContext'
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
  const { toggleMotionMode, isReduced } = useCivicMotion()
  const { user, logout } = useAuth()
  const [isScrolled, setIsScrolled] = useState(false)
  const [isAccountOpen, setIsAccountOpen] = useState(() => typeof window !== "undefined" && new URLSearchParams(window.location.search).get("open_menu") === "1")
  const accountMenuRef = useRef<HTMLDivElement>(null)

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

  // Close dropdown on outside click or Escape key
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(event.target as Node)) {
        setIsAccountOpen(false)
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsAccountOpen(false)
      }
    }
    if (isAccountOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      document.addEventListener('keydown', handleKeyDown)
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isAccountOpen])

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
    citizen_portal: 'Citizen Grievances',
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
    citizen_portal: 'Citizen Portal',
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
        'sticky top-0 h-14 px-3 sm:px-4 lg:px-5 flex items-center justify-between z-30 shrink-0 font-sans select-none gap-2 sm:gap-3 transition-[background-color,box-shadow,border-color] duration-200 border-b border-[#E4E7F1] w-full max-w-full',
        isScrolled
          ? 'bg-white/95 backdrop-blur-md shadow-sm'
          : 'bg-white shadow-[0_1px_2px_rgba(17,22,42,0.02)]'
      )}
    >
      {/* 1. Left: Breadcrumb Context & Incident Count */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0 min-w-0">
        <span className="text-xs font-medium text-[#65708B] hidden md:inline truncate max-w-[110px]">
          {currentCategory}
        </span>
        <ChevronRight className="w-3.5 h-3.5 text-[#65708B]/60 hidden md:inline shrink-0" />
        <span className="text-xs sm:text-sm font-semibold text-[#11162A] tracking-tight truncate max-w-[140px] sm:max-w-[180px] lg:max-w-[220px]">
          {currentTitle}
        </span>

        {user?.role !== 'citizen' && (
          <span className="hidden xl:inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-[#F0F2F9] border border-[#E4E7F1] text-[#65708B] shrink-0 ml-1">
            {totalIssuesCount} Active
          </span>
        )}
      </div>

      {/* 2. Center: Linear-style Search / Command Palette Trigger */}
      {user?.role !== 'citizen' && (
        <div className="hidden lg:flex items-center justify-center flex-1 min-w-0 max-w-xs xl:max-w-sm mx-1.5">
          <button
            type="button"
            onClick={onOpenCommandPalette}
            className="w-full flex items-center justify-between px-3 py-1.5 bg-[#F0F2F9] hover:bg-[#E4E7F1]/70 border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] rounded-xl text-xs transition cursor-pointer shadow-xs truncate"
          >
            <div className="flex items-center gap-2 truncate">
              <Search className="w-3.5 h-3.5 text-[#65708B] shrink-0" />
              <span className="text-[#65708B] text-xs truncate">
                Search issues, wards...
              </span>
            </div>
            <div className="hidden xl:flex items-center gap-0.5 px-1.5 py-0.5 bg-white border border-[#E4E7F1] rounded text-[10px] text-[#65708B] font-mono shrink-0 ml-1.5">
              <Command className="w-3 h-3" />
              <span>K</span>
            </div>
          </button>
        </div>
      )}

      {/* 3. Right: Clean Controls & Account Dropdown */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0 ml-auto">
        {/* Compact Search Trigger on small screens */}
        {user?.role !== 'citizen' && (
          <button
            type="button"
            onClick={onOpenCommandPalette}
            title="Search / Command Palette (Cmd+K)"
            className="flex lg:hidden p-1.5 bg-white hover:bg-slate-50 border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] rounded-xl transition cursor-pointer shadow-xs"
          >
            <Search className="w-4 h-4" />
          </button>
        )}

        {/* Ward Filter (2XL screens only to guarantee space on standard desktop viewports) */}
        {user?.role !== 'citizen' && (
          <div className="hidden 2xl:flex items-center gap-1.5 bg-white border border-[#E4E7F1] hover:border-slate-300 rounded-xl px-2.5 py-1.5 text-xs text-[#11162A] transition shadow-xs">
            <Building2 className="w-3.5 h-3.5 text-[#65708B] shrink-0" />
            <select
              value={selectedWard}
              onChange={(e) => onSelectWard(e.target.value)}
              className="bg-transparent text-[#11162A] text-xs font-medium outline-none cursor-pointer max-w-[140px] truncate"
            >
              {wards.map((w) => (
                <option key={w} value={w} className="bg-white text-[#11162A]">
                  {w}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Motion Preference Toggle */}
        <button
          type="button"
          onClick={toggleMotionMode}
          title={`Animation Mode: ${isReduced ? 'REDUCED' : 'FULL'} (Click to toggle)`}
          className={cn(
            'hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer border shadow-xs',
            !isReduced
              ? 'bg-[#6457E8]/10 border-[#6457E8]/30 text-[#6457E8] hover:bg-[#6457E8]/15'
              : 'bg-slate-100 border-slate-300 text-slate-700 hover:bg-slate-200/70'
          )}
        >
          <Zap className={cn('w-3.5 h-3.5', !isReduced ? 'text-[#6457E8]' : 'text-slate-500')} />
          <span className="hidden 2xl:inline text-[11px] font-mono font-semibold tracking-tight">
            {isReduced ? 'MOTION: REDUCED' : 'MOTION: FULL'}
          </span>
        </button>

        {/* Demo Mode Button (Inspector & Admin only) */}
        {onStartDemo && user?.role !== 'citizen' && (
          <button
            type="button"
            onClick={onStartDemo}
            title="Interactive Walkthrough (Alt+D)"
            className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer border shadow-xs ${
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

        {/* Reset Demo Button (ADMIN ONLY) */}
        {user?.role === 'admin' && (
          <button
            type="button"
            onClick={onResetDemo}
            title="Reset baseline records (Alt+R)"
            className="p-1.5 bg-white hover:bg-slate-50 border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] rounded-xl transition cursor-pointer shadow-xs"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        )}

        {/* Primary Action: New Complaint */}
        <button
          type="button"
          onClick={onOpenNewComplaint}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs font-semibold transition active:scale-95 cursor-pointer shadow-sm shrink-0"
        >
          <PlusCircle className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden md:inline">New Complaint</span>
          <span className="md:hidden">New</span>
        </button>

        {/* Authenticated User / Account Menu Control */}
        {user && (
          <div className="relative pl-1 sm:pl-2 border-l border-[#E4E7F1]" ref={accountMenuRef}>
            <button
              type="button"
              onClick={() => setIsAccountOpen(!isAccountOpen)}
              aria-expanded={isAccountOpen}
              aria-haspopup="true"
              id="civilens-account-menu-trigger"
              title={`Account Menu: ${user.name || user.username} (${user.role.toUpperCase()})`}
              className={cn(
                'flex items-center gap-1.5 sm:gap-2 px-2 py-1 rounded-xl border transition cursor-pointer shadow-xs text-xs select-none',
                isAccountOpen
                  ? 'bg-slate-100 border-[#6457E8] ring-2 ring-[#6457E8]/20'
                  : 'bg-white hover:bg-slate-50 border-[#E4E7F1]'
              )}
            >
              <div
                className={cn(
                  'w-6 h-6 rounded-lg font-bold flex items-center justify-center text-[10px] text-white shadow-2xs shrink-0',
                  user.role === 'admin'
                    ? 'bg-[#6457E8]'
                    : user.role === 'inspector'
                    ? 'bg-[#13152E]'
                    : 'bg-[#10B981]'
                )}
              >
                {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div className="hidden sm:flex flex-col items-start text-left leading-tight max-w-[85px] md:max-w-[110px] xl:max-w-[140px] truncate">
                <span className="font-semibold text-[#11162A] text-xs truncate w-full">
                  {user.name || user.username}
                </span>
                <span className="text-[9px] text-[#65708B] font-mono uppercase tracking-wider truncate">
                  {user.role === 'inspector' ? 'OFFICER' : user.role.toUpperCase()}
                </span>
              </div>
              <ChevronDown
                className={cn(
                  'w-3.5 h-3.5 text-[#65708B] transition-transform duration-200 shrink-0',
                  isAccountOpen && 'rotate-180'
                )}
              />
            </button>

            {/* Account Dropdown Menu */}
            {isAccountOpen && (
              <div
                className="absolute right-0 top-full mt-2 w-72 bg-white rounded-2xl shadow-xl border border-[#E4E7F1] py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150 font-sans"
                role="menu"
                aria-orientation="vertical"
                aria-labelledby="civilens-account-menu-trigger"
              >
                {/* User Details Header */}
                <div className="px-4 py-3 border-b border-[#E4E7F1]">
                  <div className="flex items-center gap-2.5">
                    <div
                      className={cn(
                        'w-9 h-9 rounded-xl font-bold flex items-center justify-center text-sm text-white shadow-xs shrink-0',
                        user.role === 'admin'
                          ? 'bg-[#6457E8]'
                          : user.role === 'inspector'
                          ? 'bg-[#13152E]'
                          : 'bg-[#10B981]'
                      )}
                    >
                      {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-bold text-[#11162A] truncate">
                        {user.name || user.username}
                      </p>
                      <p className="text-[11px] text-[#65708B] truncate">
                        {user.email || user.username}
                      </p>
                    </div>
                  </div>

                  {/* Verified Role Pill */}
                  <div className="mt-2.5 flex items-center justify-between pt-2 border-t border-slate-100">
                    <span className="text-[11px] font-medium text-[#65708B]">Verified Role</span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded-full font-mono font-bold text-[10px] uppercase border tracking-wide flex items-center gap-1',
                        user.role === 'admin'
                          ? 'bg-purple-50 text-purple-700 border-purple-200'
                          : user.role === 'inspector'
                          ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      )}
                    >
                      <Shield className="w-3 h-3 shrink-0" />
                      {user.role === 'admin'
                        ? 'ADMINISTRATOR'
                        : user.role === 'inspector'
                        ? 'MUNICIPAL OFFICER'
                        : 'CITIZEN'}
                    </span>
                  </div>

                  <div className="mt-1.5 flex items-center justify-between text-[10px] text-[#65708B]">
                    <span>Account ID</span>
                    <span className="font-mono text-slate-700 font-semibold">{user.userId}</span>
                  </div>
                </div>

                {/* Session Status */}
                <div className="px-4 py-2 flex items-center justify-between text-[11px] text-[#65708B] bg-slate-50/70 border-b border-[#E4E7F1]">
                  <span className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="font-medium text-slate-700">Authenticated Session</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">HMAC-SHA256</span>
                </div>

                {/* Dropdown Actions */}
                <div className="px-2 pt-1.5">
                  <button
                    type="button"
                    onClick={async () => {
                      setIsAccountOpen(false)
                      await logout()
                    }}
                    id="civilens-logout-action"
                    className="w-full flex items-center gap-2.5 px-3 py-2 text-xs font-semibold text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded-xl transition cursor-pointer"
                    role="menuitem"
                  >
                    <LogOut className="w-4 h-4 shrink-0 text-rose-500" />
                    <span>Log Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  )
}

export default TopBar
