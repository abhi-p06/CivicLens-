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
        { id: 'analyze', label: 'Analyze Complaint', icon: Sparkles },
        { id: 'intelligence', label: 'Issue Intelligence', icon: FileText },
        { id: 'map', label: 'Tactical GIS Map', icon: Map },
      ],
    },
    {
      title: 'SPATIAL INTELLIGENCE',
      items: [
        {
          id: 'hotspots',
          label: 'Spatiotemporal Hotspots',
          icon: Flame,
          badge: hotspotCount > 0 ? String(hotspotCount) : undefined,
          badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-800',
        },
        { id: 'recurring', label: 'Recurring Defects', icon: RotateCcw },
        {
          id: 'unreported',
          label: 'Unreported Patrols',
          icon: Camera,
          badge: unreportedCount > 0 ? String(unreportedCount) : undefined,
          badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-800',
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
    <aside className="w-64 bg-[#090c13] border-r border-slate-800/90 flex flex-col h-screen shrink-0 select-none z-30 font-sans">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 bg-[#0b0f17]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-700 flex items-center justify-center shadow-lg shadow-cyan-950/60 border border-cyan-400/40 shrink-0">
            <ShieldAlert className="w-5 h-5 text-white" />
          </div>
          <div className="min-w-0">
            <div className="font-mono text-base font-bold tracking-wider text-slate-100 flex items-center gap-2">
              CIVILENS
              <span className="text-[10px] px-1.5 py-0.5 bg-cyan-950 border border-cyan-700/80 text-cyan-400 rounded-md font-mono font-medium">
                v2.4
              </span>
            </div>
            <div className="text-xs text-slate-400 tracking-wide font-sans">
              Civic Infrastructure AI
            </div>
          </div>
        </div>
      </div>

      {/* Grouped Navigation Links */}
      <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-6">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1.5">
            <div className="px-3 pb-1 text-xs font-semibold tracking-wider text-slate-400 uppercase font-mono">
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
                    'w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group relative cursor-pointer',
                    isActive
                      ? 'bg-[#131b29] text-cyan-300 font-semibold shadow-sm border border-cyan-800/50'
                      : 'text-slate-300 hover:text-white hover:bg-[#0e1420]'
                  )}
                >
                  <div className="flex items-center gap-3 truncate">
                    <Icon
                      className={cn(
                        'w-[18px] h-[18px] transition-colors shrink-0',
                        isActive
                          ? 'text-cyan-400'
                          : 'text-slate-400 group-hover:text-slate-200'
                      )}
                    />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {item.badge && (
                    <span
                      className={cn(
                        'text-xs font-mono px-2 py-0.5 rounded-md border font-semibold shrink-0 ml-1.5',
                        item.badgeColor
                      )}
                    >
                      {item.badge}
                    </span>
                  )}

                  {isActive && (
                    <motion.div
                      layoutId="sidebarActivePill"
                      className="absolute left-0 top-2 bottom-2 w-1 bg-cyan-400 rounded-r shadow-[0_0_10px_rgba(6,182,212,0.9)]"
                      transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                    />
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </div>

      {/* Critical Incidents Warning Banner */}
      {criticalCount > 0 && (
        <div className="px-3.5 py-2.5 mx-3.5 mb-3 rounded-lg bg-rose-950/40 border border-rose-900/70 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-rose-300">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse shrink-0" />
            <span className="text-xs font-semibold">Critical Incidents</span>
          </div>
          <span className="px-2 py-0.5 rounded bg-rose-900 text-rose-100 font-mono font-bold text-xs">
            {criticalCount}
          </span>
        </div>
      )}

      {/* Bottom Operational Controls */}
      <div className="p-4 border-t border-slate-800/80 bg-[#0b0f17] space-y-2 text-xs">
        <div className="flex items-center justify-between px-3 py-2 rounded-lg bg-[#101622] border border-slate-800">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            <span className="text-xs text-slate-300 font-medium">Pipeline Status</span>
          </div>
          <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-bold font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            ONLINE
          </span>
        </div>

        <div className="flex items-center gap-2 pt-0.5">
          <button
            onClick={onOpenModelStatus}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 px-2 bg-[#101622] hover:bg-[#151c2a] text-slate-300 hover:text-white border border-slate-800 rounded-lg text-xs font-medium transition cursor-pointer"
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>AI Models</span>
          </button>
          <button
            onClick={onOpenSettings}
            className="flex-1 flex items-center justify-center gap-1.5 py-2 px-2 bg-[#101622] hover:bg-[#151c2a] text-slate-300 hover:text-white border border-slate-800 rounded-lg text-xs font-medium transition cursor-pointer"
          >
            <Settings2 className="w-3.5 h-3.5 text-slate-400" />
            <span>Dispatch</span>
          </button>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
