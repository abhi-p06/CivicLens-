import React from 'react'
import { CheckCircle2, ShieldCheck, ArrowRight, Camera, AlertTriangle } from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
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
    'ACTION IN PROGRESS',
    'VERIFICATION',
    'RESOLVED',
  ]

  const verifiedIssues = issues.filter((i) => i.resolutionEvidence || i.status === 'RESOLVED')

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-emerald-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              FEATURE 20: RESOLUTION VERIFICATION & WORK-ORDER LIFECYCLE
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Automated computer vision comparison of before/after field imagery to verify municipal repairs without relying purely on contractor self-certification.
          </p>
        </div>

        <div className="px-3 py-1.5 bg-emerald-950/80 border border-emerald-800 text-emerald-300 rounded font-bold">
          {verifiedIssues.length} VERIFIED WORK ORDERS
        </div>
      </div>

      {/* Lifecycle Flow Stepper */}
      <div className="p-4 bg-[#0e131d] border border-slate-800 rounded-xl space-y-2 shadow-xl">
        <div className="text-[10px] uppercase font-bold text-slate-400">
          Standard Civic Lifecycle Pipeline
        </div>
        <div className="flex items-center justify-between gap-1 overflow-x-auto py-2">
          {lifecycleStages.map((stage, idx) => (
            <React.Fragment key={stage}>
              <div className="px-2.5 py-1.5 rounded bg-[#121824] border border-slate-800 text-center shrink-0">
                <div className="text-[9px] text-slate-500 font-mono">0{idx + 1}</div>
                <div className="font-bold text-[10px] text-slate-200 uppercase whitespace-nowrap">
                  {stage}
                </div>
              </div>
              {idx < lifecycleStages.length - 1 && (
                <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0 mx-0.5" />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Table of Active & Verified Issues */}
      <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
        <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 flex items-center justify-between">
          <span>Field Verification Ledger</span>
          <span className="text-slate-500">{issues.length} Records</span>
        </div>

        <div className="space-y-3">
          {issues.map((issue) => {
            const ev = issue.resolutionEvidence
            return (
              <div
                key={issue.issueId}
                className="p-4 bg-[#111724] border border-slate-800 rounded-lg space-y-3 shadow"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
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
                      className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600/90 hover:bg-emerald-500 text-white rounded text-[11px] font-bold shadow transition"
                    >
                      <Camera className="w-3.5 h-3.5" />
                      <span>{ev ? 'Re-Verify Field Image' : 'Run Resolution Verification'}</span>
                    </button>
                  </div>
                </div>

                <p className="text-slate-300 font-sans text-xs leading-relaxed">
                  {issue.complaintText}
                </p>

                {/* If verified evidence exists */}
                {ev ? (
                  <div className="p-3 bg-[#0a0d14] rounded-lg border border-emerald-900/60 space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-emerald-400" />
                        <span className="font-bold text-slate-200">
                          Field Verification Status:{' '}
                          <span
                            className={cn(
                              ev.resolutionStatus === 'LIKELY RESOLVED'
                                ? 'text-emerald-400'
                                : 'text-amber-400'
                            )}
                          >
                            {ev.resolutionStatus}
                          </span>
                        </span>
                      </div>
                      <span className="text-cyan-400 font-mono text-[11px]">
                        {(ev.resolutionConfidence * 100).toFixed(1)}% Confidence
                      </span>
                    </div>

                    <div className="text-slate-400 text-[11px] font-sans">
                      {ev.verificationSummary}
                    </div>

                    <div className="text-[10px] text-slate-500 flex justify-between pt-1 border-t border-slate-900">
                      <span>Post-Action Image: {ev.postActionImageUrl || 'Field Snapshot'}</span>
                      <span>Verified: {new Date(ev.verifiedAt).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ) : (
                  <div className="p-2.5 bg-[#0a0d14] rounded border border-slate-800 text-slate-500 text-[11px] flex items-center justify-between">
                    <span>Awaiting field repair completion and post-action visual evidence.</span>
                    <span className="text-amber-500 font-bold uppercase text-[10px]">PENDING VERIFICATION</span>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
