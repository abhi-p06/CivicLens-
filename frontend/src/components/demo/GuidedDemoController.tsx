import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Play,
  ArrowRight,
  ArrowLeft,
  RotateCcw,
  X,
  Sparkles,
  MapPin,
  FileText,
  CheckCircle2,
  Sliders,
  ShieldAlert,
} from 'lucide-react'
import { cn } from '../../lib/utils'

export interface GuidedDemoControllerProps {
  activeDemoStep: number // 1 to 6
  onSetDemoStep: (step: number) => void
  onExitDemo: () => void
  onResetDemo: () => void
}

export const DEMO_STEPS = [
  {
    step: 1,
    title: 'Command Center',
    viewId: 'overview',
    instruction: 'Review high-priority intake feed & KPI alerts. Click "ANALYZE CIVIC ISSUE" to begin.',
    actionLabel: 'Analyze Civic Issue',
    icon: Sparkles,
  },
  {
    step: 2,
    title: 'Complaint Analysis Pipeline',
    viewId: 'analyze',
    instruction: 'Ingesting complaint: "Large pothole near school gate..." Running 10-stage AI pipeline.',
    actionLabel: 'View Synthesized Results',
    icon: Sliders,
  },
  {
    step: 3,
    title: 'Cognitive Results & Advisory',
    viewId: 'analyze',
    instruction: 'Review Priority (91/100), YOLO Confidence (94%), Consistency (HIGH), and Roads Dept routing.',
    actionLabel: 'Inspect on Tactical Map',
    icon: FileText,
  },
  {
    step: 4,
    title: 'Tactical GIS Map',
    viewId: 'map',
    instruction: 'Flying to Somaiya Vidyavihar. Visualizing detected incident, nearby reports & DBSCAN hotspot.',
    actionLabel: 'Open Intelligence Dossier',
    icon: MapPin,
  },
  {
    step: 5,
    title: 'Issue Intelligence Dossier',
    viewId: 'intelligence',
    instruction: 'Examining multimodal evidence: YOLO bounding box, 0-100 score breakdown & lifecycle timeline.',
    actionLabel: 'Verify Field Resolution',
    icon: ShieldAlert,
  },
  {
    step: 6,
    title: 'Resolution Verification',
    viewId: 'resolution',
    instruction: 'Before/After field comparison: Cold-mix patch verified. Outcome: LIKELY RESOLVED.',
    actionLabel: 'Complete Presentation Demo',
    icon: CheckCircle2,
  },
]

export const GuidedDemoController: React.FC<GuidedDemoControllerProps> = ({
  activeDemoStep,
  onSetDemoStep,
  onExitDemo,
  onResetDemo,
}) => {
  const current = DEMO_STEPS.find((s) => s.step === activeDemoStep) || DEMO_STEPS[0]
  const isFirst = activeDemoStep <= 1
  const isLast = activeDemoStep >= 6

  // Keyboard navigation for demo presenter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in input/textarea
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea') return

      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault()
        if (!isLast) onSetDemoStep(activeDemoStep + 1)
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault()
        if (!isFirst) onSetDemoStep(activeDemoStep - 1)
      } else if (e.key === 'Escape') {
        onExitDemo()
      } else if (e.altKey && e.key.toLowerCase() === 'r') {
        e.preventDefault()
        onResetDemo()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeDemoStep, isFirst, isLast, onSetDemoStep, onExitDemo, onResetDemo])

  return (
    <div className="fixed bottom-3 inset-x-4 max-w-4xl mx-auto z-50 pointer-events-auto font-mono text-xs select-none">
      <motion.div
        initial={{ y: 25, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 25, opacity: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        className="bg-[#0b101b]/95 backdrop-blur-xl border border-cyan-800/80 rounded-xl p-3 shadow-2xl shadow-cyan-950/60 flex flex-col gap-2.5"
      >
        {/* Top Stepper Track */}
        <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2">
          <div className="flex items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
            </span>
            <span className="text-cyan-300 font-bold uppercase tracking-wider text-[11px]">
              PRESENTATION DEMO MODE
            </span>
            <span className="text-slate-500 text-[10px] hidden sm:inline">
              (Alt+D to toggle &bull; Alt+R to reset)
            </span>
          </div>

          {/* Stepper Pills */}
          <div className="flex items-center gap-1.5">
            {DEMO_STEPS.map((s) => {
              const isCurrent = s.step === activeDemoStep
              const isDone = s.step < activeDemoStep
              return (
                <button
                  key={s.step}
                  onClick={() => onSetDemoStep(s.step)}
                  className={cn(
                    'px-2 py-0.5 rounded text-[10px] font-bold transition flex items-center gap-1',
                    isCurrent
                      ? 'bg-cyan-600 text-white shadow-md shadow-cyan-950/50'
                      : isDone
                      ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                      : 'bg-[#121824] text-slate-400 hover:text-slate-200 border border-slate-800'
                  )}
                  title={s.title}
                >
                  <span>{s.step}</span>
                  <span className="hidden md:inline">{s.title.split(' ')[0]}</span>
                </button>
              )
            })}
          </div>

          {/* Close Demo Mode */}
          <button
            onClick={onExitDemo}
            className="text-slate-400 hover:text-slate-200 p-1 hover:bg-slate-800 rounded transition"
            title="Exit Demo Mode (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Bottom Action Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          {/* Current Step Instruction */}
          <div className="space-y-0.5">
            <div className="text-slate-200 font-bold text-xs flex items-center gap-2">
              <span className="text-cyan-400">SCREEN {activeDemoStep}:</span>
              <span>{current.title}</span>
            </div>
            <p className="text-slate-400 font-sans text-[11px] leading-relaxed line-clamp-1">
              {current.instruction}
            </p>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={() => onSetDemoStep(activeDemoStep - 1)}
              disabled={isFirst}
              className="px-2.5 py-1.5 bg-[#121824] hover:bg-[#182030] text-slate-300 disabled:opacity-30 rounded border border-slate-700 transition flex items-center gap-1 text-[11px]"
              title="Previous Step (Left Arrow)"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Prev</span>
            </button>

            <button
              onClick={onResetDemo}
              className="px-2.5 py-1.5 bg-[#121824] hover:bg-[#182030] text-slate-300 rounded border border-slate-700 transition flex items-center gap-1 text-[11px]"
              title="Reset Demo Data (Alt+R)"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span>Reset</span>
            </button>

            <button
              onClick={() => {
                if (isLast) {
                  onExitDemo()
                } else {
                  onSetDemoStep(activeDemoStep + 1)
                }
              }}
              className="px-3.5 py-1.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow-lg shadow-cyan-950/50 transition active:scale-95"
            >
              <span>{current.actionLabel}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default GuidedDemoController
