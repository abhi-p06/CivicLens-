import React, { useEffect } from 'react'
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
  RefreshCw,
  PlusCircle,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react'
import { Issue } from '../../types'
import {
  CommandDialog,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
  CommandShortcut,
} from '../ui/command'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  onNavigate: (viewId: string) => void
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
  onOpenSubmit: () => void
  onResetDemo: () => void
  onRunScenario: (scenarioNum: number) => void
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  isOpen,
  onClose,
  onNavigate,
  issues,
  onSelectIssue,
  onOpenSubmit,
  onResetDemo,
  onRunScenario,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (isOpen) {
          onClose()
        }
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const views = [
    { id: 'overview', label: 'Command Center Overview', icon: LayoutDashboard },
    { id: 'analyze', label: 'Analyze Complaint (AI Laboratory)', icon: Sparkles },
    { id: 'intelligence', label: 'Issue Intelligence & Evidence', icon: AlertTriangle },
    { id: 'map', label: 'Tactical GIS Issue Map', icon: Map },
    { id: 'live', label: 'Live Incident Stream', icon: Radio },
    { id: 'explorer', label: 'Complaint Catalog Explorer', icon: ListFilter },
    { id: 'hotspots', label: 'Spatial Hotspots (DBSCAN)', icon: Flame },
    { id: 'recurring', label: 'Recurring Defect Analysis', icon: RotateCcw },
    { id: 'unreported', label: 'Unreported Patrol Detections', icon: Camera },
    { id: 'resolution', label: 'Resolution Center & SLA', icon: CheckCircle2 },
    { id: 'analytics', label: 'Model Benchmarks & Metrics', icon: BarChart3 },
  ]

  return (
    <CommandDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <CommandInput placeholder="Type a command, view, or municipal incident..." />
      <CommandList>
        <CommandEmpty>No matching commands or incidents found.</CommandEmpty>

        <CommandGroup heading="Quick Actions">
          <CommandItem
            onSelect={() => {
              onClose()
              onOpenSubmit()
            }}
            className="cursor-pointer"
          >
            <PlusCircle className="mr-2.5 h-4 w-4 text-cyan-600" />
            <span className="font-medium text-slate-900">Intake New Citizen Complaint</span>
            <CommandShortcut className="text-slate-400">Ctrl+N</CommandShortcut>
          </CommandItem>
          <CommandItem
            onSelect={() => {
              onClose()
              onRunScenario(1)
            }}
            className="cursor-pointer"
          >
            <Flame className="mr-2.5 h-4 w-4 text-rose-500" />
            <span>Load Scenario 1: Severe Pothole Accident Hazard (Vidyavihar)</span>
          </CommandItem>
          <CommandItem
            onSelect={() => {
              onClose()
              onRunScenario(2)
            }}
            className="cursor-pointer"
          >
            <Flame className="mr-2.5 h-4 w-4 text-amber-500" />
            <span>Load Scenario 2: Massive Garbage Overflow & Stench (LBS Marg)</span>
          </CommandItem>
          <CommandItem
            onSelect={() => {
              onClose()
              onRunScenario(3)
            }}
            className="cursor-pointer"
          >
            <Flame className="mr-2.5 h-4 w-4 text-sky-500" />
            <span>Load Scenario 3: Water Main Pipe Burst & Flooding (Dharavi)</span>
          </CommandItem>
          <CommandItem
            onSelect={() => {
              onClose()
              onResetDemo()
            }}
            className="cursor-pointer"
          >
            <RefreshCw className="mr-2.5 h-4 w-4 text-slate-500" />
            <span>Reset Demo State to Baseline</span>
            <CommandShortcut className="text-slate-400">Alt+R</CommandShortcut>
          </CommandItem>
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="System Navigation">
          {views.map((v) => {
            const Icon = v.icon
            return (
              <CommandItem
                key={v.id}
                onSelect={() => {
                  onClose()
                  onNavigate(v.id)
                }}
                className="cursor-pointer"
              >
                <Icon className="mr-2.5 h-4 w-4 text-slate-500" />
                <span>{v.label}</span>
                <ArrowRight className="ml-auto h-3 w-3 text-slate-300" />
              </CommandItem>
            )
          })}
        </CommandGroup>

        <CommandSeparator />

        <CommandGroup heading="Recent Incidents">
          {issues.slice(0, 5).map((iss) => (
            <CommandItem
              key={iss.issueId}
              onSelect={() => {
                onClose()
                onSelectIssue(iss)
              }}
              className="cursor-pointer"
            >
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-semibold text-cyan-600">
                    {iss.issueId}
                  </span>
                  <span className="text-xs text-slate-700 font-medium truncate max-w-sm">
                    {iss.category} — {iss.location}
                  </span>
                </div>
                <span className="text-[11px] text-slate-400 truncate max-w-md">
                  {iss.complaintText}
                </span>
              </div>
              <span className="ml-auto text-[11px] font-semibold text-slate-500">
                Score {iss.priorityScore}
              </span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  )
}

export default CommandPalette
