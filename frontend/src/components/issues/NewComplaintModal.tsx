import React, { useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Send, Sparkles, Image, MapPin, AlertCircle, Upload, Loader2, Check } from 'lucide-react'
import { api } from '../../services/api'
import { Issue } from '../../types'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { Portal } from '../common/Portal'

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

  // Real Image Upload State
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [previewThumbnail, setPreviewThumbnail] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  React.useEffect(() => {
    if (initialScenario) {
      loadScenario(initialScenario)
    }
  }, [initialScenario])

  const handleClearImage = () => {
    setUploadId(null)
    setImageUrl('')
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
      setImageUrl(res.previewUrl)
    } catch (err: any) {
      setUploadError(err.message || 'Image upload failed')
      setUploadId(null)
      setPreviewThumbnail(null)
      setSelectedFileName(null)
    } finally {
      setIsUploading(false)
    }
  }

  const loadScenario = (num: number) => {
    handleClearImage()
    setPreviewAnalysis(null)
    setError(null)
    if (num === 1) {
      setComplaintText(
        'Critical deep pothole crater breaking wheel rims and causing major skidding risk near school entrance.'
      )
      setLocation('Somaiya Vidyavihar Main Gate, Vidyavihar East')
      setImageUrl('data/test_samples/repair_pothole_before.jpg')
    } else if (num === 2) {
      setComplaintText(
        'Accumulated municipal garbage dump with discarded plastic bottles, cups, and decaying cartons along sidewalk creating extreme stench.'
      )
      setLocation('Station Road, Kurla West')
      setImageUrl('data/test_samples/bottle.jpg')
    } else if (num === 3) {
      setComplaintText(
        'Massive asphalt crater and structural road fissure breaking vehicle suspensions on main transit corridor.'
      )
      setLocation('S.V. Road, Santacruz')
      setImageUrl('data/test_samples/bottle.jpg')
    } else if (num === 4) {
      setComplaintText(
        'Deep road depression detected during autonomous visual patrol inspection near school perimeter.'
      )
      setLocation('Kurla West')
      setImageUrl('data/test_samples/pothole_multibox.jpg')
    }
  }

  const handlePreAnalyze = async () => {
    if (isUploading) {
      setError('Please wait for the image upload to complete.')
      return
    }
    if (!complaintText.trim() && !imageUrl.trim() && !uploadId) {
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
        uploadId: uploadId || undefined,
      })
      setPreviewAnalysis(res)
    } catch (err: any) {
      setError(err.message || 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSubmit = async () => {
    if (isUploading) {
      setError('Please wait for the image upload to complete.')
      return
    }
    if (!complaintText.trim() && !imageUrl.trim() && !uploadId) {
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
        uploadId: uploadId || undefined,
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
    <Portal>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[9000] layer-modal-backdrop bg-black/50 backdrop-blur-xs flex items-center justify-center p-4"
            onClick={onClose}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-[9001] layer-modal-content w-full max-w-3xl bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl overflow-hidden font-sans text-xs max-h-[90vh] flex flex-col"
            >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E4E7F1] bg-[#F0F2F9] shrink-0">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-[#6457E8]" />
            <span className="font-bold text-[#11162A] text-sm tracking-normal">
              Intake Civic Complaint &bull; AI Pipeline
            </span>
          </div>
          <button onClick={onClose} className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-black/5 transition cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1 bg-[#F6F7FC]">
          {/* Quick Scenario Fillers */}
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2.5">
            <div className="text-xs font-semibold text-[#65708B]">
              Load Primary Evaluated Civic Scenarios
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => loadScenario(1)}
                className="px-2.5 py-2 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 rounded-lg text-xs font-medium truncate text-left transition cursor-pointer"
              >
                1. Pothole / Road
              </button>
              <button
                type="button"
                onClick={() => loadScenario(2)}
                className="px-2.5 py-2 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 rounded-lg text-xs font-medium truncate text-left transition cursor-pointer"
              >
                2. Garbage / Litter
              </button>
              <button
                type="button"
                onClick={() => loadScenario(3)}
                className="px-2.5 py-2 bg-purple-50 hover:bg-purple-100 border border-purple-200 text-purple-800 rounded-lg text-xs font-medium truncate text-left transition cursor-pointer"
              >
                3. Mismatch Check
              </button>
              <button
                type="button"
                onClick={() => loadScenario(4)}
                className="px-2.5 py-2 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-[#6457E8] rounded-lg text-xs font-medium truncate text-left transition cursor-pointer"
              >
                4. Patrol Road Survey
              </button>
            </div>
          </div>

          {/* Complaint Text */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[#11162A] flex justify-between">
              <span>Citizen Complaint Description</span>
              <span className="text-[#65708B] font-normal">NLP text analytics & cues</span>
            </label>
            <textarea
              rows={3}
              value={complaintText}
              onChange={(e) => setComplaintText(e.target.value)}
              placeholder="e.g. Huge dangerous pothole near Somaiya Vidyavihar campus gate, bikes skidding causing serious accident risk..."
              className="w-full bg-white border border-[#E4E7F1] text-[#11162A] placeholder-[#65708B] rounded-xl p-3 text-sm font-sans outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs leading-relaxed"
            />
          </div>

          {/* Location & Image Inputs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#11162A] flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>Reported Landmark / Location</span>
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g. Vidyavihar, LBS Marg, Dharavi"
                className="w-full bg-white border border-[#E4E7F1] text-[#11162A] placeholder-[#65708B] rounded-xl p-2.5 text-xs font-sans outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#11162A] flex items-center justify-between">
                <span className="flex items-center gap-1.5">
                  <Image className="w-3.5 h-3.5 text-[#6457E8]" />
                  <span>Field Photo Evidence</span>
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
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                  placeholder={uploadId ? `Upload ID: ${uploadId}` : 'Image file or sample URI'}
                  className="flex-1 bg-white border border-[#E4E7F1] text-[#11162A] placeholder-[#65708B] rounded-xl p-2.5 text-xs font-mono outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
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
                        {selectedFileName || 'Uploaded Image'}
                      </div>
                      <div className="text-[10px] text-emerald-600 font-medium flex items-center gap-1">
                        <Check className="w-3 h-3" />
                        <span>Ready for AI analysis</span>
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
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{uploadError}</span>
                </div>
              )}
            </div>
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl flex items-center gap-2 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Pre-Analysis Result Panel */}
          {previewAnalysis && (
            <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-3">
              <div className="flex items-center justify-between border-b border-[#E4E7F1] pb-2.5">
                <div className="text-xs font-bold text-[#6457E8] flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Pre-Submission Intelligence Preview</span>
                </div>
                <ConsistencyBadge
                  level={previewAnalysis.consistencyFlag || 'CONSISTENT'}
                  score={previewAnalysis.evidenceConsistency}
                />
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 text-xs">
                <div className="p-2.5 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-[11px] font-medium">Category (NLP)</div>
                  <div className="font-bold text-[#11162A] mt-0.5 truncate">
                    {previewAnalysis.category}
                  </div>
                </div>

                <div className="p-2.5 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-[11px] font-medium">Urgency / Severity</div>
                  <div className="font-bold text-[#F97316] mt-0.5">
                    {(previewAnalysis.urgency * 100).toFixed(0)}% / {(previewAnalysis.severity * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="p-2.5 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                  <div className="text-[#65708B] text-[11px] font-medium">Department SLA</div>
                  <div className="font-bold text-emerald-700 mt-0.5 truncate">
                    {previewAnalysis.slaHours}h &bull; {previewAnalysis.departmentCode}
                  </div>
                </div>
              </div>

              {/* Priority Gauge */}
              <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                <PriorityGauge
                  score={previewAnalysis.priorityScore}
                  level={previewAnalysis.priorityLevel}
                  breakdown={previewAnalysis.priorityBreakdown}
                  reasoning={previewAnalysis.priorityReasoning}
                  showDetails={true}
                />
              </div>

              {/* Duplicate check & Hotspot status */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-[#65708B]">
                <span>
                  Duplicate Match:{' '}
                  <strong className={previewAnalysis.isDuplicate ? 'text-amber-600' : 'text-[#11162A]'}>
                    {previewAnalysis.isDuplicate ? `YES (${previewAnalysis.duplicateGroup})` : 'NO'}
                  </strong>
                </span>
                <span>&bull;</span>
                <span>
                  Hotspot Cluster:{' '}
                  <strong className={previewAnalysis.isHotspot ? 'text-[#EF4444]' : 'text-[#11162A]'}>
                    {previewAnalysis.isHotspot ? previewAnalysis.hotspotClusterId : 'NONE'}
                  </strong>
                </span>
                {previewAnalysis.recurringDetail?.recurringIssue && (
                  <>
                    <span>&bull;</span>
                    <span className="text-amber-600 font-bold">
                      RECURRING DEFECT ({previewAnalysis.recurringDetail.reportCount} prior reports)
                    </span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-white border-t border-[#E4E7F1] flex items-center justify-between shrink-0">
          <button
            type="button"
            onClick={handlePreAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-[#F0F2F9] hover:bg-slate-200/70 border border-[#E4E7F1] text-[#11162A] rounded-lg text-xs font-medium transition disabled:opacity-50 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-[#6457E8]" />
            <span>{analyzing ? 'Analyzing Pipeline...' : 'Test Full AI Pipeline'}</span>
          </button>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 bg-transparent hover:bg-slate-100 text-[#65708B] hover:text-[#11162A] rounded-lg text-xs font-medium transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-lg font-semibold text-xs transition disabled:opacity-50 shadow-xs cursor-pointer"
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
  </Portal>
)
}
