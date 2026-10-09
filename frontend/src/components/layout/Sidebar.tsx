import React from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  Sparkles,
  Map,
  Flame,
  RotateCcw,
  Camera,
  CheckCircle2,
  BarChart3,
  ShieldAlert,
  FileText,
  Activity,
  Cpu,
  Settings2,
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
  const navSections = [
    {
      title: 'OPERATIONS',
      items: [
        { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
        { id: 'analyze', label: 'Analyze Issue', icon: Sparkles },
        { id: 'intelligence', label: 'Issue Intelligence', icon: FileText },
        { id: 'map', label: 'Tactical GIS Map', icon: Map },
      ],
    },
    {
      title: 'SPATIOTEMPORAL INTELLIGENCE',
      items: [
        {
          id: 'hotspots',
          label: 'Hotspots',
          icon: Flame,
          badge: hotspotCount > 0 ? String(hotspotCount) : undefined,
          badgeColor: 'bg-rose-950 text-rose-300 border-rose-800',
        },
        { id: 'recurring', label: 'Recurring Defects', icon: RotateCcw },
        {
          id: 'unreported',
          label: 'Unreported Patrols',
          icon: Camera,
          badge: unreportedCount > 0 ? String(unreportedCount) : undefined,
          badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800',
        },
      ],
    },
    {
      title: 'VERIFICATION & AUDIT',
      items: [
        { id: 'resolution', label: 'Resolution Center', icon: CheckCircle2 },
        { id: 'analytics', label: 'Model Benchmarks', icon: BarChart3 },
      ],
    },
  ]

  return (
    <aside className="w-60 bg-[#0a0d14] border-r border-[#1a2130] flex flex-col h-screen shrink-0 select-none z-30 font-sans">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#1a2130] bg-[#0c1018]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-700 flex items-center justify-center shadow-lg shadow-cyan-950/50 border border-cyan-400/40 shrink-0">
            <ShieldAlert className="w-4 h-4 text-white" />
          </div>
          <div className="min-w-0">
            <div className="font-mono text-sm font-bold tracking-wider text-slate-100 flex items-center gap-1.5">
              CIVILENS
              <span className="text-[9px] px-1.5 py-0.2 bg-cyan-950 border border-cyan-800 text-cyan-400 rounded font-mono">
                v2.4
              </span>
            </div>
            <div className="text-[10px] text-slate-400 tracking-wide font-sans">
              Civic Issue Intelligence
            </div>
          </div>
        </div>
      </div>

      {/* Grouped Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-2 pb-1 text-[10px] uppercase font-mono tracking-wider text-slate-400 font-semibold">
              {section.title}
            </div>

            {section.items.map((item) => {
              const Icon = item.icon
              const isActive = activeView === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectView(item.id)}
                  className={cn(
                    'w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-all group relative cursor-pointer',
                    isActive
                      ? 'bg-[#151c2a] text-cyan-300 font-semibold shadow-sm border border-cyan-900/50'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#101522]'
                  )}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon
                      className={cn(
                        'w-4 h-4 transition-colors shrink-0',
                        isActive
                          ? 'text-cyan-400'
                          : 'text-slate-500 group-hover:text-slate-300'
                      )}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={cn(
                        'text-[10px] font-mono px-1.5 py-0.2 rounded border font-semibold shrink-0 ml-1.5',
                        item.badgeColor
                      )}
                    >
                      {item.badge}
                    </span>
                  )}

                  {isActive && (
                    <motion.div
                      layoutId="sidebarActivePill"
                      className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-cyan-400 rounded-r shadow-[0_0_8px_rgba(6,182,212,0.8)]"
                      transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                    />
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      {/* Critical Indicator Strip */}
      {criticalCount > 0 && (
        <div className="px-3 py-2 mx-3 mb-2 rounded-lg bg-rose-950/40 border border-rose-900/60 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-rose-300">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse shrink-0" />
            <span className="text-xs font-semibold">Critical Incidents</span>
          </div>
          <span className="px-1.5 py-0.5 rounded bg-rose-900 text-rose-100 font-mono font-bold text-[10px]">
            {criticalCount}
          </span>
        </div>
      )}

      {/* Bottom Operational Controls */}
      <div className="p-3 border-t border-[#1a2130] bg-[#0c1018] space-y-1.5 text-xs">
        <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-[#101520] border border-slate-800/80">
          <div className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-xs text-slate-300 font-medium">Pipeline Status</span>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-bold font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            ONLINE
          </span>
        </div>

        <div className="flex items-center gap-1.5 pt-1">
          <button
            onClick={onOpenModelStatus}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#101520] hover:bg-[#151c2a] text-slate-400 hover:text-slate-200 border border-slate-800 rounded-lg text-xs transition cursor-pointer"
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI Status</span>
          </button>
          <button
            onClick={onOpenSettings}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-[#101520] hover:bg-[#151c2a] text-slate-400 hover:text-slate-200 border border-slate-800 rounded-lg text-xs transition cursor-pointer"
          >
            <Settings2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Routing</span>
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
