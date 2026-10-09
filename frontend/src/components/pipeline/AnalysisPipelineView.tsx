import React, { useState } from 'react'
import {
  Sparkles,
  Send,
  Eye,
  FileText,
  MapPin,
  Flame,
  RotateCcw,
  Building,
  CheckCircle2,
  ArrowRight,
  Layers,
  ShieldCheck,
  AlertTriangle,
} from 'lucide-react'
import { api } from '../../services/api'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { StatusBadge } from '../common/StatusBadge'
import { cn } from '../../lib/utils'

export const AnalysisPipelineView: React.FC<{
  onIssueCreated?: (issue: any) => void
}> = ({ onIssueCreated }) => {
  const [complaintText, setComplaintText] = useState(
    'Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk'
  )
  const [location, setLocation] = useState('Vidyavihar')
  const [imageUrl, setImageUrl] = useState('data/sample_pothole.jpg')
  const [loading, setLoading] = useState(false)
  const [activeStep, setActiveStep] = useState<number>(0)
  const [result, setResult] = useState<any | null>(null)
  const [commitLoading, setCommitLoading] = useState(false)
  const [committedIssue, setCommittedIssue] = useState<any | null>(null)

  const steps = [
    { title: '1. Text Analytics & Urgency Cues', desc: 'TF-IDF vectorizer + high-risk keyword extraction' },
    { title: '2. Spatial Resolution & Deduplication', desc: 'Haversine proximity search + duplicate clustering' },
    { title: '3. YOLOv8 Road Defect Detection', desc: 'Bounding box regression + visual severity scoring' },
    { title: '4. Text–Image Cross-Validation', desc: 'Multimodal semantic consistency alignment' },
    { title: '5. Spatiotemporal DBSCAN & Recurrence', desc: 'Historical cluster density + chronic failure check' },
    { title: '6. Dynamic Priority Engine (0–100)', desc: 'Explainable 6-factor composite risk index' },
    { title: '7. Department Dispatch Protocol', desc: 'Automated routing, SLA assignment, and action directive' },
  ]

  const runPipeline = async () => {
    setLoading(true)
    setResult(null)
    setCommittedIssue(null)
    setActiveStep(1)

    // Simulate stepping through stages for visual operational feedback
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev < 7 ? prev + 1 : prev))
    }, 250)

    try {
      const res = await api.analyzeComplaint({
        complaintText,
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      clearInterval(interval)
      setActiveStep(7)
      setResult(res)
    } catch (err) {
      clearInterval(interval)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCommitIssue = async () => {
    setCommitLoading(true)
    try {
      const created = await api.submitIssue({
        complaintText,
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      setCommittedIssue(created)
      if (onIssueCreated) onIssueCreated(created)
    } catch (err) {
      console.error(err)
    } finally {
      setCommitLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header Banner */}
      <div className="p-4 bg-[#101420] border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-lg">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              MULTIMODAL CIVIC INTELLIGENCE PIPELINE LAB
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Execute real-time end-to-end multimodal inference across all 20 civic intelligence features.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setComplaintText('Massive overflowing garbage dump on LBS Marg, rotten food waste and flies creating extreme stench')
              setLocation('LBS Marg, Ghatkopar West')
              setImageUrl('data/sample_garbage.jpg')
            }}
            className="px-2.5 py-1 bg-amber-950/40 hover:bg-amber-900/60 border border-amber-800 text-amber-300 rounded text-[11px]"
          >
            Scenario: Garbage
          </button>
          <button
            onClick={() => {
              setComplaintText('Major drinking water pipeline burst flooding 90 Feet Road Dharavi, millions of liters wasted')
              setLocation('Dharavi')
              setImageUrl('data/sample_water_leak.jpg')
            }}
            className="px-2.5 py-1 bg-sky-950/40 hover:bg-sky-900/60 border border-sky-800 text-sky-300 rounded text-[11px]"
          >
            Scenario: Water Leak
          </button>
        </div>
      </div>

      {/* Grid: Input panel vs Live Pipeline Flow */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Inputs */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-4 space-y-4 shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>Complaint Ingestion Vectors</span>
            <span className="text-cyan-400 text-[10px]">RAW SIGNALS</span>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 font-bold uppercase">
              Citizen Narrative (NLP Text)
            </label>
            <textarea
              rows={4}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700/80 rounded p-2.5 text-xs text-slate-100 font-sans outline-none focus:border-cyan-500 leading-relaxed"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 font-bold uppercase">
              Landmark / Reported Location
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700/80 rounded p-2 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] text-slate-400 font-bold uppercase">
              Evidence Image Path / URL
            </label>
            <input
              type="text"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700/80 rounded p-2 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500"
            />
          </div>

          <button
            onClick={runPipeline}
            disabled={loading}
            className="w-full py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg shadow-cyan-950/50 transition active:scale-[0.99] disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4" />
            <span>{loading ? 'Executing Pipeline Inference...' : 'Execute Multimodal Analysis'}</span>
          </button>
        </div>

        {/* Right: Stage-by-Stage Flow & Results */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-4 space-y-4 shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>Inference Pipeline Pipeline Progress</span>
            <span className="text-cyan-400 text-[10px]">
              {result ? 'COMPLETE (ALL 7 STAGES RESOLVED)' : 'READY'}
            </span>
          </div>

          {/* Stepper bar */}
          <div className="space-y-1.5">
            {steps.map((st, idx) => {
              const stepNum = idx + 1
              const isPast = activeStep > stepNum || result !== null
              const isCurrent = activeStep === stepNum && !result
              return (
                <div
                  key={st.title}
                  className={cn(
                    'p-2 rounded border flex items-center justify-between transition-all duration-300',
                    isPast
                      ? 'bg-emerald-950/20 border-emerald-900/60 text-emerald-300'
                      : isCurrent
                      ? 'bg-cyan-950/40 border-cyan-700 text-cyan-200 animate-pulse'
                      : 'bg-[#101420] border-slate-800 text-slate-500'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        'w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold border',
                        isPast
                          ? 'bg-emerald-900 border-emerald-700 text-white'
                          : isCurrent
                          ? 'bg-cyan-900 border-cyan-600 text-cyan-200'
                          : 'bg-slate-900 border-slate-800 text-slate-500'
                      )}
                    >
                      {isPast ? <CheckCircle2 className="w-3.5 h-3.5" /> : stepNum}
                    </span>
                    <div>
                      <div className="font-bold text-[11px]">{st.title}</div>
                      <div className="text-[9px] opacity-75 font-sans">{st.desc}</div>
                    </div>
                  </div>
                  <span className="text-[10px] uppercase font-bold">
                    {isPast ? 'PASSED' : isCurrent ? 'RUNNING' : 'PENDING'}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Structured Output Dashboard (If result generated) */}
      {result && (
        <div className="bg-[#0e131d] border border-cyan-900/60 rounded-xl p-5 space-y-4 shadow-2xl animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                STRUCTURED DECISION-SUPPORT INTELLIGENCE RESULT
              </span>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-lg font-bold text-slate-100">{result.category}</span>
                <ConsistencyBadge
                  level={result.consistencyFlag}
                  score={result.evidenceConsistency}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              {committedIssue ? (
                <div className="px-3 py-1.5 bg-emerald-950/80 border border-emerald-700 text-emerald-300 rounded font-bold text-xs flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Committed as {committedIssue.issueId}</span>
                </div>
              ) : (
                <button
                  onClick={handleCommitIssue}
                  disabled={commitLoading}
                  className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{commitLoading ? 'Committing...' : 'Commit to Central Database'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px]">URGENCY (NLP CUES)</div>
              <div className="text-base font-bold text-amber-400 mt-0.5">
                {(result.urgency * 100).toFixed(0)}%
              </div>
              <div className="text-[10px] text-slate-500 mt-1 truncate">
                Cues: {result.urgencyCues?.join(', ') || 'None'}
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px]">VISUAL SEVERITY (CV)</div>
              <div className="text-base font-bold text-cyan-400 mt-0.5">
                {(result.severity * 100).toFixed(0)}%
              </div>
              <div className="text-[10px] text-slate-500 mt-1 truncate">
                {result.visualDetection || 'No detections'}
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px]">LOCATION / WARD</div>
              <div className="text-sm font-bold text-slate-200 mt-0.5 truncate">
                {result.resolvedLocation}
              </div>
              <div className="text-[10px] text-slate-500 mt-1">
                {result.latitude}, {result.longitude} ({result.ward})
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px]">DISPATCH SLA</div>
              <div className="text-base font-bold text-emerald-400 mt-0.5">
                {result.slaHours} Hours
              </div>
              <div className="text-[10px] text-slate-500 mt-1 truncate">
                {result.departmentCode}
              </div>
            </div>
          </div>

          {/* Explainable Dynamic Priority (Feature 15) */}
          <div className="p-4 bg-[#111724] border border-slate-800 rounded-lg">
            <PriorityGauge
              score={result.priorityScore}
              level={result.priorityLevel}
              breakdown={result.priorityBreakdown}
              reasoning={result.priorityReasoning}
              showDetails={true}
            />
          </div>

          {/* Feature 19 Action Directive */}
          <div className="p-3.5 bg-[#121824] border border-slate-800 rounded-lg flex items-start gap-3">
            <Building className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-[10px] text-slate-400 uppercase font-bold">
                Automated Municipal Directive &rarr; {result.department}
              </div>
              <div className="text-slate-200 text-xs mt-1 font-sans">
                {result.recommendedAction}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
