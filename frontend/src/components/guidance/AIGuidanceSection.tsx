import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  RotateCcw,
  Check,
  Edit2,
  X,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileText,
  Wrench,
  CheckSquare,
  AlertCircle,
  HelpCircle,
  BookOpen,
  ArrowRight,
  Info
} from 'lucide-react'
import {
  Issue,
  FieldGuidance,
  GuidanceActionItem,
  GuidanceCitation,
  OfficerDecisionType
} from '../../types'
import { api } from '../../services/api'
import { Portal } from '../common/Portal'

interface AIGuidanceSectionProps {
  issue: Issue
  onIssueUpdated: (updated: Issue) => void
  onOpenDocument: (docId: string) => void
}

export const AIGuidanceSection: React.FC<AIGuidanceSectionProps> = ({
  issue,
  onIssueUpdated,
  onOpenDocument,
}) => {
  const [guidance, setGuidance] = useState<FieldGuidance | null>(null)
  const [loading, setLoading] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isExpanded, setIsExpanded] = useState(true)

  // Edit Suggestion Modal State
  const [editingItem, setEditingItem] = useState<GuidanceActionItem | null>(null)
  const [editText, setEditText] = useState('')
  const [savingEdit, setSavingEdit] = useState(false)

  // Dismiss Modal State
  const [dismissingItem, setDismissingItem] = useState<GuidanceActionItem | null>(null)
  const [dismissReason, setDismissReason] = useState('')
  const [savingDismiss, setSavingDismiss] = useState(false)

  // Action in-flight tracking
  const [actionInProgressId, setActionInProgressId] = useState<string | null>(null)

  // Load guidance on issue mount or change
  useEffect(() => {
    let isMounted = true
    setLoading(true)
    setError(null)

    api.getFieldGuidance(issue.issueId, false)
      .then((data) => {
        if (isMounted) setGuidance(data)
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to retrieve AI field guidance.')
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [issue.issueId])

  // Handle Regenerate
  const handleRegenerate = async () => {
    setRegenerating(true)
    setError(null)
    try {
      const refreshed = await api.regenerateFieldGuidance(issue.issueId)
      setGuidance(refreshed)
      // Refetch issue to update timeline / metadata
      const updatedIssue = await api.getIssue(issue.issueId)
      onIssueUpdated(updatedIssue)
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate field guidance.')
    } finally {
      setRegenerating(false)
    }
  }

  // Handle Quick Accept (Use Suggestion)
  const handleUseSuggestion = async (item: GuidanceActionItem) => {
    setActionInProgressId(item.id)
    try {
      const updatedGuidance = await api.recordGuidanceDecision(issue.issueId, {
        item_id: item.id,
        decision: 'ACCEPTED',
      })
      setGuidance(updatedGuidance)
      const updatedIssue = await api.getIssue(issue.issueId)
      onIssueUpdated(updatedIssue)
    } catch (err: any) {
      setError(err.message || 'Failed to accept guidance suggestion.')
    } finally {
      setActionInProgressId(null)
    }
  }

  // Handle Edit Submit
  const handleSaveEdit = async () => {
    if (!editingItem || !editText.trim()) return
    setSavingEdit(true)
    try {
      const updatedGuidance = await api.recordGuidanceDecision(issue.issueId, {
        item_id: editingItem.id,
        decision: 'EDITED',
        edited_text: editText.trim(),
      })
      setGuidance(updatedGuidance)
      const updatedIssue = await api.getIssue(issue.issueId)
      onIssueUpdated(updatedIssue)
      setEditingItem(null)
      setEditText('')
    } catch (err: any) {
      setError(err.message || 'Failed to save edited guidance.')
    } finally {
      setSavingEdit(false)
    }
  }

  // Handle Dismiss Submit
  const handleSaveDismiss = async () => {
    if (!dismissingItem) return
    setSavingDismiss(true)
    try {
      const updatedGuidance = await api.recordGuidanceDecision(issue.issueId, {
        item_id: dismissingItem.id,
        decision: 'DISMISSED',
        reason: dismissReason.trim() || undefined,
      })
      setGuidance(updatedGuidance)
      const updatedIssue = await api.getIssue(issue.issueId)
      onIssueUpdated(updatedIssue)
      setDismissingItem(null)
      setDismissReason('')
    } catch (err: any) {
      setError(err.message || 'Failed to dismiss guidance suggestion.')
    } finally {
      setSavingDismiss(false)
    }
  }

  return (
    <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-4 text-xs font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-xl bg-gradient-to-br from-[#6457E8]/15 to-[#8B5CF6]/15 text-[#6457E8] border border-[#6457E8]/20">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#11162A] tracking-tight">
                AI Field Guidance
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#6457E8]/10 text-[#6457E8] border border-[#6457E8]/20">
                Statutory Standards
              </span>
            </div>
            <span className="text-[11px] text-[#65708B] block mt-0.5">
              Grounded recommendations synthesized from official government specifications
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRegenerate}
            disabled={regenerating || loading}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-[#F0F2F9] hover:bg-[#6457E8] hover:text-white text-[#11162A] border border-[#E4E7F1] rounded-lg text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            title="Re-synthesize guidance from latest indexed specifications"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
            <span>{regenerating ? 'Regenerating...' : 'Regenerate'}</span>
          </button>

          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-[#65708B] hover:text-[#11162A] hover:bg-black/5 rounded-lg transition cursor-pointer"
          >
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="py-8 text-center text-[#65708B] space-y-2">
          <div className="inline-block w-5 h-5 border-2 border-[#6457E8] border-t-transparent rounded-full animate-spin" />
          <p className="text-xs">Analyzing complaint context and retrieving government guidelines...</p>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-rose-600 hover:text-rose-800"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Guidance Content */}
      {!loading && guidance && isExpanded && (
        <div className="space-y-4">
          {/* 1. Insufficient Sources / Fallback Banner */}
          {guidance.has_insufficient_sources && (
            <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start gap-2.5">
              <HelpCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-xs block">Technical Review Required</span>
                <p className="text-xs">
                  {guidance.fallback_message || 'Insufficient verified guidance available. Manual technical review is recommended.'}
                </p>
              </div>
            </div>
          )}

          {/* 2. Mandatory Hazardous / Biomedical Escalation Alert */}
          {guidance.is_hazardous_escalation && guidance.escalation_notice && (
            <div className="p-4 bg-rose-50 border-2 border-rose-400 rounded-xl text-rose-950 space-y-2 shadow-xs">
              <div className="flex items-center gap-2 text-rose-700 font-bold text-xs">
                <ShieldAlert className="w-5 h-5 text-rose-600 animate-pulse" />
                <span className="tracking-wide uppercase">Urgent Hazardous / Bio-Medical Protocol Active</span>
              </div>
              <p className="text-xs font-semibold leading-relaxed">
                {guidance.escalation_notice}
              </p>
              <div className="flex items-center gap-2 pt-1 text-[11px] text-rose-800">
                <span className="font-semibold">Reference:</span>
                <button
                  type="button"
                  onClick={() => onOpenDocument('DOC-MPCB-HAZ-2016')}
                  className="underline hover:text-rose-950 cursor-pointer font-medium"
                >
                  MPCB Bio-Medical & Hazardous Waste Escalation Directive (Protocol 4.2)
                </button>
              </div>
            </div>
          )}

          {/* 3. Conflicting Sources Callout */}
          {guidance.disagreements && guidance.disagreements.length > 0 && (
            <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl text-amber-950 space-y-2">
              <div className="flex items-center gap-2 text-amber-800 font-bold text-xs">
                <AlertTriangle className="w-4 h-4 text-amber-600" />
                <span>Conflicting Specification Analysis</span>
              </div>
              {guidance.disagreements.map((dis, idx) => (
                <div key={idx} className="space-y-1.5 text-xs">
                  <div className="font-semibold text-amber-900">{dis.topic}</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2 bg-white/80 rounded-lg border border-amber-200/60">
                      <strong className="block text-slate-800">{dis.source_a}</strong>
                      <span className="text-slate-600">{dis.position_a}</span>
                    </div>
                    <div className="p-2 bg-white/80 rounded-lg border border-amber-200/60">
                      <strong className="block text-slate-800">{dis.source_b}</strong>
                      <span className="text-slate-600">{dis.position_b}</span>
                    </div>
                  </div>
                  <div className="p-2 bg-amber-100/70 rounded-lg text-[11px] text-amber-900 font-medium">
                    <strong>Recommended Reconciliation:</strong> {dis.recommended_reconciliation}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 4. Situation Summary & Rationale */}
          <div className="p-3.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-2">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#65708B] block mb-1">
                Complaint Situation Summary
              </span>
              <p className="text-[#11162A] leading-relaxed font-medium">
                {guidance.situation_summary}
              </p>
            </div>
            <div className="pt-2 border-t border-[#E4E7F1]/80">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[#65708B] block mb-1">
                Technical Recommendation Rationale
              </span>
              <p className="text-[#65708B] leading-relaxed">
                {guidance.recommendation_rationale}
              </p>
            </div>
          </div>

          {/* 5. Immediate Safety Considerations */}
          {guidance.immediate_precautions && guidance.immediate_precautions.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-amber-600" />
                <span className="text-xs font-bold text-[#11162A] uppercase tracking-wider">
                  Immediate Safety Considerations ({guidance.immediate_precautions.length})
                </span>
              </div>

              <div className="space-y-2.5">
                {guidance.immediate_precautions.map((item) => (
                  <GuidanceItemCard
                    key={item.id}
                    item={item}
                    isBusy={actionInProgressId === item.id}
                    onUse={() => handleUseSuggestion(item)}
                    onEdit={() => {
                      setEditingItem(item)
                      setEditText(item.edited_text || `${item.title}: ${item.description}`)
                    }}
                    onDismiss={() => {
                      setDismissingItem(item)
                      setDismissReason('')
                    }}
                    onOpenDocument={onOpenDocument}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 6. Recommended Field Actions */}
          {guidance.recommended_field_actions && guidance.recommended_field_actions.length > 0 && (
            <div className="space-y-2.5">
              <div className="flex items-center gap-1.5">
                <CheckSquare className="w-4 h-4 text-[#6457E8]" />
                <span className="text-xs font-bold text-[#11162A] uppercase tracking-wider">
                  Recommended Field Actions ({guidance.recommended_field_actions.length})
                </span>
              </div>

              <div className="space-y-2.5">
                {guidance.recommended_field_actions.map((item) => (
                  <GuidanceItemCard
                    key={item.id}
                    item={item}
                    isBusy={actionInProgressId === item.id}
                    onUse={() => handleUseSuggestion(item)}
                    onEdit={() => {
                      setEditingItem(item)
                      setEditText(item.edited_text || `${item.title}: ${item.description}`)
                    }}
                    onDismiss={() => {
                      setDismissingItem(item)
                      setDismissReason('')
                    }}
                    onOpenDocument={onOpenDocument}
                  />
                ))}
              </div>
            </div>
          )}

          {/* 7. Equipment, Handling Precautions & Completion Checklist Strip */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Equipment & Resources */}
            {guidance.equipment_and_resources && guidance.equipment_and_resources.length > 0 && (
              <div className="p-3 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-2">
                <span className="text-[11px] font-bold text-[#11162A] uppercase tracking-wider block">
                  Equipment & Resources Required
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {guidance.equipment_and_resources.map((eq, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md text-[11px] bg-white border border-[#E4E7F1] text-slate-700 shadow-2xs"
                    >
                      {eq}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Handling Precautions */}
            {guidance.handling_precautions && guidance.handling_precautions.length > 0 && (
              <div className="p-3 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-2">
                <span className="text-[11px] font-bold text-[#11162A] uppercase tracking-wider block">
                  Mandatory Handling Precautions
                </span>
                <ul className="space-y-1 text-[11px] text-slate-700 list-disc list-inside">
                  {guidance.handling_precautions.map((prec, i) => (
                    <li key={i}>{prec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* 8. Completion Documentation Checklist */}
          {guidance.completion_checklist && guidance.completion_checklist.length > 0 && (
            <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl space-y-2.5">
              <span className="text-[11px] font-bold text-[#11162A] uppercase tracking-wider block">
                Statutory Completion Documentation Checklist
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                {guidance.completion_checklist.map((chk, i) => (
                  <div
                    key={i}
                    className="p-2 rounded-lg bg-[#F6F7FC] border border-[#E4E7F1] flex items-center justify-between gap-2"
                  >
                    <span className="text-slate-800 font-medium">{chk.item}</span>
                    {chk.statutory && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#6457E8]/10 text-[#6457E8] shrink-0">
                        Statutory
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 9. Retrieved Government References */}
          {guidance.retrieved_references && guidance.retrieved_references.length > 0 && (
            <div className="p-3.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-2">
              <span className="text-[11px] font-bold text-[#11162A] uppercase tracking-wider block">
                Retrieved Government References ({guidance.retrieved_references.length})
              </span>
              <div className="space-y-1.5">
                {guidance.retrieved_references.map((ref, idx) => (
                  <div
                    key={idx}
                    className="p-2 bg-white rounded-lg border border-[#E4E7F1] flex items-center justify-between gap-3 text-[11px]"
                  >
                    <div className="space-y-0.5 min-w-0">
                      <strong className="text-[#11162A] block truncate">{ref.doc_title}</strong>
                      <span className="text-[#65708B] block truncate">
                        {ref.source_org} &bull; {ref.section}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => onOpenDocument(ref.doc_id)}
                      className="flex items-center gap-1 px-2 py-1 rounded bg-[#F0F2F9] hover:bg-[#6457E8] hover:text-white text-[#11162A] font-semibold transition shrink-0 cursor-pointer"
                    >
                      <BookOpen className="w-3 h-3" />
                      <span>View Source</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 10. Engineering Disclaimer */}
          {guidance.engineering_disclaimer && (
            <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-500 italic text-center">
              {guidance.engineering_disclaimer}
            </div>
          )}
        </div>
      )}

      {/* Edit Suggestion Modal */}
      {editingItem && (
        <Portal>
          <div className="fixed inset-0 z-[9100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
            <div className="w-full max-w-lg bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl p-5 space-y-4 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-[#E4E7F1]">
                <div className="flex items-center gap-2">
                  <Edit2 className="w-4 h-4 text-[#6457E8]" />
                  <span className="font-bold text-sm text-[#11162A]">Edit Field Guidance Instruction</span>
                </div>
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="text-slate-400 hover:text-slate-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-[#65708B] block mb-1">
                  Customized Instruction for Team / Timeline:
                </label>
                <textarea
                  rows={4}
                  value={editText}
                  onChange={(e) => setEditText(e.target.value)}
                  className="w-full bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] font-sans"
                  placeholder="Enter customized recommendation..."
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#E4E7F1]">
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="px-3 py-1.5 bg-[#F0F2F9] text-slate-700 font-semibold rounded-lg hover:bg-slate-200 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveEdit}
                  disabled={savingEdit || !editText.trim()}
                  className="px-4 py-1.5 bg-[#6457E8] text-white font-semibold rounded-lg hover:bg-[#5145CF] transition cursor-pointer disabled:opacity-50"
                >
                  {savingEdit ? 'Saving...' : 'Apply Customized Instruction'}
                </button>
              </div>
            </div>
          </div>
        </Portal>
      )}

      {/* Dismiss Reason Modal */}
      {dismissingItem && (
        <Portal>
          <div className="fixed inset-0 z-[9100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
            <div className="w-full max-w-md bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl p-5 space-y-4 text-xs">
              <div className="flex items-center justify-between pb-2 border-b border-[#E4E7F1]">
                <div className="flex items-center gap-2">
                  <X className="w-4 h-4 text-rose-600" />
                  <span className="font-bold text-sm text-[#11162A]">Dismiss Field Recommendation</span>
                </div>
                <button
                  type="button"
                  onClick={() => setDismissingItem(null)}
                  className="text-slate-400 hover:text-slate-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <p className="text-slate-600">
                You are dismissing recommendation: <strong>{dismissingItem.title}</strong>. Please provide an optional technical reason:
              </p>

              <div>
                <input
                  type="text"
                  value={dismissReason}
                  onChange={(e) => setDismissReason(e.target.value)}
                  placeholder="e.g. Dry weather prevailing, alternative machinery deployed..."
                  className="w-full bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-rose-500 font-sans"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-[#E4E7F1]">
                <button
                  type="button"
                  onClick={() => setDismissingItem(null)}
                  className="px-3 py-1.5 bg-[#F0F2F9] text-slate-700 font-semibold rounded-lg hover:bg-slate-200 transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveDismiss}
                  disabled={savingDismiss}
                  className="px-4 py-1.5 bg-rose-600 text-white font-semibold rounded-lg hover:bg-rose-700 transition cursor-pointer disabled:opacity-50"
                >
                  {savingDismiss ? 'Dismissing...' : 'Confirm Dismissal'}
                </button>
              </div>
            </div>
          </div>
        </Portal>
      )}
    </div>
  )
}

interface GuidanceItemCardProps {
  item: GuidanceActionItem
  isBusy: boolean
  onUse: () => void
  onEdit: () => void
  onDismiss: () => void
  onOpenDocument: (docId: string) => void
}

const GuidanceItemCard: React.FC<GuidanceItemCardProps> = ({
  item,
  isBusy,
  onUse,
  onEdit,
  onDismiss,
  onOpenDocument,
}) => {
  const isAccepted = item.officer_decision === 'ACCEPTED'
  const isEdited = item.officer_decision === 'EDITED'
  const isDismissed = item.officer_decision === 'DISMISSED'

  return (
    <div
      className={`p-3.5 rounded-xl border transition space-y-2.5 ${
        isAccepted
          ? 'bg-emerald-50/40 border-emerald-300'
          : isEdited
          ? 'bg-violet-50/40 border-violet-300'
          : isDismissed
          ? 'bg-slate-50/70 border-slate-200 opacity-60'
          : 'bg-white border-[#E4E7F1] hover:border-[#6457E8]/40 shadow-2xs'
      }`}
    >
      {/* Title & Status Strip */}
      <div className="flex items-start justify-between gap-2">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h4 className="font-bold text-[#11162A] text-xs">{item.title}</h4>
            {item.is_requirement && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                Statutory
              </span>
            )}
          </div>
          <p className="text-slate-600 text-[11.5px] leading-relaxed">
            {item.description}
          </p>
        </div>

        {/* Decision Badge */}
        {isAccepted && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 shrink-0 flex items-center gap-1">
            <Check className="w-3 h-3" />
            <span>Adopted</span>
          </span>
        )}
        {isEdited && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-100 text-violet-800 shrink-0 flex items-center gap-1">
            <Edit2 className="w-3 h-3" />
            <span>Customized</span>
          </span>
        )}
        {isDismissed && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-200 text-slate-700 shrink-0 flex items-center gap-1">
            <X className="w-3 h-3" />
            <span>Dismissed</span>
          </span>
        )}
      </div>

      {/* Steps List */}
      {item.steps && item.steps.length > 0 && (
        <div className="p-2.5 bg-[#F6F7FC] rounded-lg space-y-1">
          <span className="text-[10.5px] font-bold uppercase tracking-wider text-[#65708B] block">
            Execution Steps:
          </span>
          <ul className="space-y-1 text-[11px] text-slate-700 list-disc list-inside">
            {item.steps.map((st, i) => (
              <li key={i}>{st}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Equipment Badges */}
      {item.equipment && item.equipment.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 text-[10.5px]">
          <span className="text-[#65708B] font-medium mr-1">Equipment:</span>
          {item.equipment.map((eq, i) => (
            <span
              key={i}
              className="px-2 py-0.5 rounded bg-white border border-[#E4E7F1] text-slate-700 shadow-2xs"
            >
              {eq}
            </span>
          ))}
        </div>
      )}

      {/* Citation Reference & Officer Action Buttons */}
      <div className="pt-2 border-t border-[#E4E7F1] flex flex-wrap items-center justify-between gap-2 text-[11px]">
        {item.citation ? (
          <button
            type="button"
            onClick={() => onOpenDocument(item.citation.doc_id)}
            className="flex items-center gap-1 text-[#6457E8] hover:text-[#5145CF] font-semibold cursor-pointer underline text-[11px]"
          >
            <BookOpen className="w-3 h-3" />
            <span>
              {item.citation.source_org} &bull; {item.citation.section}
            </span>
          </button>
        ) : (
          <span className="text-slate-400">Official Specification</span>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-1.5 ml-auto">
          {!isAccepted && (
            <button
              type="button"
              onClick={onUse}
              disabled={isBusy}
              className="flex items-center gap-1 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg transition shadow-2xs cursor-pointer disabled:opacity-50"
              title="Adopt suggestion into task instructions and activity timeline"
            >
              <Check className="w-3 h-3" />
              <span>Use Suggestion</span>
            </button>
          )}

          {!isDismissed && (
            <button
              type="button"
              onClick={onEdit}
              disabled={isBusy}
              className="flex items-center gap-1 px-2.5 py-1 bg-white hover:bg-[#F0F2F9] text-[#11162A] border border-[#E4E7F1] font-semibold rounded-lg transition shadow-2xs cursor-pointer disabled:opacity-50"
              title="Customize recommendation text before adopting"
            >
              <Edit2 className="w-3 h-3 text-[#6457E8]" />
              <span>Edit</span>
            </button>
          )}

          {!isDismissed && !isAccepted && (
            <button
              type="button"
              onClick={onDismiss}
              disabled={isBusy}
              className="flex items-center gap-1 px-2 py-1 bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 font-semibold rounded-lg transition shadow-2xs cursor-pointer disabled:opacity-50"
              title="Dismiss suggestion for this issue"
            >
              <X className="w-3 h-3" />
              <span>Dismiss</span>
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
