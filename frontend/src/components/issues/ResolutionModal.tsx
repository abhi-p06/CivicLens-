import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, ShieldCheck, Image as ImageIcon, Camera } from 'lucide-react'
import { api } from '../../services/api'
import { Issue } from '../../types'
import { cn } from '../../lib/utils'
import { Portal } from '../common/Portal'

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
    <Portal>
      <AnimatePresence>
        {isOpen && issue && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[9000] layer-modal-backdrop bg-black/50 backdrop-blur-xs flex items-center justify-center p-4 font-sans text-xs"
            onClick={onClose}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-[9001] layer-modal-content w-full max-w-2xl bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#E4E7F1] bg-[#F0F2F9] shrink-0">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span className="font-bold text-[#11162A] text-sm tracking-normal">
                  Work-Order Resolution Verification
                </span>
              </div>
              <button onClick={onClose} className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-black/5 transition cursor-pointer">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-[#F6F7FC]">
              <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-1">
                <div className="text-[#65708B] text-xs font-medium">Target Issue</div>
                <div className="font-bold text-[#11162A] text-sm">{issue.issueId} &bull; {issue.category}</div>
                <div className="text-[#65708B] text-xs truncate">{issue.complaintText}</div>
              </div>

              {/* Sample Photo Selectors */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-[#65708B]">
                  Select Verification Evidence Photo
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {sampleImages.map((s) => (
                    <button
                      key={s.path}
                      type="button"
                      onClick={() => setPostActionImage(s.path)}
                      className={cn(
                        'p-2.5 rounded-lg border text-left text-xs transition cursor-pointer',
                        postActionImage === s.path
                          ? 'bg-emerald-50 border-emerald-300 text-emerald-800 font-semibold shadow-xs'
                          : 'bg-white border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50'
                      )}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Image Input */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-[#11162A] flex items-center gap-1.5">
                  <ImageIcon className="w-3.5 h-3.5 text-[#6457E8]" />
                  <span>Post-Action Resolution Image Path / URI</span>
                </label>
                <input
                  type="text"
                  value={postActionImage}
                  onChange={(e) => setPostActionImage(e.target.value)}
                  placeholder="data/sample_repaired_pothole.jpg"
                  className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              {/* Verification Result Card */}
              {result && (
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-[#E4E7F1]">
                    <span className="font-bold text-[#11162A]">Verification Outcome</span>
                    <span
                      className={cn(
                        'px-2 py-0.5 rounded text-[10px] font-bold border uppercase',
                        result.resolutionStatus === 'LIKELY RESOLVED'
                          ? 'bg-emerald-100 border-emerald-300 text-emerald-800'
                          : 'bg-rose-100 border-rose-300 text-rose-800'
                      )}
                    >
                      {result.resolutionStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[#65708B]">Confidence Score:</span>
                      <div className="font-bold text-[#6457E8] text-sm mt-0.5">
                        {(result.resolutionConfidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-[#65708B]">Remaining Detection:</span>
                      <div className="font-bold text-[#11162A] text-sm mt-0.5">
                        {result.remainingDetection || 'None (Surface Cleared)'}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] text-[#11162A] text-xs leading-relaxed">
                    {result.verificationSummary}
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="px-6 py-4 bg-white border-t border-[#E4E7F1] flex items-center justify-between shrink-0">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-2 rounded-lg border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50 text-xs font-medium transition cursor-pointer"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handleVerify}
                disabled={loading}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#10B981] hover:bg-[#059669] text-white rounded-lg font-semibold text-xs transition disabled:opacity-50 shadow-xs cursor-pointer"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                <span>{loading ? 'Evaluating Imagery...' : 'Run Vision Verification'}</span>
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  </Portal>
)
}

export default ResolutionModal
