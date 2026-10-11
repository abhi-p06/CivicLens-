import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Radio,
  Activity,
  AlertTriangle,
  Clock,
  Sparkles,
  ShieldCheck,
  ChevronRight,
  Flame,
} from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'

interface LiveIntelligenceViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const LiveIntelligenceView: React.FC<LiveIntelligenceViewProps> = ({
  issues,
  onSelectIssue,
}) => {
  const [telemetryLogs, setTelemetryLogs] = useState<
    Array<{ id: string; time: string; msg: string; type: 'info' | 'warn' | 'alert' }>
  >([])

  useEffect(() => {
    // Generate initial live telemetry stream
    const logs: Array<{ id: string; time: string; msg: string; type: 'info' | 'warn' | 'alert' }> = []
    issues.forEach((i, idx) => {
      logs.push({
        id: `LOG-${idx}-A`,
        time: new Date(i.timestamp).toLocaleTimeString(),
        msg: `Inference pipeline processed ${i.issueId}: ${i.category} [Priority: ${i.priorityScore.toFixed(0)}]`,
        type: i.priorityScore >= 80 ? 'alert' : 'info',
      })
      if (i.isHotspot) {
        logs.push({
          id: `LOG-${idx}-B`,
          time: new Date(i.timestamp).toLocaleTimeString(),
          msg: `Spatiotemporal DBSCAN tagged ${i.issueId} in cluster ${i.hotspotClusterId}`,
          type: 'warn',
        })
      }
    })
    setTelemetryLogs(logs)
  }, [issues])

  return (
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-5 font-sans text-xs bg-[#F6F7FC]">
      {/* Top Telemetry Strip */}
      <div className="p-5 bg-white border border-[#E4E7F1] rounded-2xl flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-full bg-indigo-50 border border-indigo-200">
            <Radio className="w-4 h-4 text-[#6457E8]" />
            <span className="absolute w-11 h-11 rounded-full border border-[#8B5CF6]/30 animate-ping" />
          </div>
          <div>
            <div className="text-sm font-bold text-[#11162A] tracking-normal flex items-center gap-2">
              <span>Live Municipal Sensor & Intake Radar</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-semibold">
                ACTIVE SWEEP
              </span>
            </div>
            <div className="text-xs text-[#65708B] font-sans mt-0.5">
              Multimodal NLP & YOLOv8 continuous stream across Greater Mumbai.
            </div>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-5 text-[#11162A]">
          <div className="text-right">
            <div className="text-xs text-[#65708B]">INGESTION LATENCY</div>
            <div className="text-sm font-bold text-[#6457E8] font-mono">142ms</div>
          </div>
          <div className="text-right">
            <div className="text-xs text-[#65708B]">PIPELINE THROUGHPUT</div>
            <div className="text-sm font-bold text-emerald-700 font-mono">48 req/min</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Realtime Incident Feed vs Telemetry Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
        {/* Left: Realtime Incident Cards */}
        <div className="lg:col-span-7 bg-white border border-[#E4E7F1] rounded-2xl p-5 flex flex-col shadow-xs">
          <div className="text-xs font-semibold text-[#11162A] border-b border-[#E4E7F1] pb-3 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#6457E8]" />
              <span>Real-Time Ingested Incident Feed</span>
            </span>
            <span className="text-xs text-[#65708B]">{issues.length} Monitored</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[600px]">
            {issues.map((issue) => (
              <motion.div
                key={issue.issueId}
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => onSelectIssue(issue)}
                className="p-4 bg-[#F0F2F9] hover:bg-slate-200/50 border border-[#E4E7F1] hover:border-[#8B5CF6]/50 rounded-xl cursor-pointer transition shadow-xs group"
              >
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#6457E8] font-mono group-hover:underline">
                      {issue.issueId}
                    </span>
                    <StatusBadge status={issue.status} />
                    {issue.isHotspot && (
                      <span className="px-2 py-0.5 rounded text-[10px] bg-rose-50 border border-rose-200 text-rose-700 font-semibold flex items-center gap-1">
                        <Flame className="w-3 h-3" />
                        HOTSPOT
                      </span>
                    )}
                  </div>
                  <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                </div>

                <div className="text-[#11162A] font-sans text-xs line-clamp-2 leading-relaxed mb-2">
                  {issue.complaintText}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-[#65708B] pt-2 border-t border-[#E4E7F1]">
                  <span>
                    Location: <strong className="text-[#11162A]">{issue.location}</strong> ({issue.ward})
                  </span>
                  <div className="flex items-center gap-2">
                    <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                    <span className="text-xs text-[#65708B]">
                      {new Date(issue.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Right: Operational Telemetry Audit Log */}
        <div className="lg:col-span-5 bg-white border border-[#E4E7F1] rounded-2xl p-5 flex flex-col shadow-xs">
          <div className="text-xs font-semibold text-[#11162A] border-b border-[#E4E7F1] pb-3 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-600" />
              <span>Event Audit Stream</span>
            </span>
            <span className="text-emerald-700 font-semibold text-xs font-mono">REALTIME</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[600px] bg-[#10162A] p-3.5 rounded-xl border border-[#212348] font-mono text-[11px]">
            {telemetryLogs.map((log) => (
              <div
                key={log.id}
                className="p-1.5 rounded flex items-start gap-2 border border-transparent hover:border-slate-800 transition"
              >
                <span className="text-slate-500 shrink-0">{log.time}</span>
                <span
                  className={
                    log.type === 'alert'
                      ? 'text-[#EF4444] font-bold'
                      : log.type === 'warn'
                      ? 'text-[#F97316]'
                      : 'text-indigo-200'
                  }
                >
                  {log.msg}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
