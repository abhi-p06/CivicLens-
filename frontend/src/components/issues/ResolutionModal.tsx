import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, ShieldCheck, Image as ImageIcon, Camera } from 'lucide-react'
import { api } from '../../services/api'
import { Issue } from '../../types'
import { cn } from '../../lib/utils'

interface ResolutionModalProps {
  isOpen: boolean
  onClose: () => void
  issue: Issue | null
  onVerified: (updatedIssue: Issue) => void
}

export const ResolutionModal: React.FC<ResolutionModalProps> = ({
  isOpen,
  onClose,
  issue,
  onVerified,
}) => {
  const [postActionImage, setPostActionImage] = useState('data/sample_repaired_pothole.jpg')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleVerify = async () => {
    if (!issue) return
    if (!postActionImage.trim()) {
      setError('Please provide a post-action verification image URL or path.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const res = await api.verifyResolution(issue.issueId, postActionImage)
      setResult(res)
      // fetch updated issue
      const updated = await api.getIssue(issue.issueId)
      onVerified(updated)
    } catch (err: any) {
      setError(err.message || 'Verification process failed')
    } finally {
      setLoading(false)
    }
  }

  const sampleImages = [
    { label: 'Repaired Surface (Clean Asphalt)', path: 'data/sample_repaired_pothole.jpg' },
    { label: 'Unresolved (Pothole Still Visible)', path: 'data/sample_pothole.jpg' },
    { label: 'Cleared Garbage Site', path: 'data/sample_cleared_site.jpg' },
  ]

  return (
    <AnimatePresence>
      {isOpen && issue && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 font-mono text-xs"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl bg-[#0e131d] border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#121824] shrink-0">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-slate-100 text-sm tracking-wide">
                  FEATURE 20: WORK-ORDER RESOLUTION VERIFICATION
                </span>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4 overflow-y-auto flex-1">
              <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg space-y-1">
                <div className="text-slate-400 text-[10px]">Target Issue</div>
                <div className="font-bold text-slate-100">{issue.issueId} &bull; {issue.category}</div>
                <div className="text-slate-400 text-[11px] truncate">{issue.complaintText}</div>
              </div>

              {/* Sample Photo Selectors */}
              <div className="space-y-1.5">
                <label className="text-[10px] uppercase font-bold text-slate-400">
                  Select Verification Evidence Photo
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {sampleImages.map((s) => (
                    <button
                      key={s.path}
                      type="button"
                      onClick={() => setPostActionImage(s.path)}
                      className={cn(
                        'p-2 rounded border text-left text-[11px] transition',
                        postActionImage === s.path
                          ? 'bg-emerald-950/60 border-emerald-600 text-emerald-200 font-bold'
                          : 'bg-[#111724] border-slate-800 text-slate-400 hover:text-slate-200'
                      )}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Image Input */}
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Post-Action Resolution Image Path / URI</span>
                </label>
                <input
                  type="text"
                  value={postActionImage}
                  onChange={(e) => setPostActionImage(e.target.value)}
                  placeholder="data/sample_repaired_pothole.jpg"
                  className="w-full bg-[#121824] border border-slate-700 rounded-lg p-2.5 text-slate-100 outline-none focus:border-cyan-500"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-950/60 border border-rose-800 text-rose-300 rounded-lg text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Verification Result Card */}
              {result && (
                <div className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-3 animate-in fade-in">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                    <span className="font-bold text-slate-100">Verification Outcome</span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-[10px] font-bold border uppercase',
                        result.resolutionStatus === 'LIKELY RESOLVED'
                          ? 'bg-emerald-950 border-emerald-700 text-emerald-300'
                          : 'bg-rose-950 border-rose-700 text-rose-300'
                      )}
                    >
                      {result.resolutionStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-[11px]">
                    <div>
                      <span className="text-slate-400">Confidence Score:</span>
                      <div className="font-bold text-cyan-400 text-sm">
                        {(result.resolutionConfidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-slate-400">Remaining Detection:</span>
                      <div className="font-bold text-slate-200">
                        {result.remainingDetection || 'None (Surface Cleared)'}
                      </div>
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-900/80 rounded border border-slate-800 text-slate-300 text-[11px] leading-relaxed">
                    {result.verificationSummary}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-4 bg-[#121824] border-t border-slate-800 flex items-center justify-between shrink-0">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 rounded border border-slate-700 text-slate-300 hover:bg-slate-800 transition"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleVerify}
                disabled={loading}
                className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-medium text-xs transition disabled:opacity-50 shadow-lg shadow-emerald-950/50"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>{loading ? 'Evaluating Imagery...' : 'Run Vision Verification'}</span>
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default ResolutionModal
