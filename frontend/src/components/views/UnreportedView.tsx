import React from 'react'
import { Camera, Eye, Sparkles, Send, ShieldAlert, CheckCircle2 } from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'

interface UnreportedViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const UnreportedView: React.FC<UnreportedViewProps> = ({ issues, onSelectIssue }) => {
  const unreported = issues.filter(
    (i) => i.metadata?.isAutoDrafted || i.source === 'patrol_camera' || i.source === 'camera_survey'
  )

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-cyan-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Camera className="w-5 h-5 text-cyan-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              FEATURE 11: AUTONOMOUS PATROL SURVEY DETECTIONS
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Detecting unreported civic defects via vehicle-mounted cameras and visual surveys before citizen grievances are filed.
          </p>
        </div>

        <div className="px-3 py-1.5 bg-cyan-950/80 border border-cyan-800 text-cyan-300 rounded font-bold">
          {unreported.length} AUTO-DRAFTED INCIDENTS
        </div>
      </div>

      {/* Grid of Unreported Detections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {unreported.map((issue) => (
          <div
            key={issue.issueId}
            onClick={() => onSelectIssue(issue)}
            className="p-4 bg-[#0e131d] hover:bg-[#121824] border border-slate-800 hover:border-cyan-800/80 rounded-xl cursor-pointer transition shadow-xl space-y-3 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="font-bold text-cyan-400 group-hover:underline">
                  {issue.issueId}
                </span>
                <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyan-950 border border-cyan-800 text-cyan-300 uppercase">
                  AUTO-DRAFTED
                </span>
              </div>
              <StatusBadge status={issue.status} />
            </div>

            <div className="p-2.5 bg-[#0a0d14] rounded border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-cyan-400" />
                <span className="text-slate-200 font-bold">{issue.visualDetection || 'Pothole (Detected)'}</span>
              </div>
              <span className="text-[10px] text-cyan-400 font-mono">
                {((issue.visualConfidence || 0.9) * 100).toFixed(0)}% Visual Conf
              </span>
            </div>

            <p className="text-slate-300 font-sans text-xs leading-relaxed">
              {issue.complaintText}
            </p>

            <div className="border-t border-slate-800/80 pt-2 flex items-center justify-between text-[11px] text-slate-400">
              <span>{issue.location} ({issue.ward})</span>
              <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
            </div>
          </div>
        ))}

        {unreported.length === 0 && (
          <div className="col-span-2 p-8 text-center bg-[#0e131d] border border-slate-800 rounded-xl text-slate-500">
            No pending auto-drafted patrol detections in queue.
          </div>
        )}
      </div>
    </div>
  )
}
