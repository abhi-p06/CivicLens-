import React, { useState } from 'react'
import {
  Sparkles,
  Send,
  Upload,
  MapPin,
  Image as ImageIcon,
  Building,
  CheckCircle2,
  Clock,
  Layers,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Eye,
} from 'lucide-react'
import { api } from '../../services/api'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { cn } from '../../lib/utils'

export const AnalysisPipelineView: React.FC<{
  onIssueCreated?: (issue: any) => void
}> = ({ onIssueCreated }) => {
  const [complaintText, setComplaintText] = useState('')
  const [location, setLocation] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [currentPipelineStep, setCurrentPipelineStep] = useState<number>(-1)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [commitLoading, setCommitLoading] = useState(false)
  const [committedIssue, setCommittedIssue] = useState<any | null>(null)

  const pipelineStages = [
    'INGESTING',
    'NLP ANALYSIS',
    'LOCATION EXTRACTION',
    'DUPLICATE CHECK',
    'VISION ANALYSIS',
    'CROSS VALIDATION',
    'HOTSPOT CHECK',
    'RISK CALCULATION',
    'DEPARTMENT ROUTING',
    'COMPLETE',
  ]

  const loadPreset = (type: string) => {
    setError(null)
    setResult(null)
    setCommittedIssue(null)
    setCurrentPipelineStep(-1)

    if (type === 'pothole') {
      setComplaintText(
        'Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk'
      )
      setLocation('Vidyavihar')
      setImageUrl('data/sample_pothole.jpg')
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
      setComplaintText('')
      setLocation('Kurla West')
      setImageUrl('data/patrol_survey_pothole.jpg')
    }
  }

  const handleAnalyze = async () => {
    if (!complaintText.trim() && !imageUrl.trim()) {
      setError('Please provide a description or an image of the civic issue.')
      return
    }

    setError(null)
    setResult(null)
    setCommittedIssue(null)
    setLoading(true)

    // Execute animated stepping through all 10 stages
    for (let i = 0; i < pipelineStages.length; i++) {
      setCurrentPipelineStep(i)
      await new Promise((r) => setTimeout(r, 180))
    }

    try {
      const res = await api.analyzeComplaint({
        complaintText,
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Pipeline analysis encountered an error.')
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
      {/* Page Header */}
      <div className="p-4 bg-[#101420] border border-slate-800 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
              MAIN DEMO // ANALYZE CIVIC COMPLAINT
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-0.5">
            Ingest raw civic text, imagery, and landmarks through the multimodal pipeline.
          </p>
        </div>

        {/* Quick Demo Presets */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] text-slate-400 uppercase font-bold mr-1">PRESETS:</span>
          <button
            onClick={() => loadPreset('pothole')}
            className="px-2.5 py-1 bg-rose-950/50 hover:bg-rose-900/60 border border-rose-800/80 text-rose-300 rounded text-[11px] transition"
          >
            Pothole Accident
          </button>
          <button
            onClick={() => loadPreset('garbage')}
            className="px-2.5 py-1 bg-amber-950/50 hover:bg-amber-900/60 border border-amber-800/80 text-amber-300 rounded text-[11px] transition"
          >
            Garbage Overflow
          </button>
          <button
            onClick={() => loadPreset('water')}
            className="px-2.5 py-1 bg-sky-950/50 hover:bg-sky-900/60 border border-sky-800/80 text-sky-300 rounded text-[11px] transition"
          >
            Water Main Burst
          </button>
          <button
            onClick={() => loadPreset('patrol')}
            className="px-2.5 py-1 bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-800/80 text-cyan-300 rounded text-[11px] transition"
          >
            Patrol Survey
          </button>
        </div>
      </div>

      {/* Large Clean Input Interface */}
      <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-5 shadow-2xl space-y-4">
        <div className="space-y-1.5">
          <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center justify-between">
            <span>Describe the civic issue...</span>
            <span className="text-slate-500 font-normal">NLP text analytics & severity extraction</span>
          </label>
          <textarea
            rows={4}
            value={complaintText}
            onChange={(e) => setComplaintText(e.target.value)}
            placeholder="Describe the civic issue... (e.g., Deep crater on Somaiya Vidyavihar campus road, severe accident hazard)"
            className="w-full bg-[#121824] border border-slate-700/80 rounded-lg p-3.5 text-xs text-slate-100 placeholder-slate-500 font-sans outline-none focus:border-cyan-500 leading-relaxed shadow-inner"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Location */}
          <div className="space-y-1">
            <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-cyan-400" />
              <span>Location / Landmark</span>
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Vidyavihar, LBS Marg, Dharavi, Andheri East"
              className="w-full bg-[#121824] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500"
            />
          </div>

          {/* Image Upload / URL */}
          <div className="space-y-1">
            <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
              <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
              <span>Image Upload / File URI</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="e.g. data/sample_pothole.jpg"
                className="flex-1 bg-[#121824] border border-slate-700/80 rounded-lg p-2.5 text-xs text-slate-100 font-mono outline-none focus:border-cyan-500"
              />
              <button
                type="button"
                onClick={() => setImageUrl('data/sample_pothole.jpg')}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg text-xs"
                title="Paste Sample Image"
              >
                <Upload className="w-3.5 h-3.5" />
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

        {/* ANALYZE ISSUE Button */}
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-xl shadow-cyan-950/50 transition active:scale-[0.99] disabled:opacity-50"
        >
          <Sparkles className="w-4 h-4" />
          <span>{loading ? 'PROCESSING INFERENCE...' : 'ANALYZE ISSUE'}</span>
        </button>
      </div>

      {/* Animated Pipeline Sequence */}
      {(loading || currentPipelineStep >= 0) && (
        <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>Inference Pipeline Execution</span>
            <span className="text-cyan-400 text-[10px]">
              STAGE {Math.min(currentPipelineStep + 1, 10)} OF 10
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {pipelineStages.map((stage, idx) => {
              const isPast = currentPipelineStep > idx || result !== null
              const isCurrent = currentPipelineStep === idx && !result
              return (
                <div
                  key={stage}
                  className={cn(
                    'p-2 rounded-lg border text-center transition-all duration-200',
                    isPast
                      ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300 font-bold'
                      : isCurrent
                      ? 'bg-cyan-950/70 border-cyan-500 text-cyan-200 font-bold animate-pulse shadow-lg shadow-cyan-950/50'
                      : 'bg-[#111724] border-slate-800 text-slate-500'
                  )}
                >
                  <div className="text-[9px] opacity-70">STEP 0{idx + 1}</div>
                  <div className="text-[10px] mt-0.5 truncate">{stage}</div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Structured Output Intelligence Results */}
      {result && (
        <div className="bg-[#0e131d] border border-cyan-900/60 rounded-xl p-5 space-y-5 shadow-2xl animate-in fade-in duration-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-3">
            <div>
              <span className="text-slate-400 text-[10px] uppercase font-bold tracking-wider">
                MULTIMODAL INTELLIGENCE RESULTS
              </span>
              <div className="text-xl font-bold text-slate-100 mt-1">{result.category}</div>
            </div>

            <div className="flex items-center gap-2">
              {committedIssue ? (
                <div className="px-3 py-1.5 bg-emerald-950/80 border border-emerald-700 text-emerald-300 rounded font-bold text-xs flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Committed ({committedIssue.issueId})</span>
                </div>
              ) : (
                <button
                  onClick={handleCommitIssue}
                  disabled={commitLoading}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs flex items-center gap-1.5 shadow transition disabled:opacity-50"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>{commitLoading ? 'Committing...' : 'Commit Work Order'}</span>
                </button>
              )}
            </div>
          </div>

          {/* Core Metrics: CATEGORY, URGENCY, SEVERITY, LOCATION, VISION CONFIDENCE, EVIDENCE CONSISTENCY, PRIORITY */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2.5">
            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">CATEGORY</div>
              <div className="font-bold text-slate-100 text-xs mt-1 truncate">
                {result.category}
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">URGENCY</div>
              <div className="font-bold text-amber-400 text-sm mt-1">
                {(result.urgency * 100).toFixed(0)}%
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">SEVERITY</div>
              <div className="font-bold text-rose-400 text-sm mt-1">
                {(result.overallSeverity * 100).toFixed(0)}%
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">LOCATION</div>
              <div className="font-bold text-slate-200 text-xs mt-1 truncate">
                {result.resolvedLocation}
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">VISION CONFIDENCE</div>
              <div className="font-bold text-cyan-400 text-sm mt-1">
                {((result.visualConfidence || 0.9) * 100).toFixed(0)}%
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">EVIDENCE CONSISTENCY</div>
              <div className="mt-1">
                <ConsistencyBadge
                  level={result.consistencyFlag}
                  score={result.evidenceConsistency}
                />
              </div>
            </div>

            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
              <div className="text-slate-400 text-[10px] uppercase">PRIORITY</div>
              <div className="font-bold text-cyan-300 text-sm mt-1">
                {result.priorityScore.toFixed(0)}/100 ({result.priorityLevel})
              </div>
            </div>
          </div>

          {/* Priority Breakdown (Explainable Factors) */}
          <div className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-2">
            <div className="text-[10px] uppercase font-bold text-slate-300 flex items-center justify-between">
              <span>Explainable Priority Breakdown (0-100 Score)</span>
              <span className="text-cyan-400">Total: {result.priorityScore.toFixed(1)}/100</span>
            </div>
            <PriorityGauge
              score={result.priorityScore}
              level={result.priorityLevel}
              breakdown={result.priorityBreakdown}
              reasoning={result.priorityReasoning}
              showDetails={true}
            />
          </div>

          {/* Recommended Department & Recommended Action */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-1.5">
              <div className="text-[10px] text-slate-400 uppercase font-bold">
                Recommended Department
              </div>
              <div className="flex items-center gap-2 text-slate-100 font-bold text-sm">
                <Building className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>{result.department}</span>
              </div>
              <div className="text-[10px] text-emerald-400 font-mono mt-1">
                Target Resolution SLA: {result.slaHours} Hours ({result.departmentCode})
              </div>
            </div>

            <div className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-1.5">
              <div className="text-[10px] text-slate-400 uppercase font-bold">
                Recommended Action Directive
              </div>
              <p className="text-slate-200 text-xs font-sans leading-relaxed">
                {result.recommendedAction}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
