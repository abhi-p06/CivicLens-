import React, { useState } from 'react'
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
} from 'lucide-react'
import { Issue, IssueStatus } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { api } from '../../services/api'
import { cn } from '../../lib/utils'

interface IssueDetailDrawerProps {
  issue: Issue | null
  onClose: () => void
  onUpdateIssue: (updated: Issue) => void
  onOpenResolutionModal: (issue: Issue) => void
}

export const IssueDetailDrawer: React.FC<IssueDetailDrawerProps> = ({
  issue,
  onClose,
  onUpdateIssue,
  onOpenResolutionModal,
}) => {
  const [updatingStatus, setUpdatingStatus] = useState(false)

  if (!issue) return null

  const lifecycleStages: IssueStatus[] = [
    'OPEN',
    'ANALYZED',
    'PRIORITIZED',
    'ASSIGNED',
    'ACTION IN PROGRESS',
    'VERIFICATION',
    'RESOLVED',
  ]

  const handleStatusChange = async (newStatus: IssueStatus) => {
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

  return (
    <div className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-2xl bg-[#0c1018] border-l border-[#1a2130] h-full flex flex-col shadow-2xl font-mono text-xs overflow-hidden animate-in slide-in-from-right duration-200">
        {/* Header */}
        <div className="px-5 py-4 border-b border-[#1a2130] bg-[#0e131d] flex items-center justify-between shrink-0">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold text-cyan-400">{issue.issueId}</span>
              <StatusBadge status={issue.status} />
              {issue.isDuplicate && (
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-amber-950/60 border border-amber-800 text-amber-300">
                  DUPLICATE ({issue.duplicateGroupId})
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-3">
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3 text-slate-500" />
                {issue.location} ({issue.ward})
              </span>
              <span>&bull;</span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3 text-slate-500" />
                {new Date(issue.timestamp).toLocaleString()}
              </span>
            </div>
          </div>

          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Lifecycle Action Bar */}
          <div className="p-3 bg-[#111622] border border-slate-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">
                Civic Lifecycle Workflow
              </span>
              <span className="text-[10px] text-cyan-400 font-bold">
                Current: {issue.status}
              </span>
            </div>
            <div className="flex items-center gap-1 overflow-x-auto pb-1">
              {lifecycleStages.map((st) => {
                const isActive = issue.status === st
                return (
                  <button
                    key={st}
                    disabled={updatingStatus}
                    onClick={() => handleStatusChange(st)}
                    className={cn(
                      'px-2 py-1 rounded text-[10px] uppercase transition border whitespace-nowrap',
                      isActive
                        ? 'bg-cyan-950 border-cyan-600 text-cyan-300 font-bold shadow'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    )}
                  >
                    {st}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Citizen Description */}
          <div className="p-3.5 bg-[#111724] border border-slate-800/90 rounded-lg space-y-1.5">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              Citizen Complaint Statement
            </div>
            <p className="text-slate-200 text-xs font-sans leading-relaxed">
              {issue.complaintText || '(Patrol Automated Ingestion - No citizen narrative provided)'}
            </p>
          </div>

          {/* Explainable Dynamic Priority Gauge (Feature 15) */}
          <div className="p-3.5 bg-[#111724] border border-slate-800 rounded-lg space-y-2">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              Feature 15: Risk-Aware Dynamic Priority Engine
            </div>
            <PriorityGauge
              score={issue.priorityScore}
              level={issue.priorityLevel}
              breakdown={issue.priorityBreakdown}
              reasoning={issue.priorityReasoning}
              showDetails={true}
            />
          </div>

          {/* Text-Image Evidence Consistency (Feature 18) */}
          <div className="p-3.5 bg-[#111724] border border-slate-800 rounded-lg space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">
                Feature 18: Multimodal Cross-Validation
              </span>
              <ConsistencyBadge
                level={issue.consistencyFlag || 'CONSISTENT'}
                score={issue.evidenceConsistency}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 bg-[#0a0d14] rounded border border-slate-800/80">
                <div className="text-slate-400 text-[10px]">NLP TEXT EVIDENCE</div>
                <div className="text-slate-200 mt-1 font-sans">
                  {issue.consistencyDetail?.textEvidence || `Category classified as "${issue.category}"`}
                </div>
              </div>

              <div className="p-2.5 bg-[#0a0d14] rounded border border-slate-800/80">
                <div className="text-slate-400 text-[10px]">COMPUTER VISION EVIDENCE</div>
                <div className="text-slate-200 mt-1 font-sans">
                  {issue.visualDetection
                    ? `${issue.visualDetection} (${((issue.visualConfidence || 0.9) * 100).toFixed(0)}% conf)`
                    : 'No imagery uploaded'}
                </div>
              </div>
            </div>

            {issue.consistencyDetail?.reason && (
              <div className="text-[11px] text-slate-400 font-sans leading-relaxed border-t border-slate-800/60 pt-1.5">
                {issue.consistencyDetail.reason}
              </div>
            )}
          </div>

          {/* Department Dispatch & Action Directive (Feature 19) */}
          <div className="p-3.5 bg-[#111724] border border-slate-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-bold text-slate-400">
                Feature 19: Department Routing & Action Directive
              </span>
              <span className="text-cyan-400 font-bold text-[10px]">
                SLA: {issue.slaHours} Hours
              </span>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center gap-2 text-slate-200 font-bold text-xs">
                <Building className="w-4 h-4 text-cyan-400 shrink-0" />
                <span>{issue.department}</span>
              </div>
              <div className="p-2 bg-[#0a0d14] rounded border border-slate-800 text-slate-300 font-sans text-xs">
                <strong className="text-cyan-300 font-mono text-[10px] block mb-0.5">
                  RECOMMENDED ACTION:
                </strong>
                {issue.recommendedAction}
              </div>
            </div>
          </div>

          {/* Spatiotemporal Context (Features 16 & 17) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Feature 16: Hotspot */}
            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg space-y-1.5">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase">
                <Flame className="w-3.5 h-3.5 text-rose-400" />
                <span>Feature 16: Hotspot Status</span>
              </div>
              {issue.isHotspot ? (
                <div>
                  <div className="text-rose-400 font-bold text-xs">
                    {issue.hotspotClusterId || 'ACTIVE HOTSPOT'}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    DBSCAN radius 500m &bull; High Issue Concentration
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-xs mt-1">
                  Isolated incident (Below DBSCAN clustering threshold)
                </div>
              )}
            </div>

            {/* Feature 17: Recurrence */}
            <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg space-y-1.5">
              <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase">
                <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
                <span>Feature 17: Recurrence</span>
              </div>
              {issue.recurringDetail?.recurringIssue ? (
                <div>
                  <div className="text-amber-400 font-bold text-xs">
                    RECURRING DEFECT ({issue.recurringDetail.reportCount} reports)
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">
                    Trend: <strong className="text-slate-200">{issue.recurringDetail.trend}</strong> &bull; Score: {(issue.recurringDetail.recurrenceScore * 100).toFixed(0)}%
                  </div>
                </div>
              ) : (
                <div className="text-slate-400 text-xs mt-1">
                  First recorded occurrence at this geo-hash
                </div>
              )}
            </div>
          </div>

          {/* Resolution Evidence (Feature 20) */}
          {issue.resolutionEvidence && (
            <div className="p-3.5 bg-emerald-950/30 border border-emerald-800 rounded-lg space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Feature 20: Resolution Verified</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-700 text-emerald-300 text-[10px]">
                  {issue.resolutionEvidence.resolutionStatus}
                </span>
              </div>
              <div className="text-slate-300 text-[11px] font-sans">
                {issue.resolutionEvidence.verificationSummary}
              </div>
              <div className="text-[10px] text-emerald-400 font-mono">
                Confidence: {(issue.resolutionEvidence.resolutionConfidence * 100).toFixed(1)}% &bull; Verified: {new Date(issue.resolutionEvidence.verifiedAt).toLocaleTimeString()}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-5 py-3.5 bg-[#0a0d14] border-t border-[#1a2130] flex items-center justify-between shrink-0">
          <div className="text-[11px] text-slate-500">
            Coordinates: {issue.latitude.toFixed(4)}, {issue.longitude.toFixed(4)}
          </div>
          <button
            onClick={() => onOpenResolutionModal(issue)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-semibold transition shadow-lg shadow-emerald-950/40"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Verify Field Resolution</span>
          </button>
        </div>
      </div>
    </div>
  )
}
