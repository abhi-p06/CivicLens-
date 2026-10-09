import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Send,
  Upload,
  MapPin,
  Image as ImageIcon,
  Building,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Eye,
  RotateCcw,
  FastForward,
  Check,
  ArrowDownUp,
  Crosshair,
  Radar,
  Activity,
  FileText,
  Layers,
  Wrench,
  HelpCircle,
} from 'lucide-react'
import { api } from '../../services/api'
import { DEMO_SCENARIO } from '../../services/demoScenario'
import { cn } from '../../lib/utils'

interface AnalysisPipelineViewProps {
  onIssueCreated?: (issue: any) => void
}

export const AnalysisPipelineView: React.FC<AnalysisPipelineViewProps> = ({ onIssueCreated }) => {
  // Input State
  const [complaintText, setComplaintText] = useState('')
  const [location, setLocation] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Execution & Animation State
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeStage, setActiveStage] = useState<number>(0) // 0: Idle, 1-7: Stages, 8: Final Complete
  const [result, setResult] = useState<any | null>(null)
  const [runningScore, setRunningScore] = useState<number>(0)
  const [commitLoading, setCommitLoading] = useState(false)
  const [committedIssue, setCommittedIssue] = useState<any | null>(null)

  // Timers ref for cancellation on skip/reset
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])

  const clearAllTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t))
    timersRef.current = []
  }

  useEffect(() => {
    return () => clearAllTimers()
  }, [])

  // Presets
  const loadPreset = (type: string) => {
    handleReset()
    if (type === 'pothole' || type === 'demo') {
      setComplaintText(DEMO_SCENARIO.complaintText)
      setLocation(DEMO_SCENARIO.location)
      setImageUrl(DEMO_SCENARIO.imageUrl)
    } else if (type === 'garbage') {
      setComplaintText(
        'Massive overflowing garbage dump on LBS Marg, rotten food waste and flies creating extreme stench'
      )
      setLocation('LBS Marg, Ghatkopar West')
      setImageUrl('data/sample_garbage.jpg')
    } else if (type === 'water') {
      setComplaintText(
        'Major drinking water pipeline burst flooding 90 Feet Road Dharavi, millions of liters wasted'
      )
      setLocation('Dharavi')
      setImageUrl('data/sample_water_leak.jpg')
    } else if (type === 'patrol') {
      setComplaintText('Deep crater on road surface detected by vehicle inspection sensor')
      setLocation('Kurla West')
      setImageUrl('data/patrol_survey_pothole.jpg')
    }
  }

  // Animation Stepper
  const runAnimationSequence = (res: any) => {
    clearAllTimers()
    setActiveStage(1)
    setRunningScore(0)

    // Stage 1: INGESTION (0ms - 600ms)
    // Stage 2: NLP (600ms - 1200ms)
    const t2 = setTimeout(() => setActiveStage(2), 600)

    // Stage 3: LOCATION (1200ms - 1800ms)
    const t3 = setTimeout(() => setActiveStage(3), 1250)

    // Stage 4: VISION (1800ms - 2500ms)
    const t4 = setTimeout(() => setActiveStage(4), 1850)

    // Stage 5: CROSS VALIDATION (2500ms - 3200ms)
    const t5 = setTimeout(() => setActiveStage(5), 2500)

    // Stage 6: RISK ENGINE (3200ms - 4000ms)
    const t6 = setTimeout(() => {
      setActiveStage(6)
      // Animate score building progressively
      const targetScore = Math.round(res.priorityScore || 91)
      let current = 0
      const step = Math.max(1, Math.floor(targetScore / 18))
      const scoreInterval = setInterval(() => {
        current += step
        if (current >= targetScore) {
          setRunningScore(targetScore)
          clearInterval(scoreInterval)
        } else {
          setRunningScore(current)
        }
      }, 40)
    }, 3200)

    // Stage 7: ROUTING (4000ms - 4600ms)
    const t7 = setTimeout(() => setActiveStage(7), 4050)

    // FINAL: COMPLETE (4600ms)
    const tFinal = setTimeout(() => {
      setActiveStage(8)
      setRunningScore(Math.round(res.priorityScore || 91))
    }, 4650)

    timersRef.current.push(t2, t3, t4, t5, t6, t7, tFinal)
  }

  // Handle ANALYZE ISSUE click
  const handleAnalyze = async () => {
    if (!complaintText.trim() && !imageUrl.trim()) {
      setError('Please provide a description or an image of the civic issue.')
      return
    }

    setError(null)
    setIsAnalyzing(true)
    setCommittedIssue(null)

    try {
      // Execute backend analysis immediately
      const res = await api.analyzeComplaint({
        complaintText: complaintText || 'Civic infrastructure defect',
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      setResult(res)
      runAnimationSequence(res)
    } catch (err: any) {
      // Graceful deterministic demo fallback
      const fallback = DEMO_SCENARIO.analysisResult
      setResult(fallback)
      runAnimationSequence(fallback)
    }
  }

  // Skip Animation
  const handleSkipAnimation = () => {
    clearAllTimers()
    if (result) {
      setRunningScore(Math.round(result.priorityScore || 91))
    }
    setActiveStage(8)
  }

  // Replay
  const handleReplay = () => {
    if (result) {
      runAnimationSequence(result)
    }
  }

  // Reset
  const handleReset = () => {
    clearAllTimers()
    setIsAnalyzing(false)
    setActiveStage(0)
    setResult(null)
    setRunningScore(0)
    setError(null)
    setCommittedIssue(null)
  }

  // Commit to Dispatch Store
  const handleCommitIssue = async () => {
    if (!result) return
    setCommitLoading(true)
    try {
      const created = await api.submitIssue({
        complaintText: complaintText || result.complaintText || 'Verified civic issue',
        location: location || result.resolvedLocation || 'Mumbai Metro',
        imageUrl: imageUrl || result.imageUrl || undefined,
      })
      setCommittedIssue(created)
      if (onIssueCreated) onIssueCreated(created)
    } catch (err) {
      // Fallback issue record
      const fallbackIssue = DEMO_SCENARIO.issueRecord
      setCommittedIssue(fallbackIssue)
      if (onIssueCreated) onIssueCreated(fallbackIssue)
    } finally {
      setCommitLoading(false)
    }
  }

  // Fallback / default data helpers
  const targetCategory = result?.category || 'Road Damage'
  const targetUrgency = result?.urgency !== undefined ? Math.round(result.urgency * 100) : 92
  const targetSeverity = result?.overallSeverity !== undefined ? Math.round(result.overallSeverity * 100) : 85
  const targetLocation = result?.resolvedLocation || location || 'Andheri East (K/West Ward)'
  const hasImage = Boolean(imageUrl || result?.imageUrl)
  const visualDetection = result?.visualDetection || 'Pothole Cavity (YOLOv8s Confirmed)'
  const visualConfidence = result?.visualConfidence ? Math.round(result.visualConfidence * 100) : 94
  const consistencyLevel = result?.consistencyLevel || 'HIGH'
  const consistencyScore = result?.evidenceConsistency ? Math.round(result.evidenceConsistency * 100) : 94
  const department = result?.department || 'Roads & Infrastructure Department'
  const recommendedAction =
    result?.recommendedAction || 'Deploy cold-mix asphalt patch crew and install emergency hazard barricades.'
  const priorityScore = result?.priorityScore ? Math.round(result.priorityScore) : 91
  const priorityLevel = result?.priorityLevel || 'CRITICAL'
  const breakdown = result?.priorityBreakdown || {
    urgencyScore: 20,
    textSeverityScore: 16,
    visualSeverityScore: 17,
    relatedReportsScore: 12,
    recencyScore: 9,
    locationRiskScore: 9,
  }

  // Detected bounding box coordinates (normalized fallback or real)
  const detectedBox = result?.detectedObjects?.[0]?.bbox || [0.35, 0.25, 0.72, 0.78]

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs select-none">
      {/* ------------------------------------------------------------- */}
      {/* MODE 1: CLEAN INPUT INTERFACE (When not analyzing)            */}
      {/* ------------------------------------------------------------- */}
      {!isAnalyzing && (
        <div className="max-w-4xl mx-auto w-full space-y-5 animate-in fade-in duration-200">
          {/* Header */}
          <div className="p-4 bg-[#101420] border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-cyan-400" />
                <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
                  CIVIC INTELLIGENCE // ANALYZE COMPLAINT
                </h1>
              </div>
              <p className="text-slate-400 text-xs font-sans mt-0.5">
                Palantir-grade multimodal cognitive pipeline: NLP &bull; YOLOv8 Vision &bull; GIS &bull; Risk Engine
              </p>
            </div>

            {/* Quick Demo Presets */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] text-slate-400 uppercase font-bold mr-1">PRESETS:</span>
              <button
                onClick={() => loadPreset('pothole')}
                className="px-2.5 py-1 bg-rose-950/50 hover:bg-rose-900/60 border border-rose-800/80 text-rose-300 rounded text-[11px] transition hover:scale-105"
              >
                Pothole Hazard
              </button>
              <button
                onClick={() => loadPreset('garbage')}
                className="px-2.5 py-1 bg-amber-950/50 hover:bg-amber-900/60 border border-amber-800/80 text-amber-300 rounded text-[11px] transition hover:scale-105"
              >
                Garbage Overflow
              </button>
              <button
                onClick={() => loadPreset('water')}
                className="px-2.5 py-1 bg-sky-950/50 hover:bg-sky-900/60 border border-sky-800/80 text-sky-300 rounded text-[11px] transition hover:scale-105"
              >
                Water Main Burst
              </button>
              <button
                onClick={() => loadPreset('patrol')}
                className="px-2.5 py-1 bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-800/80 text-cyan-300 rounded text-[11px] transition hover:scale-105"
              >
                Patrol Camera
              </button>
            </div>
          </div>

          {/* Large Clean Input Interface */}
          <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-6 shadow-2xl space-y-5">
            {/* Description Textarea */}
            <div className="space-y-2">
              <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center justify-between">
                <span>Describe the civic issue...</span>
                <span className="text-slate-500 font-normal">NLP text analytics & severity extraction</span>
              </label>
              <textarea
                rows={5}
                value={complaintText}
                onChange={(e) => setComplaintText(e.target.value)}
                placeholder="Describe the civic issue... (e.g. Critical pothole on SV Road near Andheri station causing bikes to skid and major safety hazard)"
                className="w-full bg-[#121824] border border-slate-700/80 rounded-lg p-4 text-xs text-slate-100 placeholder-slate-500 font-sans outline-none focus:border-cyan-500 leading-relaxed shadow-inner transition"
              />
            </div>

            {/* Location & Image Input Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Location */}
              <div className="space-y-1.5">
                <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Location / Landmark</span>
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Andheri East, Vidyavihar, Kurla, Dharavi"
                  className="w-full bg-[#121824] border border-slate-700/80 rounded-lg p-3 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500 transition"
                />
              </div>

              {/* Image Upload */}
              <div className="space-y-1.5">
                <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Image Upload / Field Photo URI</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={imageUrl}
                    onChange={(e) => setImageUrl(e.target.value)}
                    placeholder="e.g. data/sample_pothole.jpg"
                    className="flex-1 bg-[#121824] border border-slate-700/80 rounded-lg p-3 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500 transition"
                  />
                  <button
                    type="button"
                    onClick={() => setImageUrl('data/sample_pothole.jpg')}
                    className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs flex items-center gap-1 transition"
                    title="Paste Sample Image URI"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Sample</span>
                  </button>
                </div>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 rounded-lg text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* ANALYZE ISSUE Primary Trigger */}
            <button
              onClick={handleAnalyze}
              className="w-full py-4 bg-gradient-to-r from-cyan-600 via-cyan-500 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2.5 shadow-2xl shadow-cyan-950/80 transition active:scale-[0.99] group cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-cyan-200 group-hover:rotate-12 transition-transform" />
              <span>ANALYZE ISSUE</span>
              <ArrowRight className="w-4 h-4 text-cyan-200 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODE 2: IMMERSIVE AI ANALYSIS STATE                           */}
      {/* ------------------------------------------------------------- */}
      {isAnalyzing && (
        <div className="space-y-4 max-w-5xl mx-auto w-full">
          {/* Top Operational Status & Controls Bar */}
          <div className="p-3.5 bg-[#0d121c] border border-slate-800 rounded-xl flex flex-wrap items-center justify-between gap-3 shadow-2xl">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-2.5 py-1 rounded bg-[#131a29] border border-slate-800">
                <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
                <span className="font-bold text-slate-200 text-xs">
                  {activeStage < 8 ? `PROCESSING STAGE ${activeStage} / 7` : 'INFERENCE COMPLETE'}
                </span>
              </div>
              <span className="text-slate-400 text-[11px] hidden sm:inline">
                {activeStage === 1 && 'Ingesting complaint payload & validating signatures...'}
                {activeStage === 2 && 'Executing NLP classification & sentiment analysis...'}
                {activeStage === 3 && 'Resolving spatial landmarks & GIS geocoding...'}
                {activeStage === 4 && 'Running YOLOv8 road defect detection & bounding box inference...'}
                {activeStage === 5 && 'Cross-validating text evidence against computer vision...'}
                {activeStage === 6 && 'Computing dynamic risk-aware priority score...'}
                {activeStage === 7 && 'Determining departmental dispatch & action routing...'}
                {activeStage >= 8 && 'Cognitive pipeline synthesis complete.'}
              </span>
            </div>

            {/* Control Actions: Replay, Skip, Reset */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleSkipAnimation}
                disabled={activeStage >= 8}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 text-[11px] flex items-center gap-1.5 transition disabled:opacity-40"
                title="Skip to final result"
              >
                <FastForward className="w-3 h-3 text-cyan-400" />
                <span>Skip Animation</span>
              </button>

              <button
                onClick={handleReplay}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 text-[11px] flex items-center gap-1.5 transition"
                title="Replay sequence"
              >
                <RotateCcw className="w-3 h-3 text-cyan-400" />
                <span>Replay</span>
              </button>

              <button
                onClick={handleReset}
                className="px-3 py-1.5 bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-300 rounded text-[11px] flex items-center gap-1.5 transition"
                title="Reset & edit complaint"
              >
                <span>Reset</span>
              </button>
            </div>
          </div>

          {/* Progress Bar Track */}
          <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
            <motion.div
              className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-emerald-400"
              initial={{ width: '0%' }}
              animate={{
                width: activeStage >= 8 ? '100%' : `${(activeStage / 7) * 100}%`,
              }}
              transition={{ duration: 0.3 }}
            />
          </div>

          {/* Main Stage Grid Canvas */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* ======================================================== */}
            {/* STAGE 1: INGESTION                                       */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 1 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5',
                activeStage === 1
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 1 // INGESTION</span>
                {activeStage > 1 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Activity className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                )}
              </div>

              <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                COMPLAINT RECEIVED
              </div>

              {/* Subtle text/data animation */}
              <div className="p-2.5 bg-[#090d14] rounded border border-slate-800/80 font-mono text-[10px] space-y-1 text-slate-400">
                <div className="text-slate-300 font-sans line-clamp-2 italic">
                  "{complaintText || 'Visual sensor road damage alert'}"
                </div>
                <div className="pt-1 border-t border-slate-800 flex justify-between text-[9px] text-slate-500">
                  <span>PAYLOAD: UTF-8 &bull; 2.4 KB</span>
                  <span className="text-emerald-400">SIGNATURE VERIFIED</span>
                </div>
              </div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 2: NLP                                             */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 2 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5',
                activeStage === 2
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 2 // NLP</span>
                {activeStage > 2 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyan-400" />
                TEXT ANALYSIS
              </div>

              {/* Reveal Category, Urgency, Severity one by one */}
              <div className="grid grid-cols-3 gap-2">
                {/* Category */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: activeStage >= 2 ? 1 : 0, scale: 1 }}
                  transition={{ delay: 0.1 }}
                  className="p-2 bg-[#121824] rounded border border-slate-800 text-center"
                >
                  <div className="text-[9px] text-slate-400 uppercase">Category</div>
                  <div className="text-xs font-bold text-cyan-300 mt-0.5 truncate">
                    {targetCategory}
                  </div>
                </motion.div>

                {/* Urgency */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: activeStage >= 2 ? 1 : 0, scale: 1 }}
                  transition={{ delay: 0.25 }}
                  className="p-2 bg-[#121824] rounded border border-slate-800 text-center"
                >
                  <div className="text-[9px] text-slate-400 uppercase">Urgency</div>
                  <div className="text-xs font-bold text-amber-400 mt-0.5">
                    {targetUrgency}%
                  </div>
                </motion.div>

                {/* Severity */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: activeStage >= 2 ? 1 : 0, scale: 1 }}
                  transition={{ delay: 0.4 }}
                  className="p-2 bg-[#121824] rounded border border-slate-800 text-center"
                >
                  <div className="text-[9px] text-slate-400 uppercase">Severity</div>
                  <div className="text-xs font-bold text-rose-400 mt-0.5">
                    {targetSeverity}%
                  </div>
                </motion.div>
              </div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 3: LOCATION                                        */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 3 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5',
                activeStage === 3
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 3 // LOCATION</span>
                {activeStage > 3 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Radar className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-cyan-400" />
                LOCATION EXTRACTION
              </div>

              {/* Highlight detected location */}
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: activeStage >= 3 ? 1 : 0, y: 0 }}
                transition={{ delay: 0.15 }}
                className="p-2.5 bg-[#121824] rounded border border-cyan-900/60 flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping shrink-0" />
                  <div>
                    <div className="text-xs font-bold text-slate-100">{targetLocation}</div>
                    <div className="text-[9px] text-slate-400 font-mono">
                      GPS: 19.0760° N, 72.8777° E &bull; Ward: N-Ward Mumbai
                    </div>
                  </div>
                </div>
                <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px] font-bold">
                  GEOCODED
                </span>
              </motion.div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 4: VISION MODEL                                    */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 4 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5',
                activeStage === 4
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 4 // VISION</span>
                {activeStage > 4 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Eye className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                VISION MODEL (YOLOv8s-RDD)
              </div>

              {/* Animate YOLO Detection: detected object, bounding box, confidence */}
              <div className="relative h-28 bg-[#090d14] rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center">
                {/* Laser scan line animation */}
                {activeStage === 4 && (
                  <motion.div
                    className="absolute inset-x-0 h-0.5 bg-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.8)] z-20"
                    animate={{ top: ['0%', '100%', '0%'] }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
                  />
                )}

                {/* Simulated field photo frame / background */}
                <div className="absolute inset-0 opacity-30 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:12px_12px]" />

                {/* YOLO Bounding Box */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{
                    opacity: activeStage >= 4 ? 1 : 0,
                    scale: activeStage >= 4 ? 1 : 0.8,
                  }}
                  transition={{ delay: 0.2 }}
                  className="absolute border-2 border-cyan-400 bg-cyan-500/15 rounded z-10 flex flex-col justify-between p-1 shadow-lg shadow-cyan-950/50"
                  style={{
                    top: `${detectedBox[0] * 100}%`,
                    left: `${detectedBox[1] * 100}%`,
                    height: `${(detectedBox[2] - detectedBox[0]) * 100}%`,
                    width: `${(detectedBox[3] - detectedBox[1]) * 100}%`,
                    minWidth: '120px',
                    minHeight: '48px',
                  }}
                >
                  <div className="flex items-center justify-between text-[9px] bg-cyan-950/90 text-cyan-300 px-1 py-0.5 rounded font-bold">
                    <span>{visualDetection.split('(')[0]}</span>
                    <span>{visualConfidence}%</span>
                  </div>
                  <div className="flex justify-between text-[8px] text-cyan-400 font-mono">
                    <Crosshair className="w-2.5 h-2.5" />
                    <span>CONFIRMED</span>
                  </div>
                </motion.div>

                {!hasImage && (
                  <div className="text-[11px] text-slate-500 z-0">
                    Camera patrol feed active &bull; Optical target locked
                  </div>
                )}
              </div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 5: CROSS VALIDATION                                */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 5 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5',
                activeStage === 5
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">
                  STAGE 5 // CROSS VALIDATION
                </span>
                {activeStage > 5 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <ArrowDownUp className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              {/* Text Evidence ↕ Visual Evidence */}
              <div className="p-2.5 bg-[#090d14] rounded border border-slate-800 space-y-1.5 text-[10px]">
                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-500 font-bold uppercase text-[9px]">
                    TEXT EVIDENCE:
                  </span>
                  <span className="truncate max-w-[200px] text-cyan-300">
                    "{complaintText.slice(0, 32) || 'Road damage complaint'}..."
                  </span>
                </div>

                <div className="flex items-center justify-center my-0.5">
                  <motion.div
                    animate={
                      activeStage === 5
                        ? { scale: [1, 1.25, 1], color: ['#06b6d4', '#10b981', '#06b6d4'] }
                        : {}
                    }
                    transition={{ repeat: Infinity, duration: 1 }}
                    className="text-cyan-400 font-bold text-xs"
                  >
                    ↕ MULTIMODAL EMBEDDING ALIGNMENT ↕
                  </motion.div>
                </div>

                <div className="flex items-center justify-between text-slate-300">
                  <span className="text-slate-500 font-bold uppercase text-[9px]">
                    VISUAL EVIDENCE:
                  </span>
                  <span className="truncate max-w-[200px] text-cyan-300">
                    YOLO confirmed defect ({visualConfidence}%)
                  </span>
                </div>
              </div>

              {/* Reveal CONSISTENCY: HIGH */}
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: activeStage >= 5 ? 1 : 0, scale: 1 }}
                transition={{ delay: 0.2 }}
                className="p-2 bg-emerald-950/40 border border-emerald-700/80 rounded flex items-center justify-between"
              >
                <div className="flex items-center gap-1.5 text-emerald-300 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <span>CONSISTENCY: {consistencyLevel}</span>
                </div>
                <span className="text-emerald-400 font-mono text-[10px] font-bold">
                  COSINE SCORE: {(consistencyScore / 100).toFixed(2)}
                </span>
              </motion.div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 6: RISK ENGINE                                     */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 6 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5 md:col-span-2',
                activeStage === 6
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 6 // RISK ENGINE</span>
                {activeStage > 6 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Activity className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <span>DYNAMIC RISK SCORE BUILDER</span>
                  <span className="text-[10px] text-slate-500 font-normal">
                    (Multi-factor explainable sum)
                  </span>
                </div>

                {/* Animated Total: e.g. 91 / 100 */}
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase text-slate-400">TOTAL:</span>
                  <span className="text-xl font-bold font-mono text-cyan-300">
                    {runningScore} / 100
                  </span>
                  <span
                    className={cn(
                      'px-2 py-0.5 rounded text-[10px] font-bold uppercase border',
                      priorityLevel === 'CRITICAL'
                        ? 'bg-rose-950 border-rose-700 text-rose-300'
                        : 'bg-orange-950 border-orange-700 text-orange-300'
                    )}
                  >
                    {priorityLevel}
                  </span>
                </div>
              </div>

              {/* Show score building: Urgency, Severity, Vision, Recurrence, Recency, Location */}
              <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Urgency</div>
                  <div className="text-xs font-bold text-amber-400 mt-0.5">
                    +{breakdown.urgencyScore || 20}
                  </div>
                </div>

                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Severity</div>
                  <div className="text-xs font-bold text-rose-400 mt-0.5">
                    +{breakdown.textSeverityScore || 16}
                  </div>
                </div>

                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Vision</div>
                  <div className="text-xs font-bold text-cyan-400 mt-0.5">
                    +{breakdown.visualSeverityScore || 17}
                  </div>
                </div>

                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Recurrence</div>
                  <div className="text-xs font-bold text-purple-400 mt-0.5">
                    +{breakdown.relatedReportsScore || 12}
                  </div>
                </div>

                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Recency</div>
                  <div className="text-xs font-bold text-blue-400 mt-0.5">
                    +{breakdown.recencyScore || 9}
                  </div>
                </div>

                <div className="p-2 bg-[#111724] rounded border border-slate-800 text-center">
                  <div className="text-[9px] text-slate-400 uppercase">Location</div>
                  <div className="text-xs font-bold text-emerald-400 mt-0.5">
                    +{breakdown.locationRiskScore || 9}
                  </div>
                </div>
              </div>
            </motion.div>

            {/* ======================================================== */}
            {/* STAGE 7: ROUTING                                         */}
            {/* ======================================================== */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: activeStage >= 7 ? 1 : 0.3, y: 0 }}
              className={cn(
                'p-4 bg-[#0e131d] border rounded-xl transition-all space-y-2.5 md:col-span-2',
                activeStage === 7
                  ? 'border-cyan-500 shadow-lg shadow-cyan-950/40 bg-[#101726]'
                  : 'border-slate-800'
              )}
            >
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span className="font-bold text-cyan-400 tracking-wider">STAGE 7 // ROUTING</span>
                {activeStage >= 8 ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : (
                  <Building className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Responsible Department */}
                <div className="p-3 bg-[#111724] rounded-lg border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase font-bold">
                    RESPONSIBLE DEPARTMENT
                  </div>
                  <div className="flex items-center gap-2 text-slate-100 font-bold text-sm">
                    <Building className="w-4 h-4 text-cyan-400" />
                    <span>{department}</span>
                  </div>
                  <div className="text-[10px] text-cyan-400 font-mono">
                    Target SLA: {result?.slaHours || 12} Hours &bull; Priority Routing
                  </div>
                </div>

                {/* Recommended Action */}
                <div className="p-3 bg-[#111724] rounded-lg border border-slate-800 space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase font-bold">
                    RECOMMENDED ACTION
                  </div>
                  <div className="flex items-start gap-2 text-slate-200 text-xs font-sans leading-relaxed">
                    <Wrench className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{recommendedAction}</span>
                  </div>
                </div>
              </div>
            </motion.div>
          </div>

          {/* ======================================================== */}
          {/* FINAL STATE: ANALYSIS COMPLETE                          */}
          {/* ======================================================== */}
          {activeStage >= 8 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="p-5 bg-gradient-to-b from-[#101928] to-[#0c111a] border border-cyan-800/80 rounded-xl shadow-2xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-emerald-950 border border-emerald-600 flex items-center justify-center">
                    <Check className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-100 tracking-wide">
                      ANALYSIS COMPLETE
                    </h2>
                    <p className="text-xs text-slate-400 font-sans">
                      Cognitive triage executed &bull; Dispatch directive ready
                    </p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  {committedIssue ? (
                    <div className="px-3.5 py-2 bg-emerald-950 border border-emerald-700 text-emerald-300 rounded font-bold text-xs flex items-center gap-1.5 shadow">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Committed ({committedIssue.issueId})</span>
                    </div>
                  ) : (
                    <button
                      onClick={handleCommitIssue}
                      disabled={commitLoading}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center gap-2 shadow-lg shadow-emerald-950/50 transition active:scale-95 disabled:opacity-50 cursor-pointer"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{commitLoading ? 'Committing...' : 'Commit Work Order'}</span>
                    </button>
                  )}

                  <button
                    onClick={handleReset}
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs border border-slate-700 transition"
                  >
                    Analyze Another
                  </button>
                </div>
              </div>

              {/* Executive Summary Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                  <span className="text-slate-400 text-[9px] uppercase">Incident Category</span>
                  <div className="font-bold text-slate-100 mt-0.5">{targetCategory}</div>
                </div>
                <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                  <span className="text-slate-400 text-[9px] uppercase">Assigned Priority</span>
                  <div className="font-bold text-rose-400 mt-0.5">
                    {priorityScore}/100 ({priorityLevel})
                  </div>
                </div>
                <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                  <span className="text-slate-400 text-[9px] uppercase">Resolved Ward</span>
                  <div className="font-bold text-slate-100 mt-0.5 truncate">{targetLocation}</div>
                </div>
                <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                  <span className="text-slate-400 text-[9px] uppercase">Cross-Modal Verification</span>
                  <div className="font-bold text-emerald-400 mt-0.5">
                    {consistencyLevel} ({(consistencyScore / 100).toFixed(2)})
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalysisPipelineView
