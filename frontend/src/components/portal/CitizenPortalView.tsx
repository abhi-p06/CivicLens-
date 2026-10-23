import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PlusCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileText,
  MapPin,
  Camera,
  Upload,
  Loader2,
  Trash2,
  Eye,
  Activity,
  Sparkles,
  HelpCircle,
  Shield,
  Layers
} from 'lucide-react'
import { api } from '../../services/api'
import { Issue, IssueCategory, PriorityLevel } from '../../types'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../common/Toast'
import { useCivicMotion } from '../../lib/motionContext'

export const CitizenPortalView: React.FC = () => {
  const { user } = useAuth()
  const { success, error: toastError } = useToast()
  const { isReduced } = useCivicMotion()

  const [myIssues, setMyIssues] = useState<Issue[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'my_complaints' | 'new_complaint'>('my_complaints')

  // Form State for New Complaint
  const [complaintText, setComplaintText] = useState('')
  const [locationName, setLocationName] = useState('')
  const [categoryChoice, setCategoryChoice] = useState<'road' | 'garbage'>('road')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadedId, setUploadedId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [analysisPreview, setAnalysisPreview] = useState<any | null>(null)
  const [selectedIssueDetail, setSelectedIssueDetail] = useState<Issue | null>(null)

  const loadMyIssues = async () => {
    setIsLoading(true)
    try {
      const data = await api.getMyIssues()
      setMyIssues(data)
    } catch (err: any) {
      console.error('Failed to load citizen issues:', err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadMyIssues()
  }, [])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setPreviewUrl(URL.createObjectURL(file))
    setIsUploading(true)

    try {
      const uploadRes = await api.uploadImage(file)
      setUploadedId(uploadRes.uploadId)

      // Automatically trigger live analysis preview
      if (complaintText.trim()) {
        const preview = await api.analyzeComplaint({
          complaintText: complaintText.trim(),
          location: locationName.trim() || 'Mumbai Locality',
          uploadId: uploadRes.uploadId,
        })
        setAnalysisPreview(preview)
      }
    } catch (err: any) {
      toastError(err.message || 'Image upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleAnalyzePreview = async () => {
    if (!complaintText.trim()) return
    try {
      const preview = await api.analyzeComplaint({
        complaintText: complaintText.trim(),
        location: locationName.trim() || 'Mumbai Locality',
        uploadId: uploadedId || undefined,
      })
      setAnalysisPreview(preview)
    } catch (err) {
      console.error(err)
    }
  }

  const handleSubmitComplaint = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!complaintText.trim()) {
      toastError('Please describe the civic issue.')
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        complaintText: complaintText.trim(),
        location: locationName.trim() || 'Municipal Ward Area',
        uploadId: uploadedId || undefined,
        imageUrl: previewUrl || undefined,
        source: 'citizen_portal',
      }

      const created = await api.submitIssue(payload)
      success(`Complaint ${created.issueId} submitted successfully!`)

      // Reset form
      setComplaintText('')
      setLocationName('')
      setSelectedFile(null)
      setPreviewUrl(null)
      setUploadedId(null)
      setAnalysisPreview(null)
      setActiveTab('my_complaints')

      // Reload citizen complaints
      await loadMyIssues()
    } catch (err: any) {
      toastError(err.message || 'Failed to submit complaint')
    } finally {
      setIsSubmitting(false)
    }
  }

  // Summary counts
  const totalCount = myIssues.length
  const inProgressCount = myIssues.filter(
    (i) => i.status === 'ACTION IN PROGRESS' || i.status === 'VERIFICATION' || i.status === 'ASSIGNED'
  ).length
  const resolvedCount = myIssues.filter(
    (i) => i.status === 'RESOLVED'
  ).length

  return (
    <div className="space-y-6">
      {/* 1. Welcoming Hero Strip */}
      <div className="bg-white rounded-2xl border border-[#E4E7F1] p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono">
              CITIZEN ACCESS
            </span>
            <span className="text-xs text-[#65708B]">&bull;</span>
            <span className="text-xs text-[#65708B] font-medium">{user?.email}</span>
          </div>
          <h1 className="text-2xl font-extrabold text-[#11162A]">
            Welcome, {user?.name || 'Citizen'}
          </h1>
          <p className="text-xs sm:text-sm text-[#65708B] mt-0.5">
            Report road damage or garbage issues, submit photo evidence, and track verification outcomes in real time.
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setActiveTab('my_complaints')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer border ${
              activeTab === 'my_complaints'
                ? 'bg-[#13152E] text-white border-[#13152E]'
                : 'bg-white hover:bg-slate-50 text-[#11162A] border-[#E4E7F1]'
            }`}
          >
            My Complaints ({totalCount})
          </button>
          <button
            onClick={() => setActiveTab('new_complaint')}
            className={`px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition cursor-pointer flex items-center gap-1.5 shadow-sm ${
              activeTab === 'new_complaint'
                ? 'bg-[#6457E8] text-white'
                : 'bg-[#6457E8]/10 text-[#6457E8] hover:bg-[#6457E8]/20'
            }`}
          >
            <PlusCircle className="w-4 h-4" />
            <span>File Grievance</span>
          </button>
        </div>
      </div>

      {/* 2. Metrics Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-[#E4E7F1] p-4 flex items-center gap-3 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-[#6457E8] shrink-0">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-[#65708B] font-medium">Total Submitted</span>
            <p className="text-2xl font-extrabold text-[#11162A] leading-tight">{totalCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#E4E7F1] p-4 flex items-center gap-3 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600 shrink-0">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-[#65708B] font-medium">Under Action / Review</span>
            <p className="text-2xl font-extrabold text-[#11162A] leading-tight">{inProgressCount}</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-[#E4E7F1] p-4 flex items-center gap-3 shadow-xs">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 shrink-0">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs text-[#65708B] font-medium">Resolved & Verified</span>
            <p className="text-2xl font-extrabold text-[#11162A] leading-tight">{resolvedCount}</p>
          </div>
        </div>
      </div>

      {/* 3. Main Workspace: Tabs */}
      {activeTab === 'new_complaint' ? (
        /* New Complaint Submission Form */
        <motion.div
          initial={isReduced ? false : { opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl border border-[#E4E7F1] p-6 sm:p-8 shadow-xs"
        >
          <div className="max-w-2xl mx-auto">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-[#11162A]">File a New Civic Complaint</h2>
              <p className="text-xs text-[#65708B] mt-1">
                CIVILENS uses computer vision and natural language processing to triage your issue automatically.
              </p>
            </div>

            <form onSubmit={handleSubmitComplaint} className="space-y-5">
              {/* Category Quick Selector */}
              <div>
                <label className="block text-xs font-semibold text-[#11162A] mb-2">
                  Select Civic Category
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setCategoryChoice('road')
                      if (!complaintText) setComplaintText('Deep pothole and asphalt damage on roadway.')
                    }}
                    className={`p-3 rounded-xl border text-left transition cursor-pointer flex items-center gap-3 ${
                      categoryChoice === 'road'
                        ? 'border-[#6457E8] bg-[#6457E8]/5 ring-1 ring-[#6457E8]'
                        : 'border-[#E4E7F1] hover:bg-slate-50'
                    }`}
                  >
                    <span className="text-2xl">🚗</span>
                    <div>
                      <span className="block text-xs font-bold text-[#11162A]">
                        Road Damage & Potholes
                      </span>
                      <span className="text-[11px] text-[#65708B]">Crater, rutting, cracking</span>
                    </div>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setCategoryChoice('garbage')
                      if (!complaintText) setComplaintText('Overflowing garbage pile and street litter.')
                    }}
                    className={`p-3 rounded-xl border text-left transition cursor-pointer flex items-center gap-3 ${
                      categoryChoice === 'garbage'
                        ? 'border-[#6457E8] bg-[#6457E8]/5 ring-1 ring-[#6457E8]'
                        : 'border-[#E4E7F1] hover:bg-slate-50'
                    }`}
                  >
                    <span className="text-2xl">🗑️</span>
                    <div>
                      <span className="block text-xs font-bold text-[#11162A]">
                        Garbage & Litter
                      </span>
                      <span className="text-[11px] text-[#65708B]">Waste accumulation, trash</span>
                    </div>
                  </button>
                </div>
              </div>

              {/* Location Input */}
              <div>
                <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                  Location / Locality Landmark
                </label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    placeholder="e.g. Near Vidyavihar Station West, LBS Road"
                    value={locationName}
                    onChange={(e) => setLocationName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                  />
                </div>
              </div>

              {/* Complaint Description */}
              <div>
                <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                  Complaint Description
                </label>
                <textarea
                  rows={3}
                  required
                  placeholder="Describe the issue, approximate size, and hazards to traffic or pedestrians..."
                  value={complaintText}
                  onChange={(e) => setComplaintText(e.target.value)}
                  onBlur={handleAnalyzePreview}
                  className="w-full p-3 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition resize-none"
                />
              </div>

              {/* Photo Upload Dropzone */}
              <div>
                <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                  Attach Photo Evidence (Recommended)
                </label>
                <div className="border-2 border-dashed border-[#E4E7F1] hover:border-[#6457E8]/50 rounded-xl p-4 text-center transition bg-slate-50/50">
                  {previewUrl ? (
                    <div className="relative inline-block">
                      <img
                        src={previewUrl}
                        alt="Evidence preview"
                        className="max-h-48 rounded-lg object-cover border border-[#E4E7F1]"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedFile(null)
                          setPreviewUrl(null)
                          setUploadedId(null)
                          setAnalysisPreview(null)
                        }}
                        className="absolute top-2 right-2 p-1 bg-rose-600 text-white rounded-full hover:bg-rose-700 cursor-pointer shadow-sm"
                        title="Remove photo"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ) : (
                    <label className="cursor-pointer block py-4">
                      <Camera className="w-8 h-8 text-[#65708B] mx-auto mb-2" />
                      <span className="text-xs font-semibold text-[#6457E8] hover:underline block">
                        Upload image from camera or library
                      </span>
                      <span className="text-[11px] text-[#65708B] mt-0.5 block">
                        JPG, PNG, WebP up to 10MB
                      </span>
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                    </label>
                  )}

                  {isUploading && (
                    <div className="flex items-center justify-center gap-2 text-xs text-[#6457E8] mt-2">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Uploading and running computer vision inference...</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Real-time AI Analysis Preview */}
              {analysisPreview && (
                <div className="p-3.5 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs space-y-1.5">
                  <div className="flex items-center gap-2 font-bold text-[#6457E8]">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Real-time Multimodal Advisory Preview</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 text-[11px]">
                    <div>
                      <span className="text-slate-500 block">Classified Category</span>
                      <span className="font-semibold text-slate-800">{analysisPreview.category}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Vision Confidence</span>
                      <span className="font-semibold text-slate-800">
                        {analysisPreview.visualConfidence > 0
                          ? `${(analysisPreview.visualConfidence * 100).toFixed(0)}% (${analysisPreview.visualDetection})`
                          : 'Text-only heuristic'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Computed Priority</span>
                      <span className="font-semibold text-slate-800">
                        {analysisPreview.priorityScore?.toFixed(1)} / 100 ({analysisPreview.priorityLevel})
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Submit Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('my_complaints')}
                  className="px-4 py-2.5 rounded-xl text-xs font-semibold text-[#65708B] hover:text-[#11162A] hover:bg-slate-100 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting || isUploading}
                  className="px-6 py-2.5 rounded-xl bg-[#6457E8] hover:bg-[#5145CF] disabled:opacity-50 text-white text-xs sm:text-sm font-semibold transition cursor-pointer shadow-sm flex items-center gap-2"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Filing complaint...</span>
                    </>
                  ) : (
                    <>
                      <PlusCircle className="w-4 h-4" />
                      <span>Submit Grievance</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </motion.div>
      ) : (
        /* My Complaints List */
        <div className="bg-white rounded-2xl border border-[#E4E7F1] p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-[#11162A]">Your Grievance Tracker</h2>
              <p className="text-xs text-[#65708B]">
                Track all complaints filed from this citizen account and inspect verification audit trails.
              </p>
            </div>
            <button
              onClick={loadMyIssues}
              className="text-xs font-semibold text-[#6457E8] hover:underline cursor-pointer"
            >
              Refresh Statuses
            </button>
          </div>

          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center text-xs text-[#65708B] gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-[#6457E8]" />
              <span>Loading your submitted complaints...</span>
            </div>
          ) : myIssues.length === 0 ? (
            <div className="py-14 text-center border-2 border-dashed border-[#E4E7F1] rounded-xl">
              <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-[#11162A]">No complaints filed yet</h3>
              <p className="text-xs text-[#65708B] mt-1 max-w-sm mx-auto">
                Help keep Mumbai clean and safe. Report an open pothole or overflowing waste in your locality.
              </p>
              <button
                onClick={() => setActiveTab('new_complaint')}
                className="mt-4 px-4 py-2 bg-[#6457E8] text-white rounded-xl text-xs font-semibold hover:bg-[#5145CF] transition cursor-pointer inline-flex items-center gap-1.5 shadow-xs"
              >
                <PlusCircle className="w-4 h-4" />
                <span>File your first complaint</span>
              </button>
            </div>
          ) : (
            <div className="divide-y divide-[#E4E7F1]">
              {myIssues.map((issue) => {
                const isResolved = issue.status === 'RESOLVED'
                const isInProgress =
                  issue.status === 'ACTION IN PROGRESS' || issue.status === 'VERIFICATION'

                return (
                  <div
                    key={issue.issueId}
                    className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/60 transition p-2 rounded-xl"
                  >
                    <div className="flex items-start gap-3.5 min-w-0">
                      {/* Image Thumbnail or Category Icon */}
                      {issue.imageUrl ? (
                        <img
                          src={issue.imageUrl}
                          alt={issue.category}
                          className="w-14 h-14 rounded-lg object-cover border border-[#E4E7F1] shrink-0"
                        />
                      ) : (
                        <div className="w-14 h-14 rounded-lg bg-slate-100 flex items-center justify-center text-xl shrink-0 border border-[#E4E7F1]">
                          {issue.category.includes('Road') ? '🚗' : '🗑️'}
                        </div>
                      )}

                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-mono text-[11px] font-bold text-[#11162A]">
                            {issue.issueId}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-semibold border border-slate-200">
                            {issue.category}
                          </span>
                          <span
                            className={`text-[10px] px-2 py-0.5 rounded-full font-bold font-mono border ${
                              isResolved
                                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                : isInProgress
                                ? 'bg-amber-50 text-amber-700 border-amber-200'
                                : 'bg-blue-50 text-blue-700 border-blue-200'
                            }`}
                          >
                            {issue.status}
                          </span>
                        </div>

                        <p className="text-xs font-semibold text-[#11162A] mt-1 line-clamp-1">
                          {issue.complaintText}
                        </p>

                        <div className="flex items-center gap-3 text-[11px] text-[#65708B] mt-1 flex-wrap">
                          <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3 text-slate-400" />
                            {issue.location}
                          </span>
                          <span>&bull;</span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-400" />
                            {issue.timestamp}
                          </span>
                          {issue.visualDetection && (
                            <>
                              <span>&bull;</span>
                              <span className="text-[#6457E8] font-medium">
                                Detected: {issue.visualDetection} ({(((issue.visualConfidence ?? 0)) * 100).toFixed(0)}%)
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <button
                        onClick={() => setSelectedIssueDetail(issue)}
                        className="px-3 py-1.5 rounded-lg border border-[#E4E7F1] hover:bg-white text-xs font-medium text-[#11162A] transition cursor-pointer flex items-center gap-1 shadow-2xs"
                      >
                        <Eye className="w-3.5 h-3.5 text-[#6457E8]" />
                        <span>View Details</span>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* Detail Modal for Citizen Inspection */}
      <AnimatePresence>
        {selectedIssueDetail && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-2xl max-w-lg w-full p-6 border border-[#E4E7F1] shadow-xl text-xs space-y-4 max-h-[85vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-[#E4E7F1] pb-3">
                <div>
                  <span className="text-[10px] font-mono font-bold text-[#6457E8]">
                    {selectedIssueDetail.issueId}
                  </span>
                  <h3 className="text-base font-bold text-[#11162A]">Complaint Dossier</h3>
                </div>
                <button
                  onClick={() => setSelectedIssueDetail(null)}
                  className="p-1 rounded-lg hover:bg-slate-100 text-slate-500 text-sm cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <div>
                <span className="text-slate-500 font-medium block">Complaint Description</span>
                <p className="text-xs text-[#11162A] mt-0.5 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  {selectedIssueDetail.complaintText}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block">Category</span>
                  <span className="font-semibold text-slate-800">{selectedIssueDetail.category}</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block">Status</span>
                  <span className="font-semibold text-slate-800">{selectedIssueDetail.status}</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block">Assigned Department</span>
                  <span className="font-semibold text-slate-800">{selectedIssueDetail.department}</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-slate-500 block">SLA Commitment</span>
                  <span className="font-semibold text-slate-800">{selectedIssueDetail.slaHours} hours</span>
                </div>
              </div>

              {selectedIssueDetail.imageUrl && (
                <div>
                  <span className="text-slate-500 font-medium block mb-1">Attached Image</span>
                  <img
                    src={selectedIssueDetail.imageUrl}
                    alt="Complaint evidence"
                    className="w-full max-h-56 object-cover rounded-xl border border-[#E4E7F1]"
                  />
                </div>
              )}

              {selectedIssueDetail.resolutionEvidence && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200">
                  <div className="flex items-center gap-1.5 font-bold text-emerald-800 mb-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Resolution Verification Outcome</span>
                  </div>
                  <p className="text-[11px] text-emerald-700">
                    Status: {selectedIssueDetail.resolutionEvidence.resolutionStatus} (Confidence: {(selectedIssueDetail.resolutionEvidence.resolutionConfidence * 100).toFixed(0)}%)
                  </p>
                  {selectedIssueDetail.resolutionEvidence.verificationSummary && (
                    <p className="text-[11px] text-emerald-800 mt-1 italic">
                      "{selectedIssueDetail.resolutionEvidence.verificationSummary}"
                    </p>
                  )}
                </div>
              )}

              <div className="pt-2 text-right">
                <button
                  onClick={() => setSelectedIssueDetail(null)}
                  className="px-4 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold text-slate-700 cursor-pointer"
                >
                  Close Dossier
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}
