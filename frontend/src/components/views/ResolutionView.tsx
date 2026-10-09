import React from 'react'
import {
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  Camera,
  AlertTriangle,
  RotateCcw,
  Sparkles,
} from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { BeforeAfterSlider } from '../common/BeforeAfterSlider'
import { cn } from '../../lib/utils'

interface ResolutionViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
  onOpenResolutionModal: (issue: Issue) => void
}

export const ResolutionView: React.FC<ResolutionViewProps> = ({
  issues,
  onSelectIssue,
  onOpenResolutionModal,
}) => {
  const lifecycleStages = [
    'OPEN',
    'ANALYZED',
    'PRIORITIZED',
    'ASSIGNED',
    'IN PROGRESS',
    'VERIFICATION',
    'RESOLVED',
  ]

  const verifiedIssues = issues.filter(
    (i) => i.resolutionEvidence || i.status === 'RESOLVED' || i.status === 'VERIFICATION'
  )

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header Banner */}
      <div className="p-4 bg-[#101420] border border-emerald-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
              RESOLUTION CENTER // ISSUE LIFECYCLE & VERIFICATION
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-0.5">
            Automated before/after computer vision inspection preventing self-certified contractor closures.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 bg-emerald-950/80 border border-emerald-700 text-emerald-300 rounded font-bold">
            {verifiedIssues.length} VERIFIED WORK ORDERS
          </span>
        </div>
      </div>

      {/* 7-Stage Lifecycle Stepper */}
      <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-2.5 shadow-xl">
        <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
          <span>Civic Resolution Lifecycle Pipeline</span>
          <span className="text-emerald-400">Strict Quality Assurance</span>
        </div>

        <div className="flex items-center justify-between gap-1 overflow-x-auto py-2">
          {lifecycleStages.map((stage, idx) => (
            <React.Fragment key={stage}>
              <div className="px-3 py-2 rounded-lg bg-[#121824] border border-slate-800 text-center shrink-0 min-w-[100px]">
                <div className="text-[9px] text-slate-500 font-mono">0{idx + 1}</div>
                <div className="font-bold text-[10px] text-slate-200 uppercase whitespace-nowrap mt-0.5">
                  {stage}
                </div>
              </div>
              {idx < lifecycleStages.length - 1 && (
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0 mx-1" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Verification Ledger with Interactive Before/After Comparison */}
      <div className="space-y-4">
        {issues.map((issue) => {
          const ev = issue.resolutionEvidence
          return (
            <div
              key={issue.issueId}
              className="p-5 bg-[#0e131d] border border-slate-800 rounded-xl shadow-xl space-y-4"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span
                    onClick={() => onSelectIssue(issue)}
                    className="font-bold text-cyan-400 cursor-pointer hover:underline text-sm"
                  >
                    {issue.issueId}
                  </span>
                  <StatusBadge status={issue.status} />
                  <span className="text-slate-400 text-xs">({issue.category})</span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onOpenResolutionModal(issue)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-bold shadow transition"
                  >
                    <Camera className="w-3.5 h-3.5" />
                    <span>{ev ? 'Re-Verify Post-Action Image' : 'Verify Resolution'}</span>
                  </button>
                </div>
              </div>

              <div className="text-slate-200 font-sans text-xs leading-relaxed">
                {issue.complaintText}
              </div>

              {/* Interactive Before / After Comparison */}
              <div className="space-y-1.5">
                <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-between">
                  <span>Interactive Field Evidence Comparison (Drag Slider)</span>
                  <span className="text-cyan-400">Computer Vision Delta Analysis</span>
                </div>

                <BeforeAfterSlider
                  beforeLabel="ORIGINAL DEFECT (BEFORE)"
                  afterLabel="FIELD RESTORATION (AFTER)"
                  beforeSubtext={issue.visualDetection || 'Pothole (Detected, 94% conf)'}
                  afterSubtext={ev ? ev.verificationSummary : 'Clean asphalt patch (No residual defect detected)'}
                  confidence={ev ? ev.resolutionConfidence : 0.94}
                />
              </div>

              {/* Verification Assessment Badge & Notes */}
              {ev ? (
                <div className="p-3 bg-[#0a0d14] rounded-lg border border-emerald-900/60 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px]">
                  <div>
                    <span className="text-slate-400">Status: </span>
                    <strong className="text-emerald-400 font-bold">{ev.resolutionStatus}</strong>
                    <span className="text-slate-500 ml-2">({ev.verificationSummary})</span>
                  </div>
                  <div className="text-cyan-400 font-mono text-[10px] shrink-0">
                    Confidence: {(ev.resolutionConfidence * 100).toFixed(1)}% &bull;{' '}
                    {new Date(ev.verifiedAt).toLocaleTimeString()}
                  </div>
                </div>
              ) : (
                <div className="p-2.5 bg-[#0a0d14] rounded border border-slate-800 text-slate-500 text-[11px] flex items-center justify-between">
                  <span>No post-action field evidence verified yet. Work order in progress.</span>
                  <span className="text-amber-400 font-bold text-[10px]">AWAITING COMPLETION</span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
