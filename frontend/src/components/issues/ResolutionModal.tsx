import React, { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, CheckCircle, AlertTriangle, ShieldCheck, Image as ImageIcon, Camera, Upload, Loader2, Check } from 'lucide-react'
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

  // Real Image Upload State
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [previewThumbnail, setPreviewThumbnail] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleClearImage = () => {
    setUploadId(null)
    setPostActionImage('')
    setSelectedFileName(null)
    setPreviewThumbnail(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Only JPEG, PNG, and WebP images are allowed.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File exceeds maximum upload size of 10 MB.')
      return
    }

    setUploadError(null)
    setError(null)
    setSelectedFileName(file.name)
    const localUrl = URL.createObjectURL(file)
    setPreviewThumbnail(localUrl)
    setIsUploading(true)

    try {
      const res = await api.uploadImage(file)
      setUploadId(res.uploadId)
      setPostActionImage(res.previewUrl)
    } catch (err: any) {
      setUploadError(err.message || 'Image upload failed')
      setUploadId(null)
      setPreviewThumbnail(null)
      setSelectedFileName(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleVerify = async () => {
    if (!issue) return
    if (isUploading) {
      setError('Please wait for the image upload to complete.')
      return
    }
    if (!postActionImage.trim() && !uploadId) {
      setError('Please provide a post-action verification image or upload.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const updated = await api.verifyResolution(issue.issueId, postActionImage || undefined, uploadId || undefined)
      setResult(updated.resolutionEvidence)
      onVerified(updated)
    } catch (err: any) {
      setError(err.message || 'Verification process failed')
    } finally {
      setLoading(false)
    }
  }

  const sampleImages = [
    { label: 'Repaired Surface (Clean Asphalt)', path: 'data/test_samples/repair_pothole_after_repaired.jpg' },
    { label: 'Unresolved (Pothole Still Visible)', path: 'data/test_samples/repair_pothole_before.jpg' },
    { label: 'Incompatible Angle / Indoor Scene', path: 'data/test_samples/incompatible_scene.jpg' },
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
                      onClick={() => {
                        handleClearImage()
                        setPostActionImage(s.path)
                      }}
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
                <label className="text-xs font-semibold text-[#11162A] flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <ImageIcon className="w-3.5 h-3.5 text-[#6457E8]" />
                    <span>Post-Action Resolution Evidence</span>
                  </span>
                  <span className="text-[#65708B] font-normal text-[11px]">
                    JPEG, PNG, WebP &le; 10MB
                  </span>
                </label>

                <input
                  type="file"
                  ref={fileInputRef}
                  accept="image/jpeg,image/png,image/webp"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={postActionImage}
                    onChange={(e) => setPostActionImage(e.target.value)}
                    placeholder={uploadId ? `Upload ID: ${uploadId}` : 'Image file or sample URI'}
                    className="flex-1 bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] font-mono outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
                  />
                  <button
                    type="button"
                    disabled={isUploading}
                    onClick={() => fileInputRef.current?.click()}
                    className="px-3 py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50 shrink-0"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                        <span>Uploading...</span>
                      </>
                    ) : (
                      <>
                        <Upload className="w-3.5 h-3.5 text-white" />
                        <span>Upload</span>
                      </>
                    )}
                  </button>
                </div>

                {(previewThumbnail || uploadId) && (
                  <div className="flex items-center justify-between p-2 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl mt-1.5">
                    <div className="flex items-center gap-2 min-w-0">
                      {previewThumbnail && (
                        <img
                          src={previewThumbnail}
                          alt="Upload preview"
                          className="w-8 h-8 object-cover rounded-lg border border-[#E4E7F1] shrink-0"
                        />
                      )}
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-[#11162A] truncate">
                          {selectedFileName || 'Uploaded Photo'}
                        </div>
                        <div className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          <span>Ready for verification</span>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleClearImage}
                      className="p-1 text-[#65708B] hover:text-rose-600 rounded-lg hover:bg-rose-50 transition cursor-pointer shrink-0"
                      title="Remove image"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}

                {uploadError && (
                  <div className="p-2 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg text-[11px] flex items-center gap-1.5 mt-1">
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}
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
                          : result.resolutionStatus === 'STILL PRESENT'
                          ? 'bg-rose-100 border-rose-300 text-rose-800'
                          : 'bg-amber-100 border-amber-300 text-amber-800'
                      )}
                    >
                      {result.resolutionStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs">
                    <div className="p-2 bg-[#F0F2F9] rounded-lg">
                      <span className="text-[10px] text-[#65708B] font-semibold uppercase block">Confidence</span>
                      <div className="font-bold text-[#6457E8] text-xs mt-0.5">
                        {((result.resolutionConfidence ?? 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="p-2 bg-[#F0F2F9] rounded-lg">
                      <span className="text-[10px] text-[#65708B] font-semibold uppercase block">Scene Aligned</span>
                      <div className="font-bold text-[#11162A] text-xs mt-0.5">
                        {result.sceneComparable ? 'Comparable' : 'Incompatible'}
                      </div>
                    </div>
                    <div className="p-2 bg-[#F0F2F9] rounded-lg">
                      <span className="text-[10px] text-[#65708B] font-semibold uppercase block">SSIM Index</span>
                      <div className="font-bold text-[#11162A] text-xs mt-0.5">
                        {result.comparisonMetrics?.ssim != null ? `${(result.comparisonMetrics.ssim * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="p-2 bg-[#F0F2F9] rounded-lg">
                      <span className="text-[10px] text-[#65708B] font-semibold uppercase block">Remaining</span>
                      <div className="font-bold text-[#11162A] text-xs mt-0.5 truncate">
                        {result.remainingDetection || 'None (Cleared)'}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] text-[#11162A] text-xs leading-relaxed space-y-1">
                    <div className="font-semibold text-[#11162A]">Method: {result.verificationMethod || 'yolo_before_after_comparison'}</div>
                    <div className="text-[#65708B]">{result.verificationSummary}</div>
                  </div>

                  {result.requiresManualReview && (
                    <div className="p-2 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg text-[11px] font-medium flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-amber-600" />
                      <span>Flagged for on-site supervisory review by Municipal Ward Engineer.</span>
                    </div>
                  )}
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
