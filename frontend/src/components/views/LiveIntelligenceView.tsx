import React, { useState, useEffect } from 'react'
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
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Top Telemetry Strip */}
      <div className="p-4 bg-[#101420] border border-cyan-900/50 rounded-xl flex items-center justify-between shadow-xl">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-full bg-cyan-950/60 border border-cyan-700/60">
            <Radio className="w-4 h-4 text-cyan-400" />
            <span className="absolute w-10 h-10 rounded-full border border-cyan-500/30 animate-ping" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-100 tracking-wide flex items-center gap-2">
              <span>LIVE MUNICIPAL SENSOR & INTAKE RADAR</span>
              <span className="px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400 text-[10px]">
                ACTIVE SWEEP
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-sans mt-0.5">
              Multimodal NLP & YOLOv8 continuous stream across Greater Mumbai.
            </div>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-4 text-slate-300">
          <div className="text-right">
            <div className="text-[10px] text-slate-400">INGESTION LATENCY</div>
            <div className="text-sm font-bold text-cyan-400 font-mono">142ms</div>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-slate-400">PIPELINE THROUGHPUT</div>
            <div className="text-sm font-bold text-emerald-400 font-mono">48 req/min</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Realtime Incident Feed vs Telemetry Console */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 flex-1">
        {/* Left: Realtime Incident Cards */}
        <div className="lg:col-span-7 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <span>Real-Time Ingested Incident Feed</span>
            </span>
            <span className="text-slate-500">{issues.length} Monitored</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[600px]">
            {issues.map((issue) => (
              <div
                key={issue.issueId}
                onClick={() => onSelectIssue(issue)}
                className="p-3.5 bg-[#111724] hover:bg-[#151c2e] border border-slate-800/90 hover:border-cyan-800/80 rounded-lg cursor-pointer transition shadow group"
              >
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-cyan-400 group-hover:underline">
                      {issue.issueId}
                    </span>
                    <StatusBadge status={issue.status} />
                    {issue.isHotspot && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-950 border border-rose-800 text-rose-300 flex items-center gap-1">
                        <Flame className="w-3 h-3" />
                        HOTSPOT
                      </span>
                    )}
                  </div>
                  <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                </div>

                <div className="text-slate-100 font-sans text-xs line-clamp-2 leading-relaxed mb-2">
                  {issue.complaintText}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400 pt-2 border-t border-slate-800/70">
                  <span>
                    Location: <strong className="text-slate-200">{issue.location}</strong> ({issue.ward})
                  </span>
                  <div className="flex items-center gap-2">
                    <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                    <span className="text-slate-500">
                      {new Date(issue.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Operational Telemetry Audit Log */}
        <div className="lg:col-span-5 bg-[#0e131d] border border-slate-800 rounded-xl p-4 flex flex-col shadow-xl">
          <div className="text-[11px] uppercase font-bold text-slate-300 border-b border-slate-800 pb-2 mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-emerald-400" />
              <span>Event Audit Stream</span>
            </span>
            <span className="text-emerald-400 text-[10px]">REALTIME</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 pr-1 max-h-[600px] bg-[#090c13] p-3 rounded-lg border border-slate-900 font-mono text-[11px]">
            {telemetryLogs.map((log) => (
              <div
                key={log.id}
                className="p-1.5 rounded flex items-start gap-2 border border-transparent hover:border-slate-800 transition"
              >
                <span className="text-slate-500 shrink-0">{log.time}</span>
                <span
                  className={
                    log.type === 'alert'
                      ? 'text-rose-400 font-bold'
                      : log.type === 'warn'
                      ? 'text-amber-400'
                      : 'text-slate-300'
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
