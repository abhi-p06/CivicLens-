import React, { useState } from 'react'
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

  if (!isOpen || !issue) return null

  const handleVerify = async () => {
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
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 font-mono text-xs">
      <div className="w-full max-w-2xl bg-[#0e131d] border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
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
          {/* Issue summary */}
          <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg flex items-start justify-between gap-3">
            <div>
              <div className="text-[10px] text-slate-400">TARGET INCIDENT</div>
              <div className="font-bold text-cyan-400 text-xs mt-0.5">{issue.issueId}</div>
              <div className="text-slate-300 text-[11px] mt-1 font-sans line-clamp-2">
                {issue.complaintText}
              </div>
            </div>
            <div className="text-right shrink-0">
              <div className="text-[10px] text-slate-400">ASSIGNED DEPT</div>
              <div className="text-slate-200 text-[11px] font-bold mt-0.5">{issue.department}</div>
            </div>
          </div>

          {/* Quick preset selector */}
          <div className="space-y-1.5">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              Select Field Verification Evidence
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {sampleImages.map((s) => (
                <button
                  key={s.path}
                  type="button"
                  onClick={() => setPostActionImage(s.path)}
                  className={cn(
                    'p-2 rounded border text-left transition text-[11px]',
                    postActionImage === s.path
                      ? 'bg-cyan-950/50 border-cyan-700 text-cyan-300'
                      : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                  )}
                >
                  <div className="font-semibold truncate">{s.label}</div>
                  <div className="text-[9px] text-slate-500 font-mono mt-0.5 truncate">{s.path}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Post action image input */}
          <div className="space-y-1">
            <label className="text-[11px] uppercase font-bold text-slate-300 flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5 text-cyan-400" />
              <span>Post-Action Field Photo URI</span>
            </label>
            <input
              type="text"
              value={postActionImage}
              onChange={(e) => setPostActionImage(e.target.value)}
              placeholder="e.g. data/sample_repaired_pothole.jpg"
              className="w-full bg-[#111724] border border-slate-700 text-slate-100 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
            />
          </div>

          {error && (
            <div className="p-2.5 bg-rose-950/60 border border-rose-800 text-rose-300 rounded text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Verification Result */}
          {result && (
            <div className="p-4 bg-[#0a0d14] border border-slate-800 rounded-lg space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-bold">
                  Computer Vision Verification Outcome
                </span>
                <span
                  className={cn(
                    'px-2.5 py-0.5 rounded font-bold border text-xs',
                    result.resolutionStatus === 'LIKELY RESOLVED'
                      ? 'bg-emerald-950/70 border-emerald-700 text-emerald-300'
                      : result.resolutionStatus === 'STILL PRESENT'
                      ? 'bg-rose-950/70 border-rose-700 text-rose-300'
                      : 'bg-amber-950/70 border-amber-700 text-amber-300'
                  )}
                >
                  {result.resolutionStatus}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[11px]">
                <div className="p-2 bg-[#121824] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">VERIFICATION CONFIDENCE</div>
                  <div className="text-base font-bold text-cyan-400 mt-0.5">
                    {(result.resolutionConfidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="p-2 bg-[#121824] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">RESIDUAL DEFECT DETECTION</div>
                  <div className="text-xs font-bold text-slate-200 mt-1 truncate">
                    {result.remainingDetection || 'None Detected (Surface Restored)'}
                  </div>
                </div>
              </div>

              <div className="p-2.5 bg-[#121824] rounded border border-slate-800 text-slate-300 text-[11px] font-sans leading-relaxed">
                {result.verificationSummary}
              </div>

              <div className="text-[10px] text-slate-500 italic font-sans">
                * Note: Model computes probabilistic visual change detection without asserting absolute certainty.
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3.5 bg-[#0c1018] border-t border-slate-800 flex items-center justify-between shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded text-xs transition"
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
      </div>
    </div>
  )
}
