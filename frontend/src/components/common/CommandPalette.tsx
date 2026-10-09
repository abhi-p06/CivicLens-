import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
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
  X,
} from 'lucide-react'
import { Issue } from '../../types'

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
  const [query, setQuery] = useState('')

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (isOpen) onClose()
        else setQuery('')
      }
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const views = [
    { id: 'overview', label: 'Overview Command Dashboard', icon: LayoutDashboard },
    { id: 'live', label: 'Live Intelligence Stream', icon: Radio },
    { id: 'analyze', label: 'Analyze Complaint (AI Laboratory)', icon: Sparkles },
    { id: 'explorer', label: 'Complaint Explorer', icon: ListFilter },
    { id: 'map', label: 'Tactical GIS Issue Map', icon: Map },
    { id: 'hotspots', label: 'Spatiotemporal Hotspots', icon: Flame },
    { id: 'recurring', label: 'Recurring Defect Analysis', icon: RotateCcw },
    { id: 'unreported', label: 'Unreported Patrol Detections', icon: Camera },
    { id: 'resolution', label: 'Resolution Verification & Lifecycle', icon: CheckCircle2 },
    { id: 'analytics', label: 'Model Evaluation & Analytics', icon: BarChart3 },
  ]

  const filteredViews = views.filter((v) =>
    v.label.toLowerCase().includes(query.toLowerCase())
  )

  const filteredIssues = issues
    .filter(
      (i) =>
        i.issueId.toLowerCase().includes(query.toLowerCase()) ||
        i.complaintText.toLowerCase().includes(query.toLowerCase()) ||
        i.category.toLowerCase().includes(query.toLowerCase()) ||
        i.location.toLowerCase().includes(query.toLowerCase())
    )
    .slice(0, 5)

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-start justify-center pt-20 px-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl bg-[#0e131d] border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden font-mono text-xs"
          >
            {/* Search header */}
            <div className="flex items-center px-4 py-3 border-b border-slate-800 bg-[#121824]">
              <Search className="w-5 h-5 text-cyan-400 mr-3 shrink-0" />
              <input
                autoFocus
                type="text"
                placeholder="Search commands, views, or civic issues (e.g., 'pothole', 'map', 'CIVIC-001')..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 outline-none font-mono"
              />
              <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-800 border border-slate-700 rounded mr-2">
                ESC
              </kbd>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="max-h-96 overflow-y-auto p-2 divide-y divide-slate-800/60 font-mono text-xs">
              {/* Quick Actions */}
              <div className="py-2">
                <div className="px-3 py-1 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                  Quick Actions
                </div>
                <button
                  onClick={() => {
                    onClose()
                    onOpenSubmit()
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-200 hover:bg-cyan-950/40 hover:text-cyan-300 rounded transition text-left"
                >
                  <PlusCircle className="w-4 h-4 text-cyan-400" />
                  <span>Intake New Citizen Complaint</span>
                </button>
                <button
                  onClick={() => {
                    onClose()
                    onRunScenario(1)
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-200 hover:bg-rose-950/40 hover:text-rose-300 rounded transition text-left"
                >
                  <Flame className="w-4 h-4 text-rose-400" />
                  <span>Load Scenario 1: Severe Pothole Accident Hazard (Vidyavihar)</span>
                </button>
                <button
                  onClick={() => {
                    onClose()
                    onRunScenario(2)
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-200 hover:bg-amber-950/40 hover:text-amber-300 rounded transition text-left"
                >
                  <Flame className="w-4 h-4 text-amber-400" />
                  <span>Load Scenario 2: Massive Garbage Overflow & Stench (LBS Marg)</span>
                </button>
                <button
                  onClick={() => {
                    onClose()
                    onRunScenario(3)
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-200 hover:bg-sky-950/40 hover:text-sky-300 rounded transition text-left"
                >
                  <Flame className="w-4 h-4 text-sky-400" />
                  <span>Load Scenario 3: Water Main Pipe Burst & Flooding (Dharavi)</span>
                </button>
                <button
                  onClick={() => {
                    onClose()
                    onResetDemo()
                  }}
                  className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-200 hover:bg-slate-800 rounded transition text-left"
                >
                  <RefreshCw className="w-4 h-4 text-slate-400" />
                  <span>Reset Demo State to Baseline</span>
                </button>
              </div>

              {/* Navigation Views */}
              {filteredViews.length > 0 && (
                <div className="py-2">
                  <div className="px-3 py-1 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                    System Views
                  </div>
                  {filteredViews.map((v) => {
                    const Icon = v.icon
                    return (
                      <button
                        key={v.id}
                        onClick={() => {
                          onClose()
                          onNavigate(v.id)
                        }}
                        className="w-full flex items-center gap-2.5 px-3 py-2 text-slate-300 hover:bg-cyan-950/40 hover:text-cyan-300 rounded transition text-left"
                      >
                        <Icon className="w-4 h-4 text-slate-400" />
                        <span>{v.label}</span>
                      </button>
                    )
                  })}
                </div>
              )}

              {/* Matched Issues */}
              {filteredIssues.length > 0 && (
                <div className="py-2">
                  <div className="px-3 py-1 text-[10px] uppercase tracking-wider text-slate-500 font-bold">
                    Incident Match ({filteredIssues.length})
                  </div>
                  {filteredIssues.map((issue) => (
                    <button
                      key={issue.issueId}
                      onClick={() => {
                        onClose()
                        onSelectIssue(issue)
                      }}
                      className="w-full flex items-center justify-between px-3 py-2 text-slate-300 hover:bg-slate-800/80 rounded transition text-left"
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className="text-cyan-400 font-bold">{issue.issueId}</span>
                        <span className="truncate max-w-[320px] text-slate-300 font-sans">
                          {issue.complaintText}
                        </span>
                      </div>
                      <span className="text-[10px] text-slate-400 shrink-0">{issue.location}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="px-4 py-2 bg-[#090c13] border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-500 font-mono">
              <span>Use &uarr; &darr; to navigate, Enter to select</span>
              <span className="text-cyan-500">CiviLens Command Engine v2.4</span>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default CommandPalette
