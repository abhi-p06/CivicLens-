import React, { useEffect, useState } from 'react'
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
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { cn } from '../../lib/utils'

export interface GuidedDemoControllerProps {
  activeDemoStep: number // 1 to 5
  onSetDemoStep: (step: number) => void
  onExitDemo: () => void
  onResetDemo: () => void
}

export const DEMO_STEPS = [
  {
    step: 1,
    title: 'Pothole & Road Damage Intake',
    viewId: 'analyze',
    preset: 'pothole',
    instruction: 'Submit pothole complaint with image. Genuine YOLOv8s RDD2022 inference, Priority scoring, and Roads Dept routing.',
    actionLabel: 'Next: Submit Garbage Complaint',
    icon: Sparkles,
  },
  {
    step: 2,
    title: 'Garbage & Street Litter Intake',
    viewId: 'analyze',
    preset: 'garbage',
    instruction: 'Submit municipal waste complaint with image. Genuine YOLO11s TACO inference, SWM routing, transparent uncertainty disclosure.',
    actionLabel: 'Next: Test Cross-Validation Mismatch',
    icon: Sliders,
  },
  {
    step: 3,
    title: 'Cross-Category Mismatch Validation',
    viewId: 'analyze',
    preset: 'mismatch',
    instruction: 'Test road complaint paired with garbage image. Waste detector assists cross-check; flagged INCONSISTENT for supervisory triage.',
    actionLabel: 'Next: Compare Priority Scores & GIS',
    icon: ShieldAlert,
  },
  {
    step: 4,
    title: 'Tactical GIS & Dual-Category Priorities',
    viewId: 'map',
    preset: undefined,
    instruction: 'Spatial visualization across Mumbai wards. Compare 6-factor priority scores, Haversine DBSCAN hotspots, and department routing.',
    actionLabel: 'Next: Verify Pothole Repair',
    icon: MapPin,
  },
  {
    step: 5,
    title: 'Pothole Before & After Repair Verification',
    viewId: 'resolution',
    preset: 'resolution',
    instruction: 'Lifecycle verification: Compare pothole before-and-after repair images using OpenCV SSIM & YOLO defect clearance (LIKELY RESOLVED).',
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
  const [isCollapsed, setIsCollapsed] = useState(false)
  const current = DEMO_STEPS.find((s) => s.step === activeDemoStep) || DEMO_STEPS[0]
  const isFirst = activeDemoStep <= 1
  const isLast = activeDemoStep >= DEMO_STEPS.length

  // Keyboard navigation for demo presenter
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
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
      } else if (e.altKey && e.key.toLowerCase() === 'm') {
        e.preventDefault()
        setIsCollapsed((prev) => !prev)
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [activeDemoStep, isFirst, isLast, onSetDemoStep, onExitDemo, onResetDemo])

  return (
    <div className="fixed bottom-4 right-6 z-40 select-none font-sans pointer-events-auto">
      {/* 1. Collapsed Pill Mode */}
      {isCollapsed ? (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 20, opacity: 0 }}
          transition={{ duration: 0.18 }}
          onClick={() => setIsCollapsed(false)}
          className="bg-[#0e121b]/95 backdrop-blur-md border border-cyan-500/30 hover:border-cyan-500/50 rounded-full px-4 py-2 shadow-2xl flex items-center gap-3 cursor-pointer text-xs"
        >
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
          </span>
          <span className="font-semibold text-white">
            Demo {activeDemoStep}/6: {current.title}
          </span>
          <span className="text-[11px] text-cyan-400 font-medium hidden sm:inline">
            (Click to expand)
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onExitDemo()
            }}
            className="text-slate-400 hover:text-white p-0.5 rounded transition"
            title="Exit Demo"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </motion.div>
      ) : (
        /* 2. Expanded Controller Mode (Safely Anchored to Right, Never Overlapping Sidebar) */
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 20, opacity: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="bg-[#0e121b]/95 backdrop-blur-xl border border-white/[0.12] rounded-2xl p-4 shadow-2xl max-w-xl w-full flex flex-col gap-3"
        >
          {/* Top Header & Stepper Track */}
          <div className="flex items-center justify-between gap-3 border-b border-white/[0.08] pb-2.5">
            <div className="flex items-center gap-2">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
              </span>
              <span className="text-xs font-semibold text-white tracking-tight">
                Presentation Demo Mode
              </span>
              <span className="text-slate-500 text-[11px] hidden sm:inline">
                (Alt+D &bull; Alt+R)
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
                      'px-2 py-0.5 rounded-md text-[11px] font-semibold transition flex items-center gap-1 cursor-pointer',
                      isCurrent
                        ? 'bg-cyan-500 text-slate-950 shadow-sm'
                        : isDone
                        ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                        : 'bg-white/[0.04] text-slate-400 hover:text-slate-200 border border-white/[0.06]'
                    )}
                    title={s.title}
                  >
                    <span>{s.step}</span>
                  </button>
                )
              })}
            </div>

            {/* Collapse & Close */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsCollapsed(true)}
                className="text-slate-400 hover:text-slate-200 p-1 hover:bg-white/[0.06] rounded-md transition cursor-pointer"
                title="Minimize (Alt+M)"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
              <button
                onClick={onExitDemo}
                className="text-slate-400 hover:text-slate-200 p-1 hover:bg-white/[0.06] rounded-md transition cursor-pointer"
                title="Exit Demo Mode (Esc)"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Bottom Action Row */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-0.5">
            {/* Current Step Instruction */}
            <div className="space-y-0.5 min-w-0 pr-2">
              <div className="text-slate-200 font-semibold text-xs flex items-center gap-2">
                <span className="text-cyan-400 font-mono">Step {activeDemoStep}:</span>
                <span className="truncate">{current.title}</span>
              </div>
              <p className="text-slate-400 text-xs leading-relaxed line-clamp-1">
                {current.instruction}
              </p>
            </div>

            {/* Navigation Controls */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => onSetDemoStep(activeDemoStep - 1)}
                disabled={isFirst}
                className="px-2.5 py-1.5 bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 disabled:opacity-30 rounded-lg border border-white/[0.08] transition flex items-center gap-1 text-xs font-medium cursor-pointer"
                title="Previous Step"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Prev</span>
              </button>

              <button
                onClick={onResetDemo}
                className="px-2.5 py-1.5 bg-white/[0.04] hover:bg-white/[0.08] text-slate-300 rounded-lg border border-white/[0.08] transition flex items-center gap-1 text-xs font-medium cursor-pointer"
                title="Reset Demo (Alt+R)"
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
                className="px-3.5 py-1.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg font-semibold text-xs flex items-center gap-1.5 shadow-sm transition cursor-pointer"
              >
                <span>{current.actionLabel}</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-950" />
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default GuidedDemoController
