import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Sparkles, Image, MapPin, AlertCircle } from 'lucide-react'
import { api } from '../../services/api'
import { Issue } from '../../types'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'

interface NewComplaintModalProps {
  isOpen: boolean
  onClose: () => void
  onIssueCreated: (issue: Issue) => void
  initialScenario?: number | null
}

export const NewComplaintModal: React.FC<NewComplaintModalProps> = ({
  isOpen,
  onClose,
  onIssueCreated,
  initialScenario,
}) => {
  const [complaintText, setComplaintText] = useState('')
  const [location, setLocation] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [previewAnalysis, setPreviewAnalysis] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  React.useEffect(() => {
    if (initialScenario) {
      loadScenario(initialScenario)
    }
  }, [initialScenario])

  const loadScenario = (num: number) => {
    setPreviewAnalysis(null)
    setError(null)
    if (num === 1) {
      setComplaintText(
        'Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk'
      )
      setLocation('Vidyavihar')
      setImageUrl('data/sample_pothole.jpg')
    } else if (num === 2) {
      setComplaintText(
        'Massive overflowing garbage dump on LBS Marg, rotten food waste and flies creating extreme stench'
      )
      setLocation('LBS Marg, Ghatkopar West')
      setImageUrl('data/sample_garbage.jpg')
    } else if (num === 3) {
      setComplaintText(
        'Major drinking water pipeline burst flooding 90 Feet Road Dharavi, millions of liters wasted'
      )
      setLocation('Dharavi')
      setImageUrl('data/sample_water_leak.jpg')
    } else if (num === 4) {
      setComplaintText('')
      setLocation('Kurla West')
      setImageUrl('data/patrol_survey_pothole.jpg')
    }
  }

  const handlePreAnalyze = async () => {
    if (!complaintText.trim() && !imageUrl.trim()) {
      setError('Please provide complaint text or an image.')
      return
    }
    setError(null)
    setAnalyzing(true)
    try {
      const res = await api.analyzeComplaint({
        complaintText,
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      setPreviewAnalysis(res)
    } catch (err: any) {
      setError(err.message || 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSubmit = async () => {
    if (!complaintText.trim() && !imageUrl.trim()) {
      setError('Please provide complaint text or an image.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await api.submitIssue({
        complaintText,
        location: location || undefined,
        imageUrl: imageUrl || undefined,
      })
      onIssueCreated(res)
      onClose()
    } catch (err: any) {
      setError(err.message || 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-3xl bg-[#0e131d] border border-slate-700 rounded-xl shadow-2xl overflow-hidden font-mono text-xs max-h-[90vh] flex flex-col"
          >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#121824] shrink-0">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <span className="font-bold text-slate-100 text-sm tracking-wide">
              INTAKE CIVIC COMPLAINT // AI PIPELINE
            </span>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 overflow-y-auto flex-1">
          {/* Quick Scenario Fillers */}
          <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg space-y-2">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              Load Evaluated Test Scenarios
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => loadScenario(1)}
                className="px-2 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 border border-rose-800/80 text-rose-300 rounded text-[11px] truncate text-left"
              >
                1. Pothole / Crash
              </button>
              <button
                type="button"
                onClick={() => loadScenario(2)}
                className="px-2 py-1.5 bg-amber-950/40 hover:bg-amber-900/60 border border-amber-800/80 text-amber-300 rounded text-[11px] truncate text-left"
              >
                2. Garbage Dump
              </button>
              <button
                type="button"
                onClick={() => loadScenario(3)}
                className="px-2 py-1.5 bg-sky-950/40 hover:bg-sky-900/60 border border-sky-800/80 text-sky-300 rounded text-[11px] truncate text-left"
              >
                3. Water Main Burst
              </button>
              <button
                type="button"
                onClick={() => loadScenario(4)}
                className="px-2 py-1.5 bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-800/80 text-cyan-300 rounded text-[11px] truncate text-left"
              >
                4. Patrol Camera
              </button>
            </div>
          </div>

          {/* Complaint Text */}
          <div className="space-y-1.5">
            <label className="text-[11px] uppercase font-bold text-slate-300 flex justify-between">
              <span>Citizen Complaint Description</span>
              <span className="text-slate-500 font-normal">NLP text analytics & cues</span>
            </label>
            <textarea
              rows={3}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              placeholder="e.g. Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk..."
              className="w-full bg-[#111724] border border-slate-700/80 text-slate-100 placeholder-slate-500 rounded p-3 text-xs font-sans outline-none focus:border-cyan-500 leading-relaxed"
            />
          </div>

          {/* Location & Image Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                <span>Reported Landmark / Location</span>
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Vidyavihar, LBS Marg, Dharavi"
                className="w-full bg-[#111724] border border-slate-700/80 text-slate-100 placeholder-slate-500 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
                <Image className="w-3.5 h-3.5 text-cyan-400" />
                <span>Image Path / URL (Optional)</span>
              </label>
              <input
                type="text"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="e.g. data/sample_pothole.jpg"
                className="w-full bg-[#111724] border border-slate-700/80 text-slate-100 placeholder-slate-500 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {error && (
            <div className="p-2.5 bg-rose-950/60 border border-rose-800 text-rose-300 rounded flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Pre-Analysis Result Panel */}
          {previewAnalysis && (
            <div className="p-3.5 bg-[#0a0d14] border border-cyan-900/60 rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <div className="text-[11px] font-bold text-cyan-400 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>PRE-SUBMISSION INTELLIGENCE PREVIEW</span>
                </div>
                <ConsistencyBadge
                  level={previewAnalysis.consistencyFlag || 'CONSISTENT'}
                  score={previewAnalysis.evidenceConsistency}
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-[11px]">
                <div className="p-2 bg-[#121824] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">CATEGORY (NLP)</div>
                  <div className="font-bold text-slate-200 mt-0.5 truncate">
                    {previewAnalysis.category}
                  </div>
                </div>

                <div className="p-2 bg-[#121824] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">URGENCY / SEVERITY</div>
                  <div className="font-bold text-amber-400 mt-0.5">
                    {(previewAnalysis.urgency * 100).toFixed(0)}% / {(previewAnalysis.severity * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-2 bg-[#121824] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">DEPARTMENT SLA</div>
                  <div className="font-bold text-emerald-400 mt-0.5 truncate">
                    {previewAnalysis.slaHours}h &bull; {previewAnalysis.departmentCode}
                  </div>
                </div>
              </div>

              {/* Priority Gauge */}
              <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                <PriorityGauge
                  score={previewAnalysis.priorityScore}
                  level={previewAnalysis.priorityLevel}
                  breakdown={previewAnalysis.priorityBreakdown}
                  reasoning={previewAnalysis.priorityReasoning}
                  showDetails={true}
                />
              </div>

              {/* Duplicate check & Hotspot status */}
              <div className="flex flex-wrap items-center gap-3 text-[10px] text-slate-400">
                <span>
                  Duplicate Match:{' '}
                  <strong className={previewAnalysis.isDuplicate ? 'text-amber-400' : 'text-slate-300'}>
                    {previewAnalysis.isDuplicate ? `YES (${previewAnalysis.duplicateGroup})` : 'NO'}
                  </strong>
                </span>
                <span>&bull;</span>
                <span>
                  Hotspot Cluster:{' '}
                  <strong className={previewAnalysis.isHotspot ? 'text-rose-400' : 'text-slate-300'}>
                    {previewAnalysis.isHotspot ? previewAnalysis.hotspotClusterId : 'NONE'}
                  </strong>
                </span>
                {previewAnalysis.recurringDetail?.recurringIssue && (
                  <>
                    <span>&bull;</span>
                    <span className="text-amber-400 font-bold">
                      RECURRING DEFECT ({previewAnalysis.recurringDetail.reportCount} prior reports)
                    </span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3.5 bg-[#0c1018] border-t border-slate-800 flex items-center justify-between shrink-0">
          <button
            type="button"
            onClick={handlePreAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#151c2a] hover:bg-[#1a2336] border border-slate-700 text-slate-200 rounded text-xs transition disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            <span>{analyzing ? 'Analyzing Pipeline...' : 'Test Full AI Pipeline'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded text-xs transition"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium text-xs transition disabled:opacity-50 shadow-lg shadow-cyan-950/50"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{loading ? 'Registering...' : 'Commit & Dispatch Issue'}</span>
            </button>
          </div>
        </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
