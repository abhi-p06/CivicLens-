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
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Top Header & Issue Selector */}
      <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">
              ISSUE INTELLIGENCE DOSSIER
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-lg font-bold text-slate-100">{current.issueId}</span>
              <StatusBadge status={current.status} />
              <ConsistencyBadge level={current.consistencyFlag || 'CONSISTENT'} />
            </div>
          </div>
        </div>

        {/* Dropdown selector to switch between issues */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400 uppercase">Select Issue:</span>
          <select
            value={current.issueId}
            onChange={(e) => {
              const found = issues.find((i) => i.issueId === e.target.value)
              if (found) onSelectIssue(found)
            }}
            className="bg-[#121824] border border-slate-700 text-slate-200 rounded px-2.5 py-1.5 text-xs outline-none focus:border-cyan-500 cursor-pointer"
          >
            {issues.map((i) => (
              <option key={i.issueId} value={i.issueId} className="bg-[#0e131d]">
                {i.issueId} &bull; {i.category} ({i.location})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Overview Metadata Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">STATUS</div>
          <div className="font-bold text-cyan-400 text-xs mt-1 truncate">{current.status}</div>
        </div>

        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">CATEGORY</div>
          <div className="font-bold text-slate-100 text-xs mt-1 truncate">{current.category}</div>
        </div>

        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">LOCATION</div>
          <div className="font-bold text-slate-200 text-xs mt-1 truncate">{current.location}</div>
        </div>

        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">WARD</div>
          <div className="font-bold text-slate-300 text-xs mt-1 truncate">{current.ward}</div>
        </div>

        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">DATE INGESTED</div>
          <div className="font-bold text-slate-300 text-xs mt-1 truncate">
            {new Date(current.timestamp).toLocaleDateString()}
          </div>
        </div>

        <div className="p-3 bg-[#111724] border border-slate-800 rounded-lg">
          <div className="text-slate-400 text-[10px] uppercase">PRIORITY SCORE</div>
          <div className="font-bold text-rose-400 text-sm mt-0.5">
            {current.priorityScore.toFixed(0)}/100 ({current.priorityLevel})
          </div>
        </div>
      </div>

      {/* Main Grid: Complaint & Vision Detections */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Complaint Text & NLP Analytics */}
        <div className="lg:col-span-6 space-y-4">
          {/* Complaint Text */}
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-2 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              <span>Citizen Complaint Narrative</span>
            </div>
            <p className="text-slate-200 font-sans text-xs leading-relaxed">
              {current.complaintText || '(Patrol Automated Ingestion - No narrative provided)'}
            </p>
          </div>

          {/* NLP Extraction Result */}
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-3 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              NLP Analysis & Semantic Cues
            </div>
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">EXTRACTED URGENCY</div>
                <div className="text-sm font-bold text-amber-400 mt-0.5">
                  {(current.urgency * 100).toFixed(0)}%
                </div>
              </div>
              <div className="p-2.5 bg-[#121824] rounded border border-slate-800">
                <div className="text-slate-400 text-[10px]">TEXT SEVERITY</div>
                <div className="text-sm font-bold text-rose-400 mt-0.5">
                  {(current.severity * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            <div className="p-2.5 bg-[#121824] rounded border border-slate-800 text-slate-300 font-sans text-xs">
              <strong>Consistency Analysis: </strong>
              {current.consistencyDetail?.reason || 'Cross-validated NLP tokens with visual detection.'}
            </div>
          </div>

          {/* Explainable Dynamic Priority Breakdown */}
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-2 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400">
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
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-3 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-cyan-400" />
                <span>YOLOv8 Computer Vision Detection</span>
              </span>
              <span className="text-cyan-400 font-mono">
                {((current.visualConfidence || 0.9) * 100).toFixed(0)}% Confidence
              </span>
            </div>

            {/* Visual Box Representation */}
            <div className="relative h-48 bg-[#0a0d14] rounded-lg border border-slate-800 flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 bg-dot-matrix opacity-30" />
              {/* Simulated Bounding Box Overlay */}
              <div className="relative z-10 p-3 border-2 border-cyan-400 bg-cyan-950/20 rounded shadow-lg shadow-cyan-950/50 flex flex-col items-center">
                <span className="text-[10px] bg-cyan-500 text-black px-1.5 py-0.5 rounded font-bold uppercase mb-1">
                  {current.visualDetection || 'Pothole (Detected)'}
                </span>
                <span className="text-[11px] text-cyan-300 font-mono">
                  Confidence: {((current.visualConfidence || 0.9) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1">
              <span>Image Evidence URI: {current.imageUrl || 'Patrol Survey Imagery'}</span>
              <span className="text-emerald-400">YOLOv8s Ingested</span>
            </div>
          </div>

          {/* Department Dispatch & Recommended Action */}
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-2.5 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
              <span>Feature 19: Department Routing Protocol</span>
              <span className="text-emerald-400 font-bold">SLA: {current.slaHours} Hours</span>
            </div>

            <div className="flex items-center gap-2 text-slate-100 font-bold text-sm">
              <Building className="w-4 h-4 text-cyan-400 shrink-0" />
              <span>{current.department}</span>
            </div>

            <div className="p-2.5 bg-[#121824] rounded border border-slate-800 text-slate-200 text-xs font-sans">
              <strong className="text-cyan-400 font-mono text-[10px] block mb-1">
                RECOMMENDED ACTION:
              </strong>
              {current.recommendedAction}
            </div>
          </div>

          {/* Timeline & Lifecycle Action Bar */}
          <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-3 shadow-xl">
            <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
              <span>Work Order Lifecycle Timeline</span>
              <button
                onClick={() => onOpenResolutionModal(current)}
                className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-bold shadow transition flex items-center gap-1"
              >
                <Camera className="w-3 h-3" />
                <span>Verify Resolution</span>
              </button>
            </div>

            <div className="flex items-center gap-1 overflow-x-auto py-1">
              {lifecycleStages.map((st) => {
                const isActive = current.status === st
                return (
                  <button
                    key={st}
                    disabled={advancing}
                    onClick={() => handleAdvanceStatus(st)}
                    className={cn(
                      'px-2 py-1 rounded text-[10px] uppercase transition border whitespace-nowrap',
                      isActive
                        ? 'bg-cyan-950 border-cyan-500 text-cyan-200 font-bold shadow'
                        : 'bg-slate-900 border-slate-800 text-slate-500 hover:text-slate-300'
                    )}
                  >
                    {st}
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
