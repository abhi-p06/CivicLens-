import React from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  ScanSearch,
  Activity,
  Map,
  Flame,
  History,
  Radar,
  CheckCircle2,
  BarChart3,
  ShieldCheck,
  Cpu,
  Settings2,
  Radio,
  FolderOpen,
} from 'lucide-react'
import {
  Sidebar as ShadcnSidebar,
  SidebarHeader,
  SidebarContent,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarFooter,
  SidebarTrigger,
  useSidebar,
} from '../ui/sidebar'
import { cn } from '../../lib/utils'
import { useAuth } from '../../context/AuthContext'

interface SidebarProps {
  activeView: string
  onSelectView: (viewId: string) => void
  criticalCount?: number
  hotspotCount?: number
  unreportedCount?: number
  onOpenModelStatus: () => void
  onOpenSettings: () => void
}

interface NavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
  badgeColor?: string
}

interface NavSection {
  title: string
  items: NavItem[]
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
  const { open } = useSidebar()
  const { user } = useAuth()
  const role = user?.role || 'citizen'

  const navSections: NavSection[] = React.useMemo(() => {
    if (role === 'citizen') {
      return [
        {
          title: 'MY WORKSPACE',
          items: [
            { id: 'citizen_portal', label: 'My Grievances', icon: FolderOpen },
            { id: 'map', label: 'Civic Map', icon: Map },
            { id: 'analyze', label: 'Check Photo / Text', icon: ScanSearch },
          ],
        },
      ]
    }

    if (role === 'inspector') {
      return [
        {
          title: 'OPERATIONS',
          items: [
            { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
            { id: 'explorer', label: 'Priority Queue', icon: FolderOpen },
            { id: 'map', label: 'Tactical GIS Map', icon: Map },
            { id: 'intelligence', label: 'Issue Dossier', icon: Activity },
            { id: 'live', label: 'Live Radar', icon: Radio },
          ],
        },
        {
          title: 'VERIFICATION',
          items: [
            { id: 'resolution', label: 'Resolution Center', icon: CheckCircle2 },
            { id: 'analytics', label: 'Model Benchmarks', icon: BarChart3 },
          ],
        },
      ]
    }

    return [
      {
        title: 'OPERATIONS',
        items: [
          { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
          { id: 'analyze', label: 'Analyze Complaint', icon: ScanSearch },
          { id: 'intelligence', label: 'Issue Intelligence', icon: Activity },
          { id: 'map', label: 'Tactical GIS Map', icon: Map },
          { id: 'live', label: 'Live Radar', icon: Radio },
          { id: 'explorer', label: 'Issue Catalog', icon: FolderOpen },
        ],
      },
      {
        title: 'SPATIAL INTELLIGENCE',
        items: [
          {
            id: 'hotspots',
            label: 'Hotspots',
            icon: Flame,
            badge: hotspotCount > 0 ? String(hotspotCount) : undefined,
            badgeColor: 'bg-rose-500/15 text-rose-300 border-rose-500/25',
          },
          { id: 'recurring', label: 'Recurring Issues', icon: History },
          {
            id: 'unreported',
            label: 'Unreported Issues',
            icon: Radar,
            badge: unreportedCount > 0 ? String(unreportedCount) : undefined,
            badgeColor: 'bg-[#8B5CF6]/20 text-[#C4B5FD] border-[#8B5CF6]/30',
          },
        ],
      },
      {
        title: 'VERIFICATION',
        items: [
          { id: 'resolution', label: 'Resolution Center', icon: CheckCircle2 },
          { id: 'analytics', label: 'Model Benchmarks', icon: BarChart3 },
        ],
      },
    ]
  }, [role, hotspotCount, unreportedCount])

  return (
    <ShadcnSidebar>
      {/* 1. BRAND HEADER */}
      <SidebarHeader className="justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-[#6457E8]/15 border border-[#8B5CF6]/30 flex items-center justify-center text-[#8B5CF6] shrink-0">
            <ShieldCheck className="w-4 h-4 text-[#8B5CF6]" />
          </div>

          {open && (
            <motion.div
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -6 }}
              transition={{ duration: 0.16 }}
              className="min-w-0 flex flex-col justify-center"
            >
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-bold tracking-tight text-white font-sans">
                  CIVILENS
                </span>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/[0.08] border border-white/[0.1] text-slate-300 font-medium font-mono">
                  v2.4
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-normal leading-none mt-0.5">
                Civic Intelligence
              </p>
            </motion.div>
          )}
        </div>

        <SidebarTrigger />
      </SidebarHeader>

      {/* 2. PRIMARY NAVIGATION GROUPS */}
      <SidebarContent>
        {navSections.map((section) => (
          <SidebarGroup key={section.title}>
            <SidebarGroupLabel>{section.title}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {section.items.map((item) => {
                  const Icon = item.icon
                  const isActive = activeView === item.id

                  return (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton
                        isActive={isActive}
                        tooltip={item.label}
                        onClick={() => onSelectView(item.id)}
                      >
                        <Icon
                          className={cn(
                            'w-4 h-4 shrink-0 transition-colors',
                            isActive ? 'text-[#8B5CF6]' : 'text-slate-300 group-hover:text-white'
                          )}
                        />

                        {open && (
                          <span className="truncate flex-1 text-left">
                            {item.label}
                          </span>
                        )}

                        {open && item.badge && (
                          <span
                            className={cn(
                              'px-1.5 py-0.5 rounded-full text-[10px] font-mono font-semibold border shrink-0',
                              item.badgeColor
                            )}
                          >
                            {item.badge}
                          </span>
                        )}
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  )
                })}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>

      {/* 3. CRITICAL INCIDENTS BANNER */}
      {criticalCount > 0 && open && (
        <div className="px-3 py-2 mx-3 mb-2 rounded-lg bg-[#EF4444]/15 border border-[#EF4444]/25 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-rose-300 min-w-0">
            <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse shrink-0" />
            <span className="font-medium truncate">Critical Incidents</span>
          </div>
          <span className="px-2 py-0.5 rounded-full bg-[#EF4444]/20 text-rose-200 font-mono font-semibold text-[11px] shrink-0">
            {criticalCount}
          </span>
        </div>
      )}

      {/* 4. BOTTOM UTILITY CONTROLS */}
      <SidebarFooter>
        {/* System Status Indicator */}
        {open ? (
          <div className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06]">
            <span className="text-slate-400 text-xs font-normal">Pipeline Engine</span>
            <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Online
            </span>
          </div>
        ) : (
          <div
            className="flex items-center justify-center py-1.5 relative group cursor-help"
            title="Pipeline Engine: Online"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
          </div>
        )}

        {/* Role-Restricted Utility Controls */}
        {role !== 'citizen' && (
          open ? (
            <div className="flex items-center gap-2 pt-0.5">
              <button
                id="sidebar-model-status-btn"
                onClick={onOpenModelStatus}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/[0.08] rounded-lg text-xs font-medium transition cursor-pointer"
              >
                <Cpu className="w-3.5 h-3.5 text-[#8B5CF6]" />
                <span>AI Models</span>
              </button>
              {role === 'admin' && (
                <button
                  id="sidebar-settings-btn"
                  onClick={onOpenSettings}
                  className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 hover:text-white border border-white/[0.08] rounded-lg text-xs font-medium transition cursor-pointer"
                >
                  <Settings2 className="w-3.5 h-3.5 text-slate-400" />
                  <span>Settings</span>
                </button>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1.5">
              <button
                id="sidebar-model-status-btn"
                onClick={onOpenModelStatus}
                className="p-2 bg-white/[0.04] hover:bg-white/[0.08] text-[#8B5CF6] border border-white/[0.08] rounded-lg transition cursor-pointer"
                title="AI Models Status"
              >
                <Cpu className="w-4 h-4" />
              </button>
              {role === 'admin' && (
                <button
                  id="sidebar-settings-btn"
                  onClick={onOpenSettings}
                  className="p-2 bg-white/[0.04] hover:bg-white/[0.08] text-slate-400 hover:text-white border border-white/[0.08] rounded-lg transition cursor-pointer"
                  title="Platform Settings"
                >
                  <Settings2 className="w-4 h-4" />
                </button>
              )}
            </div>
          )
        )}
      </SidebarFooter>
    </ShadcnSidebar>
  )
}

export default Sidebar
