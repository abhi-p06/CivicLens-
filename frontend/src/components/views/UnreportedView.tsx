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
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-6 font-sans bg-[#F6F7FC]">
      {/* Header */}
      <div className="p-6 bg-white border border-[#E4E7F1] rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs relative overflow-hidden">
        <div className="absolute top-0 left-0 w-1.5 h-full bg-[#6457E8]" />
        
        <div className="space-y-1 pl-2">
          <div className="flex items-center gap-2.5">
            <Camera className="w-6 h-6 text-[#6457E8]" />
            <h1 className="text-xl sm:text-2xl font-bold text-[#11162A] tracking-normal">
              Autonomous Patrol Discoveries
            </h1>
            <span className="px-2.5 py-0.5 rounded-md text-xs font-semibold bg-indigo-50 border border-indigo-200 text-[#6457E8]">
              FEATURE 11
            </span>
          </div>
          <p className="text-[#65708B] text-sm max-w-2xl leading-relaxed">
            Vehicle-mounted and bus dashcam feeds proactively detect infrastructure defects before citizen escalation.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0 pl-2 md:pl-0">
          <div className="px-4 py-2 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl text-right">
            <div className="text-xs text-[#65708B]">Camera Detections</div>
            <div className="text-base font-bold font-mono text-[#6457E8]">
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
              className="p-6 bg-white hover:bg-[#F0F2F9]/50 border border-[#E4E7F1] hover:border-[#8B5CF6]/60 rounded-2xl cursor-pointer transition-all duration-200 shadow-xs space-y-4 group relative overflow-hidden"
            >
              {/* Header with UNREPORTED ISSUE pill */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-indigo-50 border border-indigo-200 text-[#6457E8]">
                    AUTONOMOUS PATROL
                  </span>
                  <span className="font-mono text-sm font-bold text-[#11162A] group-hover:text-[#6457E8] transition-colors">
                    {issue.issueId}
                  </span>
                </div>
                <StatusBadge status={issue.status} />
              </div>

              {/* Image & YOLO Detection */}
              <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <Eye className="w-5 h-5 text-[#6457E8] shrink-0" />
                  <div>
                    <div className="text-[#11162A] font-bold text-sm">
                      {issue.visualDetection || 'Pothole (Detected)'}
                    </div>
                    <div className="text-xs text-[#65708B]">
                      YOLOv8 Feature Extraction
                    </div>
                  </div>
                </div>
                <span className="text-[#6457E8] font-mono text-xs font-semibold px-2.5 py-1 rounded-md bg-white border border-[#E4E7F1]">
                  {confidence}% Confidence
                </span>
              </div>

              {/* Location */}
              <div className="flex items-center gap-2 text-[#11162A] text-sm">
                <MapPin className="w-4 h-4 text-[#6457E8] shrink-0" />
                <span className="font-semibold">{issue.location}</span>
                {issue.ward && (
                  <span className="text-[#65708B] font-mono text-xs">({issue.ward})</span>
                )}
              </div>

              {/* Description (14px readable) */}
              <p className="text-[#11162A] text-sm leading-relaxed font-sans line-clamp-3">
                {issue.complaintText}
              </p>

              {/* Spatial Matching Audit */}
              <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-1.5 text-xs">
                <div className="text-[#65708B] text-xs font-semibold">
                  Spatial Deduplication Audit
                </div>
                <div className="flex justify-between text-[#11162A]">
                  <span className="text-[#65708B]">Adjacent Citizen Complaints:</span>
                  <strong className="text-[#F97316] font-mono">
                    {issue.metadata?.nearDuplicateCount ?? (issue.isDuplicate ? 1 : 0)} nearby reports
                  </strong>
                </div>
                <div className="flex justify-between text-[#11162A]">
                  <span className="text-[#65708B]">Routing Recommendation:</span>
                  <strong className="text-emerald-700 font-semibold">
                    Auto-drafted Municipal Work Order
                  </strong>
                </div>
              </div>

              {/* Footer Priority */}
              <div className="border-t border-[#E4E7F1] pt-3.5 flex items-center justify-between gap-3">
                <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                <button
                  type="button"
                  className="px-3.5 py-2 bg-[#6457E8] group-hover:bg-[#5145CF] text-white rounded-lg text-xs font-semibold shadow-xs transition flex items-center gap-1.5 cursor-pointer"
                >
                  <span>View Dossier</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )
        })}

        {unreported.length === 0 && (
          <div className="col-span-2 p-12 text-center bg-white border border-[#E4E7F1] rounded-2xl text-[#65708B] space-y-2 shadow-xs">
            <Camera className="w-8 h-8 text-slate-400 mx-auto" />
            <div className="text-base font-semibold text-[#11162A]">
              No Unreported Patrol Detections In Queue
            </div>
            <p className="text-xs text-[#65708B] max-w-md mx-auto">
              Automated sensor surveillance vehicles have cleared active patrol sectors.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

export default UnreportedView
