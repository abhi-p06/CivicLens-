import React from 'react'
import {
  LayoutDashboard,
  Radio,
  Sparkles,
  ListFilter,
  Map,
  Flame,
  RotateCcw,
  Camera,
  CheckCircle2,
  BarChart3,
  Cpu,
  Settings2,
  Activity,
  ShieldAlert,
  FileText,
} from 'lucide-react'
import { cn } from '../../lib/utils'

interface SidebarProps {
  activeView: string
  onSelectView: (viewId: string) => void
  criticalCount?: number
  hotspotCount?: number
  unreportedCount?: number
  onOpenModelStatus: () => void
  onOpenSettings: () => void
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onSelectView,
  criticalCount = 0,
  hotspotCount = 0,
  unreportedCount = 0,
  onOpenModelStatus,
  onOpenSettings,
}) => {
  const navItems = [
    { id: 'overview', label: '1. Command Center', icon: LayoutDashboard },
    { id: 'analyze', label: '2. Analyze Complaint', icon: Sparkles },
    { id: 'intelligence', label: '3. Issue Intelligence', icon: FileText },
    { id: 'map', label: '4. Tactical GIS Map', icon: Map },
    {
      id: 'hotspots',
      label: '5. Hotspots',
      icon: Flame,
      badge: hotspotCount > 0 ? String(hotspotCount) : undefined,
      badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
    },
    { id: 'recurring', label: '6. Recurring Issues', icon: RotateCcw },
    {
      id: 'unreported',
      label: '7. Unreported Issues',
      icon: Camera,
      badge: unreportedCount > 0 ? String(unreportedCount) : undefined,
      badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800',
    },
    { id: 'resolution', label: '8. Resolution Center', icon: CheckCircle2 },
    { id: 'analytics', label: '9. Analytics', icon: BarChart3 },
    { id: 'live', label: 'Live Incident Radar', icon: Radio, pulse: true },
    { id: 'explorer', label: 'Complaint Explorer', icon: ListFilter },
  ]

  return (
    <aside className="w-64 bg-[#0a0d14] border-r border-[#1a2130] flex flex-col h-screen shrink-0 select-none z-30 font-sans">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#1a2130] bg-[#0c1018]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-700 flex items-center justify-center shadow-lg shadow-cyan-950/50 border border-cyan-400/40">
            <ShieldAlert className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-mono text-sm font-bold tracking-wider text-slate-100 flex items-center gap-1.5">
              CIVILENS
              <span className="text-[9px] px-1.5 py-0.2 bg-cyan-950 border border-cyan-800 text-cyan-400 rounded font-normal">
                v2.4
              </span>
            </div>
            <div className="text-[10px] text-slate-400 tracking-tight font-mono">
              COMMAND CENTER &bull; OPS
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-2.5 py-3 space-y-1">
        <div className="px-2 pb-1 text-[10px] uppercase font-mono tracking-wider text-slate-400 font-semibold">
          Operational Views
        </div>

        {navItems.map((item) => {
          const Icon = item.icon
          const isActive = activeView === item.id
          return (
            <button
              key={item.id}
              onClick={() => onSelectView(item.id)}
              className={cn(
                'w-full flex items-center justify-between px-2.5 py-2 rounded-md text-xs font-medium transition-all group relative',
                isActive
                  ? 'bg-[#151c2a] text-cyan-300 font-semibold shadow-sm border border-cyan-900/50'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-[#101522]'
              )}
            >
              <div className="flex items-center gap-2.5">
                <Icon
                  className={cn(
                    'w-4 h-4 transition-colors shrink-0',
                    isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300',
                    item.pulse && 'text-cyan-400 animate-pulse'
                  )}
                />
                <span className="truncate">{item.label}</span>
              </div>

              {item.badge && (
                <span
                  className={cn(
                    'text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold shrink-0',
                    item.badgeColor
                  )}
                >
                  {item.badge}
                </span>
              )}

              {isActive && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-cyan-400 rounded-r" />
              )}
            </button>
          )
        })}
      </div>

      {/* Critical Indicator Strip */}
      {criticalCount > 0 && (
        <div className="px-3 py-2 mx-2 mb-2 rounded bg-rose-950/40 border border-rose-900/60 flex items-center justify-between text-xs font-mono">
          <div className="flex items-center gap-2 text-rose-300">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            <span className="text-[11px] font-bold">CRITICAL INCIDENTS</span>
          </div>
          <span className="px-1.5 py-0.5 rounded bg-rose-900 text-rose-100 font-bold text-[10px]">
            {criticalCount}
          </span>
        </div>
      )}

      {/* Bottom Operational Controls */}
      <div className="p-3 border-t border-[#1a2130] bg-[#0c1018] space-y-1 font-mono text-xs">
        {/* System Status */}
        <div className="flex items-center justify-between px-2 py-1.5 rounded bg-[#101520] border border-slate-800/80 mb-1">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-[11px] text-slate-300 font-medium">SYS STATUS</span>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE
          </span>
        </div>

        {/* Model Status Modal Trigger */}
        <button
          onClick={onOpenModelStatus}
          className="w-full flex items-center justify-between px-2 py-1.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-[#121824] transition"
        >
          <div className="flex items-center gap-2">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[11px]">Model Telemetry</span>
          </div>
          <span className="text-[9px] text-cyan-400 uppercase">ONLINE</span>
        </button>

        {/* Settings Modal Trigger */}
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center justify-between px-2 py-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-[#121824] transition"
        >
          <div className="flex items-center gap-2">
            <Settings2 className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[11px]">Dispatch Config</span>
          </div>
          <span className="text-[9px] text-slate-400 uppercase">SLAs</span>
        </button>
      </div>
    </aside>
  )
}
