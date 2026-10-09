import React from 'react'
import {
  Camera,
  Eye,
  MapPin,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { cn } from '../../lib/utils'

interface UnreportedViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const UnreportedView: React.FC<UnreportedViewProps> = ({ issues, onSelectIssue }) => {
  const unreported = issues.filter(
    (i) =>
      i.metadata?.isAutoDrafted ||
      i.source === 'patrol_camera' ||
      i.source === 'camera_survey' ||
      i.issueId === 'CIVIC-2026-006'
  )

  return (
    <div className="h-full flex flex-col overflow-y-auto p-5 sm:p-7 space-y-6 font-sans">
      {/* Header */}
      <div className="p-6 bg-[#0c1018] border border-slate-800/90 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-2 h-full bg-cyan-500 shadow-[0_0_12px_#06b6d4]" />
        
        <div className="space-y-1 pl-2">
          <div className="flex items-center gap-2.5">
            <Camera className="w-6 h-6 text-cyan-400" />
            <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
              Autonomous Patrol Discoveries
            </h1>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-mono font-bold bg-cyan-950/80 border border-cyan-700 text-cyan-300">
              FEATURE 11
            </span>
          </div>
          <p className="text-slate-400 text-sm max-w-2xl leading-relaxed">
            Vehicle-mounted and bus dashcam feeds proactively detect infrastructure defects before citizen escalation.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pl-2 md:pl-0">
          <div className="px-4 py-2 bg-[#101622] border border-slate-800 rounded-xl text-right">
            <div className="text-xs text-slate-400 font-mono">Camera Detections</div>
            <div className="text-base font-bold font-mono text-cyan-400">
              {unreported.length} Discovered
            </div>
          </div>
        </div>
      </div>

      {/* Grid of Unreported Detections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {unreported.map((issue) => {
          const confidence = ((issue.visualConfidence || 0.94) * 100).toFixed(0)

          return (
            <div
              key={issue.issueId}
              onClick={() => onSelectIssue(issue)}
              className="p-6 bg-[#0c1018] hover:bg-[#101624] border border-slate-800/90 hover:border-cyan-500/70 rounded-2xl cursor-pointer transition-all duration-200 shadow-xl space-y-4 group relative overflow-hidden"
            >
              {/* Header with UNREPORTED ISSUE pill */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-md text-xs font-bold bg-cyan-950/90 border border-cyan-600/80 text-cyan-300 tracking-wider font-mono">
                    AUTONOMOUS PATROL
                  </span>
                  <span className="font-mono text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">
                    {issue.issueId}
                  </span>
                </div>
                <StatusBadge status={issue.status} />
              </div>

              {/* Image & YOLO Detection */}
              <div className="p-3.5 bg-[#080b11] rounded-xl border border-slate-800/90 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <Eye className="w-5 h-5 text-cyan-400 shrink-0" />
                  <div>
                    <div className="text-white font-bold text-sm">
                      {issue.visualDetection || 'Pothole (Detected)'}
                    </div>
                    <div className="text-xs text-slate-500 font-mono">
                      YOLOv8 Feature Extraction
                    </div>
                  </div>
                </div>
                <span className="text-cyan-400 font-mono text-xs font-bold px-2 py-1 rounded bg-[#0e1422] border border-cyan-900/60">
                  {confidence}% Confidence
                </span>
              </div>

              {/* Location */}
              <div className="flex items-center gap-2 text-slate-200 text-sm">
                <MapPin className="w-4 h-4 text-cyan-400 shrink-0" />
                <span className="font-semibold">{issue.location}</span>
                {issue.ward && (
                  <span className="text-slate-400 font-mono">({issue.ward})</span>
                )}
              </div>

              {/* Description (14px readable) */}
              <p className="text-slate-300 text-sm leading-relaxed font-sans line-clamp-3">
                {issue.complaintText}
              </p>

              {/* Spatial Matching Audit */}
              <div className="p-3 bg-[#111724] rounded-xl border border-slate-800 space-y-1.5 text-xs">
                <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider font-mono">
                  Spatial Deduplication Audit
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Adjacent Citizen Complaints:</span>
                  <strong className="text-amber-400 font-mono">
                    {issue.metadata?.nearDuplicateCount ?? (issue.isDuplicate ? 1 : 0)} nearby reports
                  </strong>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Routing Recommendation:</span>
                  <strong className="text-emerald-400 font-mono">
                    Auto-drafted Municipal Work Order
                  </strong>
                </div>
              </div>

              {/* Footer Priority */}
              <div className="border-t border-slate-800/90 pt-3.5 flex items-center justify-between gap-3">
                <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                <button
                  type="button"
                  className="px-3.5 py-1.5 bg-cyan-600 group-hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold shadow-md transition flex items-center gap-1.5"
                >
                  <span>View Dossier</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        })}

        {unreported.length === 0 && (
          <div className="col-span-2 p-12 text-center bg-[#0c1018] border border-slate-800 rounded-2xl text-slate-400 space-y-2">
            <Camera className="w-8 h-8 text-slate-600 mx-auto" />
            <div className="text-base font-semibold text-slate-200">
              No Unreported Patrol Detections In Queue
            </div>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              Automated sensor surveillance vehicles have cleared active patrol sectors.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default UnreportedView
