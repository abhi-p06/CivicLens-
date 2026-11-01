import React, { useState } from 'react'
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
} from 'lucide-react'
import { Issue, IssueStatus } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { api } from '../../services/api'
import { cn } from '../../lib/utils'
import { Portal } from '../common/Portal'
import { useAuth } from '../../context/AuthContext'

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
              {(() => {
                const group = issue.duplicateGroup || issue.duplicateGroupId
                const count = issue.nearDuplicateCount ?? 0
                if (issue.isDuplicate) {
                  return (
                    <span className="px-2.5 py-0.5 rounded-full text-xs bg-amber-500/10 border border-amber-500/25 text-amber-700 font-medium inline-flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                      <span>Confirmed Duplicate {group ? `(${group})` : ''}</span>
                      {count > 0 && <span className="text-amber-600/80">&bull; {count} related {count === 1 ? 'report' : 'reports'}</span>}
                    </span>
                  )
                }
                if (count > 0) {
                  return (
                    <span className="px-2.5 py-0.5 rounded-full text-xs bg-indigo-50 border border-indigo-200 text-indigo-700 font-medium inline-flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#6457E8]" />
                      <span>{count} related {count === 1 ? 'report' : 'reports'}</span>
                    </span>
                  )
                }
                return (
                  <span className="px-2.5 py-0.5 rounded-full text-xs bg-slate-100 border border-slate-200 text-slate-500 font-medium inline-flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                    <span>No duplicates found</span>
                  </span>
                )
              })()}
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
                <span>Open Dossier</span>
              </button>
            )}
            <button onClick={onClose} className="text-[#65708B] hover:text-[#11162A] p-1.5 rounded-lg hover:bg-black/5 transition cursor-pointer">
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-[#F6F7FC]">
          {/* Lifecycle Action Bar */}
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#11162A]">
                Civic Lifecycle Workflow
              </span>
              <span className="text-xs text-[#6457E8] font-semibold">
                Current: {issue.status}
              </span>
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
              {lifecycleStages.map((st) => {
                const isActive = issue.status === st
                return (
                  <button
                    key={st}
                    disabled={updatingStatus}
                    onClick={() => handleStatusChange(st)}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-xs font-medium transition border whitespace-nowrap cursor-pointer',
                      isActive
                        ? 'bg-[#6457E8] border-[#6457E8] text-white font-semibold shadow-xs'
                        : 'bg-[#F0F2F9] border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-200/60'
                    )}
                  >
                    {st.replace(/_/g, ' ')}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Citizen Description & Visual Evidence */}
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-3">
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
                    {issue.visionModel || (issue.category === 'Sanitation & Garbage' ? 'YOLOv8s TACO Waste' : 'YOLOv8s RDD2022')}
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
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2.5">
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
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-3">
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

            {issue.consistencyDetail?.reason && (
              <div className="text-xs text-[#65708B] font-sans leading-relaxed border-t border-[#E4E7F1] pt-2">
                {issue.consistencyDetail.reason}
              </div>
            )}
          </div>

          {/* Department Dispatch & Action Directive */}
          <div className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2.5">
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

          {/* Spatiotemporal Context */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Feature 16: Hotspot */}
            <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#11162A]">
                <Flame className="w-4 h-4 text-[#EF4444]" />
                <span>Hotspot Status</span>
              </div>
              {issue.isHotspot ? (
                <div>
                  <div className="text-[#EF4444] font-semibold text-xs">
                    {issue.hotspotClusterId || 'Active Hotspot'}
                  </div>
                  <div className="text-xs text-[#65708B] mt-1">
                    DBSCAN radius 500m &bull; High Issue Concentration
                  </div>
                </div>
              ) : (
                <div className="text-[#65708B] text-xs mt-1">
                  Isolated incident (Below DBSCAN clustering threshold)
                </div>
              )}
            </div>

            {/* Feature 17: Recurrence */}
            <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-[#11162A]">
                <RotateCcw className="w-4 h-4 text-[#F97316]" />
                <span>Recurrence History</span>
              </div>
              {issue.recurringDetail?.recurringIssue ? (
                <div>
                  <div className="text-[#F97316] font-semibold text-xs">
                    RECURRING DEFECT ({issue.recurringDetail.reportCount} reports)
                  </div>
                  <div className="text-xs text-[#65708B] mt-1">
                    Trend: <strong className="text-[#11162A]">{issue.recurringDetail.trend}</strong> &bull; Score: {(issue.recurringDetail.recurrenceScore * 100).toFixed(0)}%
                  </div>
                </div>
              ) : (
                <div className="text-[#65708B] text-xs mt-1">
                  First recorded occurrence at this geo-hash
                </div>
              )}
            </div>
          </div>

          {/* Resolution Evidence */}
          {issue.resolutionEvidence && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-emerald-700 font-bold text-xs">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Closure Summary</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-100 border border-emerald-300 text-emerald-800 text-[10px] font-medium">
                  {issue.resolutionEvidence.resolutionStatus}
                </span>
              </div>
              <div className="text-emerald-950 text-xs font-sans">
                {issue.resolutionEvidence.verificationSummary}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
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
  </Portal>
)
}
