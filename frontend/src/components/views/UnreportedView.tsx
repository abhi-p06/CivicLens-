import React from 'react'
import { Camera, Eye, MapPin, Sparkles, Send, CheckCircle2, AlertTriangle, Layers } from 'lucide-react'
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
    (i) => i.metadata?.isAutoDrafted || i.source === 'patrol_camera' || i.source === 'camera_survey'
  )

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-cyan-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <Camera className="w-5 h-5 text-cyan-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide uppercase">
              FEATURE 11 // UNREPORTED CIVIC DEFECTS (AUTONOMOUS PATROL)
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-0.5">
            Surveillance vehicle and bus-mounted cameras proactively identify infrastructure damage before citizens report them.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 bg-cyan-950/80 border border-cyan-700 text-cyan-300 rounded font-bold">
            {unreported.length} PROACTIVE DISCOVERIES
          </span>
        </div>
      </div>

      {/* Grid of Unreported Detections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {unreported.map((issue) => {
          const confidence = ((issue.visualConfidence || 0.9) * 100).toFixed(0)

          return (
            <div
              key={issue.issueId}
              onClick={() => onSelectIssue(issue)}
              className="p-5 bg-[#0e131d] hover:bg-[#121824] border border-cyan-900/60 hover:border-cyan-500 rounded-xl cursor-pointer transition shadow-xl space-y-4 group relative overflow-hidden"
            >
              {/* Top Accent */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 to-blue-500" />

              {/* Header with UNREPORTED ISSUE pill */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-cyan-950 border border-cyan-600 text-cyan-300 uppercase tracking-wider">
                    UNREPORTED ISSUE
                  </span>
                  <span className="font-bold text-slate-100 group-hover:text-cyan-300">
                    {issue.issueId}
                  </span>
                </div>
                <StatusBadge status={issue.status} />
              </div>

              {/* Image & YOLO Detection */}
              <div className="p-3 bg-[#0a0d14] rounded-lg border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4 text-cyan-400" />
                    <span className="text-slate-100 font-bold text-xs">
                      {issue.visualDetection || 'Pothole (Detected)'}
                    </span>
                  </div>
                  <span className="text-cyan-400 font-mono text-xs font-bold">
                    {confidence}% YOLO Confidence
                  </span>
                </div>

                <div className="text-[10px] text-slate-500 font-mono">
                  Evidence URI: {issue.imageUrl || 'data/patrol_survey_pothole.jpg'}
                </div>
              </div>

              {/* Location */}
              <div className="flex items-center gap-2 text-slate-200">
                <MapPin className="w-4 h-4 text-cyan-400 shrink-0" />
                <span className="font-bold">{issue.location}</span>
                <span className="text-slate-400">({issue.ward}) &bull; Lat: {issue.latitude.toFixed(4)}, Lng: {issue.longitude.toFixed(4)}</span>
              </div>

              {/* Synthetic Description */}
              <p className="text-slate-300 font-sans text-xs leading-relaxed">
                {issue.complaintText}
              </p>

              {/* Matching Result & Nearby Complaints */}
              <div className="p-3 bg-[#111724] rounded-lg border border-slate-800 space-y-1.5 text-[11px]">
                <div className="text-slate-400 text-[10px] uppercase font-bold">
                  Spatial Matching & Deduplication Audit
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Nearby Citizen Reports:</span>
                  <span className="font-bold text-amber-400">
                    {issue.metadata?.nearDuplicateCount ?? (issue.isDuplicate ? 1 : 0)} adjacent complaints
                  </span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Matching Result:</span>
                  <span className="font-bold text-emerald-400">
                    {issue.isDuplicate ? `Merged into Cluster ${issue.duplicateGroupId || 'GRP-01'}` : 'New Discovered Incident (Triaged)'}
                  </span>
                </div>
              </div>

              {/* Footer Priority */}
              <div className="border-t border-slate-800/80 pt-3 flex items-center justify-between">
                <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                <button
                  type="button"
                  className="px-3 py-1 bg-cyan-600 group-hover:bg-cyan-500 text-white rounded text-[11px] font-bold shadow transition"
                >
                  Inspect Issue &rarr;
                </button>
              </div>
            </div>
          )
        })}

        {unreported.length === 0 && (
          <div className="col-span-2 p-12 text-center bg-[#0e131d] border border-slate-800 rounded-xl text-slate-500">
            No active unreported camera survey incidents in queue.
          </div>
        )}
      </div>
    </div>
  )
}
