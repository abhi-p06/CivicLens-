import React, { useState } from 'react'
import {
  Sparkles,
  MapPin,
  Calendar,
  Building,
  CheckCircle2,
  Clock,
  Eye,
  FileText,
  ShieldCheck,
  ArrowRight,
  Camera,
  Layers,
  ChevronDown,
} from 'lucide-react'
import { Issue, IssueStatus } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { api } from '../../services/api'
import { cn } from '../../lib/utils'

interface IssueIntelligenceViewProps {
  issues: Issue[]
  selectedIssue: Issue | null
  onSelectIssue: (issue: Issue) => void
  onUpdateIssue: (updated: Issue) => void
  onOpenResolutionModal: (issue: Issue) => void
}

export const IssueIntelligenceView: React.FC<IssueIntelligenceViewProps> = ({
  issues,
  selectedIssue,
  onSelectIssue,
  onUpdateIssue,
  onOpenResolutionModal,
}) => {
  const current = selectedIssue || issues[0] || null
  const [advancing, setAdvancing] = useState(false)

  if (!current) {
    return (
      <div className="h-full flex items-center justify-center p-8 font-mono text-xs text-slate-500">
        No issues available for intelligence inspection.
      </div>
    )
  }

  const lifecycleStages: IssueStatus[] = [
    'OPEN',
    'ANALYZED',
    'PRIORITIZED',
    'ASSIGNED',
    'ACTION IN PROGRESS',
    'VERIFICATION',
    'RESOLVED',
  ]

  const handleAdvanceStatus = async (st: IssueStatus) => {
    setAdvancing(true)
    try {
      const updated = await api.updateStatus(current.issueId, st, `Status updated to ${st}`)
      onUpdateIssue(updated)
    } catch (err) {
      console.error(err)
    } finally {
      setAdvancing(false)
    }
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-5 font-sans text-xs bg-[#F6F7FC]">
      {/* Top Header & Issue Selector */}
      <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-50 border border-indigo-200 text-[#6457E8]">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-[#65708B] font-semibold">
              Issue Intelligence Dossier
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-lg font-bold text-[#11162A] font-mono">{current.issueId}</span>
              <StatusBadge status={current.status} />
              <ConsistencyBadge level={current.consistencyFlag || 'CONSISTENT'} />
            </div>
          </div>
        </div>

        {/* Dropdown selector to switch between issues */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#65708B]">Select Issue:</span>
          <select
            value={current.issueId}
            onChange={(e) => {
              const found = issues.find((i) => i.issueId === e.target.value)
              if (found) onSelectIssue(found)
            }}
            className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-lg px-3 py-1.5 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
          >
            {issues.map((i) => (
              <option key={i.issueId} value={i.issueId}>
                {i.issueId} &bull; {i.category} ({i.location})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Overview Metadata Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">STATUS</div>
          <div className="font-bold text-[#6457E8] text-xs mt-1 truncate">{current.status}</div>
        </div>

        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">CATEGORY</div>
          <div className="font-bold text-[#11162A] text-xs mt-1 truncate">{current.category}</div>
        </div>

        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">LOCATION</div>
          <div className="font-bold text-[#11162A] text-xs mt-1 truncate">{current.location}</div>
        </div>

        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">WARD</div>
          <div className="font-bold text-[#11162A] text-xs mt-1 truncate">{current.ward}</div>
        </div>

        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">DATE INGESTED</div>
          <div className="font-bold text-[#11162A] text-xs mt-1 truncate">
            {new Date(current.timestamp).toLocaleDateString()}
          </div>
        </div>

        <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-xl shadow-xs">
          <div className="text-[#65708B] text-xs font-semibold">PRIORITY SCORE</div>
          <div className="font-bold text-[#EF4444] text-sm mt-0.5">
            {current.priorityScore.toFixed(0)}/100 ({current.priorityLevel})
          </div>
        </div>
      </div>

      {/* Main Grid: Complaint & Vision Detections */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Complaint Text & NLP Analytics */}
        <div className="lg:col-span-6 space-y-4">
          {/* Complaint Text */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-2 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B] flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#6457E8]" />
              <span>Citizen Complaint Narrative</span>
            </div>
            <p className="text-[#11162A] font-sans text-sm leading-relaxed">
              {current.complaintText || '(Patrol Automated Ingestion - No narrative provided)'}
            </p>
          </div>

          {/* NLP Extraction Result */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-3 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B]">
              NLP Analysis & Semantic Cues
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                <div className="text-[#65708B] text-xs font-medium">Extracted Urgency</div>
                <div className="text-sm font-bold text-[#F97316] mt-0.5">
                  {(current.urgency * 100).toFixed(0)}%
                </div>
              </div>
              <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1]">
                <div className="text-[#65708B] text-xs font-medium">Text Severity</div>
                <div className="text-sm font-bold text-[#EF4444] mt-0.5">
                  {(current.severity * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] text-[#11162A] font-sans text-xs">
              <strong>Consistency Analysis: </strong>
              {current.consistencyDetail?.reason || 'Cross-validated NLP tokens with visual detection.'}
            </div>
          </div>

          {/* Explainable Dynamic Priority Breakdown */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-2 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B]">
              Feature 15: Explainable Priority Factors
            </div>
            <PriorityGauge
              score={current.priorityScore}
              level={current.priorityLevel}
              breakdown={current.priorityBreakdown}
              reasoning={current.priorityReasoning}
              showDetails={true}
            />
          </div>
        </div>

        {/* Right: Vision / YOLO Detection & Department Routing */}
        <div className="lg:col-span-6 space-y-4">
          {/* YOLO Detection Panel */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-3 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B] flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>YOLOv8 Computer Vision Detection</span>
              </span>
              <span className="text-[#6457E8] font-mono text-xs font-semibold">
                {((current.visualConfidence || 0.9) * 100).toFixed(0)}% Confidence
              </span>
            </div>

            {/* Visual Box Representation */}
            <div className="relative h-48 bg-[#10162A] rounded-xl border border-[#212348] flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 bg-dot-matrix opacity-30" />
              {/* Bounding Box Overlay */}
              <div className="relative z-10 p-3 border-2 border-[#8B5CF6] bg-[#6457E8]/20 rounded-lg shadow-lg flex flex-col items-center">
                <span className="text-xs bg-[#6457E8] text-white px-2 py-0.5 rounded font-semibold uppercase mb-1">
                  {current.visualDetection || 'Pothole (Detected)'}
                </span>
                <span className="text-xs text-indigo-200 font-mono">
                  Confidence: {((current.visualConfidence || 0.9) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-[#65708B] pt-1">
              <span>Image Evidence URI: {current.imageUrl || 'Patrol Survey Imagery'}</span>
              <span className="text-emerald-700 font-medium">YOLOv8s Ingested</span>
            </div>
          </div>

          {/* Department Dispatch & Recommended Action */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-2.5 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B] flex items-center justify-between">
              <span>Feature 19: Department Routing Protocol</span>
              <span className="text-[#6457E8] font-bold">SLA: {current.slaHours} Hours</span>
            </div>

            <div className="flex items-center gap-2 text-[#11162A] font-bold text-sm">
              <Building className="w-4 h-4 text-[#6457E8] shrink-0" />
              <span>{current.department}</span>
            </div>

            <div className="p-3 bg-[#F0F2F9] rounded-lg border border-[#E4E7F1] text-[#11162A] text-xs font-sans">
              <strong className="text-[#6457E8] font-semibold text-xs block mb-1">
                RECOMMENDED ACTION:
              </strong>
              {current.recommendedAction}
            </div>
          </div>

          {/* Timeline & Lifecycle Action Bar */}
          <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl space-y-3 shadow-xs">
            <div className="text-xs font-semibold text-[#65708B] flex items-center justify-between">
              <span>Work Order Lifecycle Timeline</span>
              <button
                onClick={() => onOpenResolutionModal(current)}
                className="px-3 py-1.5 bg-[#10B981] hover:bg-[#059669] text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1 cursor-pointer"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Verify Resolution</span>
              </button>
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto py-1">
              {lifecycleStages.map((st) => {
                const isActive = current.status === st
                return (
                  <button
                    key={st}
                    disabled={advancing}
                    onClick={() => handleAdvanceStatus(st)}
                    className={cn(
                      'px-2.5 py-1 rounded-lg text-xs font-medium transition border whitespace-nowrap cursor-pointer',
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
        </div>
      </div>
    </div>
  )
}
