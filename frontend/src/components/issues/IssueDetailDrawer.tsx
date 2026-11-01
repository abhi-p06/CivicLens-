import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  MapPin,
  Calendar,
  Building,
  CheckCircle2,
  Clock,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Flame,
  RotateCcw,
  ExternalLink,
  Eye,
  Wrench,
  ClipboardList,
  Send,
  Camera,
  AlertCircle,
  FileCheck,
  Check,
  Truck,
  ArrowRight,
} from 'lucide-react'
import { Issue, IssueStatus, FieldTeam, TimelineEvent } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { api } from '../../services/api'
import { cn } from '../../lib/utils'
import { Portal } from '../common/Portal'
import { useAuth } from '../../context/AuthContext'
import { AIGuidanceSection } from '../guidance/AIGuidanceSection'
import { GuidanceDocumentModal } from '../guidance/GuidanceDocumentModal'

interface IssueDetailDrawerProps {
  issue: Issue | null
  onClose: () => void
  onUpdateIssue: (updated: Issue) => void
  onNavigateToIntelligence?: (issue: Issue) => void
}

export const IssueDetailDrawer: React.FC<IssueDetailDrawerProps> = ({
  issue,
  onClose,
  onUpdateIssue,
  onNavigateToIntelligence,
}) => {
  const { user } = useAuth()
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [teams, setTeams] = useState<FieldTeam[]>([])
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)

  // Operations Form States
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [assignedDept, setAssignedDept] = useState('')
  const [assignedTeamId, setAssignedTeamId] = useState('')
  const [assignedOfficer, setAssignedOfficer] = useState('')
  const [assignedPriority, setAssignedPriority] = useState('HIGH')
  const [scheduledDate, setScheduledDate] = useState('')
  const [assignInstructions, setAssignInstructions] = useState('')
  const [submittingAssign, setSubmittingAssign] = useState(false)

  // Temporary Safety Measures State (Roads)
  const [barricadesPlaced, setBarricadesPlaced] = useState(false)
  const [conesDeployed, setConesDeployed] = useState(false)
  const [coldMixApplied, setColdMixApplied] = useState(false)
  const [warningSignsPosted, setWarningSignsPosted] = useState(false)
  const [tempNotes, setTempNotes] = useState('')
  const [submittingTemp, setSubmittingTemp] = useState(false)

  // Road Inspection State
  const [inspectionNotes, setInspectionNotes] = useState('')
  const [submittingInspection, setSubmittingInspection] = useState(false)

  // Road Repair Progress State
  const [repairNotes, setRepairNotes] = useState('')
  const [submittingRepair, setSubmittingRepair] = useState(false)

  // Sanitation Repeat Collection State
  const [repeatFrequency, setRepeatFrequency] = useState('WEEKLY')
  const [nextCollectionDate, setNextCollectionDate] = useState('')
  const [repeatNotes, setRepeatNotes] = useState('')
  const [submittingRepeat, setSubmittingRepeat] = useState(false)

  // Sanitation Cleanup Progress State
  const [sanitationProgressNotes, setSanitationProgressNotes] = useState('')
  const [submittingSanitationProgress, setSubmittingSanitationProgress] = useState(false)

  // Completion State
  const [completionNote, setCompletionNote] = useState('')
  const [completionPhotoUrl, setCompletionPhotoUrl] = useState('')
  const [submittingCompletion, setSubmittingCompletion] = useState(false)
  const [completionError, setCompletionError] = useState<string | null>(null)

  // Reopen State
  const [reopenReason, setReopenReason] = useState('')
  const [submittingReopen, setSubmittingReopen] = useState(false)
  const [reopenError, setReopenError] = useState<string | null>(null)

  // Load field teams on mount
  useEffect(() => {
    let mounted = true
    api.getFieldTeams().then((data) => {
      if (mounted) setTeams(data)
    }).catch(() => {})
    return () => {
      mounted = false
    }
  }, [])

  // Sync state with active issue
  useEffect(() => {
    if (issue) {
      setAssignedDept(issue.department || (issue.category?.includes('Road') ? 'Roads & Footpaths' : 'Sanitation & Garbage'))
      setAssignedOfficer(issue.assignment?.assigned_officer || user?.name || 'Abhinay')
      setAssignedPriority(issue.assignment?.priority || issue.priorityLevel || 'HIGH')
      setScheduledDate(issue.assignment?.scheduled_date || '')
      setAssignInstructions(issue.assignment?.instructions || '')
      if (issue.assignment?.team_id) {
        setAssignedTeamId(issue.assignment.team_id)
      } else {
        const matchingTeam = teams.find((t) => t.department === (issue.department || 'Roads & Footpaths'))
        setAssignedTeamId(matchingTeam ? matchingTeam.id : (teams[0]?.id || ''))
      }

      if (issue.temporary_measures) {
        const m = issue.temporary_measures.measures || []
        setBarricadesPlaced(m.includes('Barricades Placed'))
        setConesDeployed(m.includes('Traffic Cones Deployed'))
        setColdMixApplied(m.includes('Cold Mix Temporary Fill'))
        setWarningSignsPosted(m.includes('Warning Signs Posted'))
        setTempNotes(issue.temporary_measures.notes || '')
      }

      if (issue.repeat_collection) {
        setRepeatFrequency(issue.repeat_collection.frequency || 'WEEKLY')
        setNextCollectionDate(issue.repeat_collection.next_collection_date || '')
        setRepeatNotes(issue.repeat_collection.instructions || '')
      }

      setCompletionNote('')
      setCompletionPhotoUrl('')
      setCompletionError(null)
      setReopenReason('')
      setReopenError(null)
    }
  }, [issue, teams, user])

  const isRoadCategory =
    issue?.category === 'Roads & Footpaths' ||
    issue?.category?.toLowerCase().includes('road') ||
    issue?.category?.toLowerCase().includes('pothole')

  const isSanitationCategory =
    issue?.category === 'Sanitation & Garbage' ||
    issue?.category?.toLowerCase().includes('sanitation') ||
    issue?.category?.toLowerCase().includes('garbage') ||
    issue?.category?.toLowerCase().includes('waste')

  const handleStatusChange = async (newStatus: IssueStatus) => {
    if (!issue) return
    setUpdatingStatus(true)
    try {
      const updated = await api.updateStatus(issue.issueId, newStatus, `Lifecycle state advanced to ${newStatus}`)
      onUpdateIssue(updated)
    } catch (err) {
      console.error(err)
    } finally {
      setUpdatingStatus(false)
    }
  }

  // Handle Task Assignment Submit
  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue || !assignedTeamId) return
    setSubmittingAssign(true)
    try {
      const selectedTeam = teams.find((t) => t.id === assignedTeamId)
      const updated = await api.assignTask(issue.issueId, {
        department: assignedDept,
        team_id: assignedTeamId,
        team_name: selectedTeam ? selectedTeam.name : 'Field Operations Team',
        assigned_officer: assignedOfficer,
        priority: assignedPriority,
        scheduled_date: scheduledDate,
        instructions: assignInstructions,
      })
      onUpdateIssue(updated)
      setShowAssignForm(false)
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingAssign(false)
    }
  }

  // Handle Temporary Measures (Roads)
  const handleTemporaryMeasuresSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue) return
    setSubmittingTemp(true)
    try {
      const measuresList: string[] = []
      if (barricadesPlaced) measuresList.push('Barricades Placed')
      if (conesDeployed) measuresList.push('Traffic Cones Deployed')
      if (coldMixApplied) measuresList.push('Cold Mix Temporary Fill')
      if (warningSignsPosted) measuresList.push('Warning Signs Posted')

      const updated = await api.recordAction(issue.issueId, {
        action_type: 'TEMPORARY_SAFETY_MEASURES',
        measures: measuresList,
        notes: tempNotes || undefined,
      })
      onUpdateIssue(updated)
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingTemp(false)
    }
  }

  // Handle Inspection Completed
  const handleInspectionCompleted = async () => {
    if (!issue) return
    setSubmittingInspection(true)
    try {
      const updated = await api.recordAction(issue.issueId, {
        action_type: 'ROAD_INSPECTION_COMPLETED',
        notes: inspectionNotes || 'Site physical inspection completed by Ward Officer',
      })
      onUpdateIssue(updated)
      setInspectionNotes('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingInspection(false)
    }
  }

  // Handle Repair Progress
  const handleRepairProgressSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue || !repairNotes.trim()) return
    setSubmittingRepair(true)
    try {
      const updated = await api.recordAction(issue.issueId, {
        action_type: 'ROAD_REPAIR_PROGRESS',
        stage: 'In Progress',
        notes: repairNotes.trim(),
      })
      onUpdateIssue(updated)
      setRepairNotes('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingRepair(false)
    }
  }

  // Handle Repeat Collection (Sanitation)
  const handleRepeatCollectionSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue) return
    setSubmittingRepeat(true)
    try {
      const updated = await api.recordAction(issue.issueId, {
        action_type: 'REPEAT_COLLECTION_SCHEDULED',
        frequency: repeatFrequency,
        scheduled_date: nextCollectionDate || undefined,
        notes: repeatNotes || undefined,
      })
      onUpdateIssue(updated)
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingRepeat(false)
    }
  }

  // Handle Sanitation Cleanup Progress
  const handleSanitationProgressSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue || !sanitationProgressNotes.trim()) return
    setSubmittingSanitationProgress(true)
    try {
      const updated = await api.recordAction(issue.issueId, {
        action_type: 'CLEANUP_PROGRESS',
        stage: 'In Progress',
        notes: sanitationProgressNotes.trim(),
      })
      onUpdateIssue(updated)
      setSanitationProgressNotes('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingSanitationProgress(false)
    }
  }

  // Handle Task Completion
  const handleCompleteTaskSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue) return
    if (!completionNote.trim()) {
      setCompletionError('A descriptive completion note is required before closing this task.')
      return
    }
    setSubmittingCompletion(true)
    setCompletionError(null)
    try {
      const updated = await api.completeTask(issue.issueId, {
        completion_note: completionNote.trim(),
        closure_reason: 'Work completed according to municipal specification',
        completion_photo_url: completionPhotoUrl.trim() || undefined,
      })
      onUpdateIssue(updated)
    } catch (err: any) {
      console.error(err)
      setCompletionError(err.message || 'Failed to complete task')
    } finally {
      setSubmittingCompletion(false)
    }
  }

  // Handle Reopen Task
  const handleReopenSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!issue) return
    if (!reopenReason.trim()) {
      setReopenError('Please provide a reason for reopening this complaint.')
      return
    }
    setSubmittingReopen(true)
    setReopenError(null)
    try {
      const updated = await api.reopenTask(issue.issueId, {
        reason: reopenReason.trim(),
        note: `Reopened by ${user?.name || 'Abhinay'}`,
      })
      onUpdateIssue(updated)
      setReopenReason('')
    } catch (err: any) {
      console.error(err)
      setReopenError(err.message || 'Failed to reopen complaint')
    } finally {
      setSubmittingReopen(false)
    }
  }

  const isResolved = issue?.status === 'RESOLVED' || issue?.status === 'Verified Closed'

  // Pre-filter teams by active department
  const filteredTeams = teams.filter((t) => !assignedDept || t.department === assignedDept || teams.length <= 4)

  return (
    <Portal>
      <AnimatePresence>
        {issue && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="fixed inset-0 z-[8000] layer-drawer bg-black/40 backdrop-blur-xs flex justify-end"
            onClick={onClose}
          >
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 32, stiffness: 350 }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-[8001] w-full max-w-2xl bg-white border-l border-[#E4E7F1] h-full flex flex-col shadow-2xl font-sans text-sm overflow-hidden"
            >
              {/* Header */}
              <div className="px-6 py-5 border-b border-[#E4E7F1] bg-[#F0F2F9] flex items-center justify-between shrink-0">
                <div>
                  <div className="flex items-center gap-2.5">
                    <span className="text-base font-bold text-[#11162A] font-mono">{issue.issueId}</span>
                    <StatusBadge status={issue.status} />
                    {issue.status === 'REOPENED' && (
                      <span className="px-2 py-0.5 rounded-full text-xs bg-rose-100 text-rose-800 border border-rose-300 font-bold">
                        Reopened
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-[#65708B] mt-1.5 flex items-center gap-3">
                    <span className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#65708B]" />
                      {issue.location} {issue.ward ? `(${issue.ward})` : ''}
                    </span>
                    <span>&bull;</span>
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-[#65708B]" />
                      {new Date(issue.timestamp).toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {onNavigateToIntelligence && (
                    <button
                      onClick={() => {
                        onNavigateToIntelligence(issue)
                        onClose()
                      }}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-lg text-xs font-semibold shadow-xs transition cursor-pointer"
                      title="Open complete Issue Intelligence Dossier"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Full Dossier</span>
                    </button>
                  )}
                  <button
                    onClick={onClose}
                    className="text-[#65708B] hover:text-[#11162A] p-1.5 rounded-lg hover:bg-black/5 transition cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Scrollable Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-[#F6F7FC]">
                {/* AI FIELD GUIDANCE SECTION */}
                <AIGuidanceSection
                  issue={issue}
                  onIssueUpdated={onUpdateIssue}
                  onOpenDocument={(docId) => setSelectedDocumentId(docId)}
                />

                {/* 1. TASK ASSIGNMENT & SCHEDULING SECTION */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-[#6457E8]/10 text-[#6457E8]">
                        <Wrench className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-[#11162A] tracking-tight">
                        Field Team Assignment & Schedule
                      </span>
                    </div>

                    <button
                      onClick={() => setShowAssignForm(!showAssignForm)}
                      className="px-3 py-1 bg-[#F0F2F9] hover:bg-[#6457E8] hover:text-white text-[#11162A] border border-[#E4E7F1] rounded-lg text-xs font-semibold transition cursor-pointer"
                    >
                      {showAssignForm ? 'Close Assignment Form' : issue.assignment?.team_name ? 'Reassign / Reschedule' : 'Assign Field Team'}
                    </button>
                  </div>

                  {/* Current Assignment Display */}
                  {issue.assignment?.team_name ? (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-xl bg-[#F0F2F9] border border-[#E4E7F1] text-xs">
                      <div>
                        <span className="text-[#65708B] block text-[11px]">Field Team</span>
                        <strong className="text-[#11162A] font-semibold">{issue.assignment.team_name}</strong>
                      </div>
                      <div>
                        <span className="text-[#65708B] block text-[11px]">Assigned Officer</span>
                        <span className="text-[#11162A] font-medium">{issue.assignment.assigned_officer || 'Abhinay'}</span>
                      </div>
                      <div>
                        <span className="text-[#65708B] block text-[11px]">Scheduled Date</span>
                        <span className="text-[#11162A] font-medium">{issue.assignment.scheduled_date || 'Pending'}</span>
                      </div>
                      <div>
                        <span className="text-[#65708B] block text-[11px]">Priority</span>
                        <span className="font-bold text-[#6457E8]">{issue.assignment.priority || issue.priorityLevel}</span>
                      </div>
                      {issue.assignment.instructions && (
                        <div className="col-span-2 sm:col-span-4 pt-1.5 border-t border-[#E4E7F1] text-[11px] text-[#65708B]">
                          <strong className="text-[#11162A]">Instructions:</strong> {issue.assignment.instructions}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ClipboardList className="w-4 h-4 text-amber-600 shrink-0" />
                        <span>No field team has been assigned to this complaint yet.</span>
                      </div>
                      <button
                        onClick={() => setShowAssignForm(true)}
                        className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-xs font-semibold transition cursor-pointer"
                      >
                        Assign Now
                      </button>
                    </div>
                  )}

                  {/* Inline Assignment Form */}
                  {showAssignForm && (
                    <form onSubmit={handleAssignSubmit} className="pt-2 border-t border-[#E4E7F1] space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="text-xs font-semibold text-[#65708B] block mb-1">
                            Responsible Department
                          </label>
                          <select
                            value={assignedDept}
                            onChange={(e) => setAssignedDept(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8]"
                          >
                            <option value="Roads & Footpaths">Roads & Footpaths</option>
                            <option value="Sanitation & Garbage">Sanitation & Garbage</option>
                          </select>
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-[#65708B] block mb-1">
                            Predefined Field Team
                          </label>
                          <select
                            value={assignedTeamId}
                            onChange={(e) => setAssignedTeamId(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8]"
                          >
                            {filteredTeams.map((team) => (
                              <option key={team.id} value={team.id}>
                                {team.name} ({team.status})
                              </option>
                            ))}
                          </select>
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-[#65708B] block mb-1">
                            Assigned Officer
                          </label>
                          <input
                            type="text"
                            value={assignedOfficer}
                            onChange={(e) => setAssignedOfficer(e.target.value)}
                            placeholder="Officer Name"
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>

                        <div>
                          <label className="text-xs font-semibold text-[#65708B] block mb-1">
                            Scheduled Work Date
                          </label>
                          <input
                            type="date"
                            value={scheduledDate}
                            onChange={(e) => setScheduledDate(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-xs font-semibold text-[#65708B] block mb-1">
                          Instructions for Team
                        </label>
                        <textarea
                          rows={2}
                          value={assignInstructions}
                          onChange={(e) => setAssignInstructions(e.target.value)}
                          placeholder="Specific equipment, materials or access instructions..."
                          className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8]"
                        />
                      </div>

                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setShowAssignForm(false)}
                          className="px-3 py-1.5 text-xs text-[#65708B] hover:text-[#11162A] font-medium"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submittingAssign}
                          className="px-4 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-50"
                        >
                          {submittingAssign ? 'Saving...' : 'Confirm Assignment'}
                        </button>
                      </div>
                    </form>
                  )}
                </div>

                {/* 2. ISSUE-SPECIFIC OPERATIONS ACTIONS */}
                {isRoadCategory && (
                  <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-orange-50 border border-orange-200 text-[#F97316]">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-[#11162A] tracking-tight">
                        Road Damage & Pothole Field Actions
                      </span>
                    </div>

                    {/* Temporary Safety Measures Checkboxes */}
                    <form onSubmit={handleTemporaryMeasuresSubmit} className="p-3 bg-[#F0F2F9] rounded-xl space-y-2.5">
                      <span className="text-xs font-semibold text-[#11162A] block">
                        Record Temporary Safety Measures
                      </span>
                      <div className="grid grid-cols-2 gap-2 text-xs text-[#11162A]">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={barricadesPlaced}
                            onChange={(e) => setBarricadesPlaced(e.target.checked)}
                            className="rounded border-[#E4E7F1] text-[#6457E8] focus:ring-[#6457E8]"
                          />
                          <span>Barricades Placed</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={conesDeployed}
                            onChange={(e) => setConesDeployed(e.target.checked)}
                            className="rounded border-[#E4E7F1] text-[#6457E8] focus:ring-[#6457E8]"
                          />
                          <span>Traffic Cones Deployed</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={coldMixApplied}
                            onChange={(e) => setColdMixApplied(e.target.checked)}
                            className="rounded border-[#E4E7F1] text-[#6457E8] focus:ring-[#6457E8]"
                          />
                          <span>Cold Mix Temporary Fill</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={warningSignsPosted}
                            onChange={(e) => setWarningSignsPosted(e.target.checked)}
                            className="rounded border-[#E4E7F1] text-[#6457E8] focus:ring-[#6457E8]"
                          />
                          <span>Warning Signs Posted</span>
                        </label>
                      </div>

                      <div className="flex gap-2 pt-1">
                        <input
                          type="text"
                          value={tempNotes}
                          onChange={(e) => setTempNotes(e.target.value)}
                          placeholder="Safety notes (e.g., Ward 4 fast response crew deployed cones)"
                          className="flex-1 bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg px-2.5 py-1 text-xs outline-none focus:border-[#6457E8]"
                        />
                        <button
                          type="submit"
                          disabled={submittingTemp}
                          className="px-3 py-1 bg-[#13152E] text-white rounded-lg text-xs font-semibold hover:bg-[#212348] transition cursor-pointer disabled:opacity-50"
                        >
                          {submittingTemp ? 'Recording...' : 'Save Safety Measures'}
                        </button>
                      </div>
                    </form>

                    {/* Inspection & Progress Quick Actions */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {/* Mark Inspection Completed */}
                      <div className="p-3 bg-[#F0F2F9] rounded-xl space-y-2">
                        <span className="text-xs font-semibold text-[#11162A] block">
                          Inspection Verification
                        </span>
                        <input
                          type="text"
                          value={inspectionNotes}
                          onChange={(e) => setInspectionNotes(e.target.value)}
                          placeholder="Inspection findings..."
                          className="w-full bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg px-2.5 py-1 text-xs outline-none focus:border-[#6457E8]"
                        />
                        <button
                          type="button"
                          onClick={handleInspectionCompleted}
                          disabled={submittingInspection}
                          className="w-full py-1.5 bg-white border border-[#E4E7F1] hover:border-[#6457E8] hover:text-[#6457E8] text-[#11162A] font-semibold text-xs rounded-lg transition cursor-pointer"
                        >
                          {submittingInspection ? 'Updating...' : 'Mark Inspection Completed'}
                        </button>
                      </div>

                      {/* Record Repair Progress */}
                      <form onSubmit={handleRepairProgressSubmit} className="p-3 bg-[#F0F2F9] rounded-xl space-y-2">
                        <span className="text-xs font-semibold text-[#11162A] block">
                          Track Repair Progress
                        </span>
                        <input
                          type="text"
                          value={repairNotes}
                          onChange={(e) => setRepairNotes(e.target.value)}
                          placeholder="Asphalt layering, roller active..."
                          className="w-full bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg px-2.5 py-1 text-xs outline-none focus:border-[#6457E8]"
                        />
                        <button
                          type="submit"
                          disabled={submittingRepair || !repairNotes.trim()}
                          className="w-full py-1.5 bg-[#6457E8] text-white font-semibold text-xs rounded-lg hover:bg-[#5145CF] transition cursor-pointer disabled:opacity-50"
                        >
                          {submittingRepair ? 'Recording...' : 'Update Repair Progress'}
                        </button>
                      </form>
                    </div>
                  </div>
                )}

                {isSanitationCategory && (
                  <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-4">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-[#10B981]">
                        <Truck className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-[#11162A] tracking-tight">
                        Sanitation & Waste Cleanup Actions
                      </span>
                    </div>

                    {/* Schedule Repeat Collection */}
                    <form onSubmit={handleRepeatCollectionSubmit} className="p-3 bg-[#F0F2F9] rounded-xl space-y-2.5">
                      <span className="text-xs font-semibold text-[#11162A] block">
                        Schedule Recurring Waste Collection
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        <div>
                          <label className="text-[11px] text-[#65708B] block mb-1">Frequency</label>
                          <select
                            value={repeatFrequency}
                            onChange={(e) => setRepeatFrequency(e.target.value)}
                            className="w-full bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg p-1.5 text-xs outline-none focus:border-[#6457E8]"
                          >
                            <option value="DAILY">Daily Pickup</option>
                            <option value="WEEKLY">Weekly Routine</option>
                            <option value="BIWEEKLY">Twice Weekly</option>
                            <option value="MONTHLY">Monthly Sweep</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[11px] text-[#65708B] block mb-1">Next Collection Date</label>
                          <input
                            type="date"
                            value={nextCollectionDate}
                            onChange={(e) => setNextCollectionDate(e.target.value)}
                            className="w-full bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg p-1.5 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>
                      </div>

                      <div className="flex gap-2 pt-1">
                        <input
                          type="text"
                          value={repeatNotes}
                          onChange={(e) => setRepeatNotes(e.target.value)}
                          placeholder="Collection notes (e.g. morning compactor truck dispatch)"
                          className="flex-1 bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg px-2.5 py-1 text-xs outline-none focus:border-[#6457E8]"
                        />
                        <button
                          type="submit"
                          disabled={submittingRepeat}
                          className="px-3 py-1 bg-[#10B981] hover:bg-emerald-600 text-white rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50"
                        >
                          {submittingRepeat ? 'Saving...' : 'Set Repeat Schedule'}
                        </button>
                      </div>
                    </form>

                    {/* Cleanup Progress Quick Action */}
                    <form onSubmit={handleSanitationProgressSubmit} className="p-3 bg-[#F0F2F9] rounded-xl space-y-2">
                      <span className="text-xs font-semibold text-[#11162A] block">
                        Record Waste Cleanup Progress
                      </span>
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={sanitationProgressNotes}
                          onChange={(e) => setSanitationProgressNotes(e.target.value)}
                          placeholder="e.g., 2 tons cleared, bin sanitized and replaced..."
                          className="flex-1 bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg px-2.5 py-1 text-xs outline-none focus:border-[#6457E8]"
                        />
                        <button
                          type="submit"
                          disabled={submittingSanitationProgress || !sanitationProgressNotes.trim()}
                          className="px-3 py-1 bg-[#6457E8] text-white font-semibold text-xs rounded-lg hover:bg-[#5145CF] transition cursor-pointer disabled:opacity-50"
                        >
                          {submittingSanitationProgress ? 'Updating...' : 'Record Progress'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {/* 3. WORK ORDER COMPLETION & CLOSURE */}
                {!isResolved ? (
                  <form onSubmit={handleCompleteTaskSubmit} className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-[#11162A] tracking-tight">
                        Complete Work Order & Close Complaint
                      </span>
                    </div>

                    {completionError && (
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{completionError}</span>
                      </div>
                    )}

                    <div>
                      <label className="text-xs font-semibold text-[#11162A] block mb-1">
                        Completion Note <span className="text-rose-500">* (Mandatory)</span>
                      </label>
                      <textarea
                        rows={2}
                        value={completionNote}
                        onChange={(e) => setCompletionNote(e.target.value)}
                        placeholder="Detail the work carried out, materials utilized, and site handover status..."
                        className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2.5 text-xs outline-none focus:border-emerald-500 font-sans"
                      />
                    </div>

                    <div>
                      <label className="text-xs font-semibold text-[#65708B] block mb-1">
                        Completion Photo Proof URL (Optional)
                      </label>
                      <input
                        type="text"
                        value={completionPhotoUrl}
                        onChange={(e) => setCompletionPhotoUrl(e.target.value)}
                        placeholder="https://... or /data/proof_..."
                        className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-emerald-500 font-sans"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={submittingCompletion || !completionNote.trim()}
                        className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-xs transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <Check className="w-4 h-4" />
                        <span>{submittingCompletion ? 'Closing Complaint...' : 'Confirm Completion & Close'}</span>
                      </button>
                    </div>
                  </form>
                ) : (
                  /* Reopen Box for Resolved Complaints */
                  <form onSubmit={handleReopenSubmit} className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-600">
                          <RotateCcw className="w-4 h-4" />
                        </div>
                        <span className="text-xs font-bold text-[#11162A] tracking-tight">
                          Reopen Complaint
                        </span>
                      </div>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 font-medium border border-emerald-200">
                        Status: Resolved
                      </span>
                    </div>

                    {reopenError && (
                      <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>{reopenError}</span>
                      </div>
                    )}

                    <div>
                      <input
                        type="text"
                        value={reopenReason}
                        onChange={(e) => setReopenReason(e.target.value)}
                        placeholder="Enter justification for reopening this complaint..."
                        className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2.5 text-xs outline-none focus:border-rose-500 font-sans"
                      />
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={submittingReopen || !reopenReason.trim()}
                        className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow-xs transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>{submittingReopen ? 'Reopening...' : 'Reopen Complaint'}</span>
                      </button>
                    </div>
                  </form>
                )}

                {/* 4. ACTIVITY TIMELINE */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-[#6457E8]" />
                      <span className="text-xs font-bold text-[#11162A] tracking-tight">
                        Complaint Activity & Progress Timeline
                      </span>
                    </div>
                    <span className="text-xs text-[#65708B] font-mono">
                      {issue.timeline?.length || 1} Events
                    </span>
                  </div>

                  <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-[2px] before:bg-[#E4E7F1]">
                    {issue.timeline && issue.timeline.length > 0 ? (
                      issue.timeline.map((evt, idx) => (
                        <div key={evt.id || idx} className="relative text-xs">
                          <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-white border-2 border-[#6457E8]" />
                          <div className="flex items-center justify-between">
                            <span className="font-semibold text-[#11162A]">{evt.title}</span>
                            <span className="text-[11px] text-[#65708B]">
                              {new Date(evt.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <div className="text-[11px] text-[#65708B] mt-0.5">
                            By: <strong className="text-[#11162A]">{evt.actor}</strong>
                          </div>
                          {evt.description && (
                            <p className="mt-1 p-2 bg-[#F0F2F9] rounded-lg text-slate-700 text-xs">
                              {evt.description}
                            </p>
                          )}
                        </div>
                      ))
                    ) : (
                      <div className="relative text-xs">
                        <div className="absolute -left-6 top-1 w-3 h-3 rounded-full bg-white border-2 border-[#6457E8]" />
                        <div className="font-semibold text-[#11162A]">Complaint Filed</div>
                        <div className="text-[11px] text-[#65708B]">
                          {new Date(issue.timestamp).toLocaleString()}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Citizen Description & Visual Evidence */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                  <div className="text-xs font-semibold text-[#11162A]">
                    Citizen Complaint Statement
                  </div>
                  <p className="text-[#11162A] text-sm font-sans leading-relaxed">
                    {issue.complaintText || '(Patrol Automated Ingestion - No citizen narrative provided)'}
                  </p>
                  {issue.imageUrl ? (
                    <div className="mt-3 space-y-2.5">
                      <div className="flex items-center justify-between text-xs text-[#65708B]">
                        <span className="font-semibold flex items-center gap-1.5 text-[#11162A]">
                          <Eye className="w-3.5 h-3.5 text-[#6457E8]" />
                          <span>Visual Evidence & Bounding Box Localization</span>
                        </span>
                        <span className="text-[11px] font-mono text-[#6457E8] bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
                          {issue.visionModel || (isSanitationCategory ? 'YOLOv8s TACO Waste' : 'YOLOv8s RDD2022')}
                        </span>
                      </div>

                      <div className="relative rounded-xl overflow-hidden border border-[#212348] bg-[#10162A] flex items-center justify-center min-h-[220px]">
                        <img
                          src={issue.imageUrl.startsWith('/') || issue.imageUrl.startsWith('http') || issue.imageUrl.startsWith('blob:') ? issue.imageUrl : `/${issue.imageUrl}`}
                          alt="Incident Field Photo"
                          className="w-full max-h-72 object-contain"
                          onError={(e) => { (e.target as HTMLElement).style.display = 'none' }}
                        />

                        {/* Dynamic Bounding Box Overlays */}
                        {issue.detectedObjects && issue.detectedObjects.length > 0 ? (
                          issue.detectedObjects.map((obj, idx) => {
                            const [ymin, xmin, ymax, xmax] = obj.bbox || [0.25, 0.25, 0.75, 0.75]
                            const top = `${ymin * 100}%`
                            const left = `${xmin * 100}%`
                            const width = `${Math.max(6, (xmax - xmin) * 100)}%`
                            const height = `${Math.max(6, (ymax - ymin) * 100)}%`
                            return (
                              <div
                                key={idx}
                                style={{ top, left, width, height }}
                                className="absolute z-10 border-2 border-[#8B5CF6] bg-[#6457E8]/20 backdrop-blur-xs rounded-md shadow-lg pointer-events-none flex flex-col justify-between p-1"
                              >
                                <span className="text-[10px] bg-[#6457E8] text-white px-1.5 py-0.5 rounded font-semibold uppercase tracking-tight self-start truncate max-w-full">
                                  {obj.label}
                                </span>
                                <span className="text-[9px] bg-black/75 text-indigo-200 font-mono px-1 rounded self-end">
                                  {(obj.confidence * 100).toFixed(1)}%
                                </span>
                              </div>
                            )
                          })
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-4">
                            <div className="p-3 bg-black/70 border border-slate-700 rounded-lg text-center backdrop-blur-xs max-w-xs">
                              <span className="text-xs text-slate-200 font-semibold block">
                                No Civic Defect Detected
                              </span>
                              <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                                {issue.visionModel || 'YOLOv8'} Analyzed &bull; Clean surface or below threshold (0.15)
                              </span>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Optical Evidence Summary Strip */}
                      <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] space-y-2 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-[#65708B] font-medium">Model Runtime Status:</span>
                          <span className="font-mono text-[#11162A] font-semibold">
                            {issue.visionMode || (issue.detectedObjects?.length ? 'real_yolo_inference' : 'analyzed_no_detections')}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-[#65708B] font-medium">Visual Severity Component:</span>
                          <span className="font-mono font-semibold text-[#11162A]">
                            {issue.priorityBreakdown?.visualSeverity !== undefined 
                              ? `${Number(issue.priorityBreakdown.visualSeverity).toFixed(1)} / 20 pts`
                              : (issue.visualSeverity ? `${(issue.visualSeverity * 20).toFixed(1)} / 20 pts` : '0.0 / 20 pts (No defect detected)')}
                          </span>
                        </div>
                        {issue.detectedObjects && issue.detectedObjects.length > 0 && (
                          <div className="pt-1.5 border-t border-[#E4E7F1] flex flex-wrap gap-1.5 items-center">
                            <span className="text-[#65708B] text-[11px]">Detections:</span>
                            {issue.detectedObjects.map((d, i) => (
                              <span key={i} className="px-2 py-0.5 rounded bg-white border border-[#E4E7F1] text-[11px] font-mono text-[#11162A]">
                                {d.label} &bull; {(d.confidence * 100).toFixed(1)}%
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 italic">
                      No photographic evidence provided with this citizen report.
                    </div>
                  )}
                </div>

                {/* Explainable Dynamic Priority Gauge */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-2.5">
                  <div className="text-xs font-semibold text-[#11162A]">
                    Risk-Aware Dynamic Priority Assessment
                  </div>
                  <PriorityGauge
                    score={issue.priorityScore}
                    level={issue.priorityLevel}
                    breakdown={issue.priorityBreakdown}
                    reasoning={issue.priorityReasoning}
                    showDetails={true}
                  />
                </div>

                {/* Text-Image Evidence Consistency */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#11162A]">
                      Multimodal Cross-Validation
                    </span>
                    <ConsistencyBadge
                      level={issue.consistencyFlag || 'CONSISTENT'}
                      score={issue.evidenceConsistency}
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                    <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                      <div className="text-[#65708B] text-xs font-medium">Text Evidence (NLP)</div>
                      <div className="text-[#11162A] mt-1 font-sans text-xs">
                        {issue.consistencyDetail?.textEvidence || `Category classified as "${issue.category}"`}
                      </div>
                    </div>

                    <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                      <div className="text-[#65708B] text-xs font-medium">Computer Vision (YOLO)</div>
                      <div className="text-[#11162A] mt-1 font-sans text-xs">
                        {issue.visualDetection
                          ? `${issue.visualDetection}${issue.visualConfidence && !issue.visualDetection.includes('Confidence') && !issue.visualDetection.includes('conf') ? ` (${(issue.visualConfidence * 100).toFixed(1)}% conf)` : ''}`
                          : (issue.imageUrl ? 'No defect detected in image' : 'No imagery uploaded')}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Department Dispatch & Action Directive */}
                <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#11162A]">
                      Department Routing & Action Directive
                    </span>
                    <span className="text-[#6457E8] font-semibold text-xs font-mono">
                      SLA: {issue.slaHours} Hours
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-[#11162A] font-semibold text-sm">
                      <Building className="w-4 h-4 text-[#6457E8] shrink-0" />
                      <span>{issue.department}</span>
                    </div>
                    <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] text-[#11162A] font-sans text-xs">
                      <span className="text-[#6457E8] font-semibold text-xs block mb-1">
                        Recommended Action:
                      </span>
                      {issue.recommendedAction}
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 bg-white border-t border-[#E4E7F1] flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
                <div className="text-xs text-[#65708B] space-y-0.5">
                  <div>Coordinates: {issue.latitude.toFixed(4)}, {issue.longitude.toFixed(4)}</div>
                  <div className="text-[11px] text-[#65708B]">Ward: {issue.ward || 'Municipal Operations Area'}</div>
                </div>
                <button
                  onClick={onClose}
                  className="px-4 py-2 rounded-xl border border-[#E4E7F1] bg-[#F0F2F9] hover:bg-slate-200 text-xs font-semibold text-[#11162A] transition cursor-pointer"
                >
                  Close Panel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Official Specification Viewer Modal */}
      <GuidanceDocumentModal
        docId={selectedDocumentId}
        onClose={() => setSelectedDocumentId(null)}
      />
    </Portal>
  )
}
