import React, { useState } from 'react'
import {
  Layers,
  ShieldCheck,
  Sparkles,
  Info,
  AlertTriangle,
  Clock,
  Database,
  Cpu,
  Eye,
  CheckCircle2,
  ExternalLink
} from 'lucide-react'
import { Issue, VisionComparisonData, HostedCandidateResult, VisualDetectionDetail } from '../../types'
import { useAuth } from '../../context/AuthContext'

interface VisionModelComparisonProps {
  issue: Issue
}

export const VisionModelComparison: React.FC<VisionModelComparisonProps> = ({ issue }) => {
  const { role, user } = useAuth()
  const [activeModelTab, setActiveModelTab] = useState<'local' | 'hosted'>('local')

  // Enforce access control: Authorized Municipal Officers and Admins only
  const isAuthorizedStaff = role === 'inspector' || role === 'admin' || user?.role === 'inspector' || user?.role === 'admin'
  if (!isAuthorizedStaff) {
    return null
  }

  const comparison = issue.metadata?.visionComparison as VisionComparisonData | undefined
  const hosted = (issue.metadata?.hosted || comparison?.hosted) as HostedCandidateResult | undefined
  const summary = comparison?.comparisonSummary
  const local = comparison?.local

  // Local model detections
  const localDetections: VisualDetectionDetail[] = local?.detectedObjects || issue.detectedObjects || []
  const localModelName = summary?.localModel || issue.visionModel || (issue.category?.toString().toLowerCase().includes('sanitation') ? 'YOLO11s TACO Waste' : 'YOLOv8s RDD2022')
  const localLatency = summary?.localLatencyMs ?? local?.inferenceTimeMs ?? 50.0
  const localConfidence = summary?.localConfidence ?? issue.visualConfidence ?? 0.0
  const localClasses = local?.detectedClasses || Array.from(new Set(localDetections.map(d => d.label)))

  // Hosted candidate detections
  const hostedDetections: VisualDetectionDetail[] = hosted?.detectedObjects || []
  const hostedModelId = hosted?.modelId || summary?.hostedModel || 'roboflow_candidate'
  const hostedArchitecture = hosted?.architecture || 'Hosted Serverless'
  const hostedLatency = hosted?.inferenceTimeMs ?? summary?.hostedLatencyMs ?? 0.0
  const hostedConfidence = hosted?.visualConfidence ?? summary?.hostedConfidence ?? 0.0
  const hostedClasses = hosted?.detectedClasses || Array.from(new Set(hostedDetections.map(d => d.label)))
  const isHostedCached = hosted?.cached ?? summary?.hostedCached ?? false
  const isHostedSuccess = hosted?.status === 'SUCCESS' || hosted?.status === 'EMPTY'
  const isHostedFailed = hosted?.status === 'ERROR' || hosted?.status === 'UNAVAILABLE'

  // If no comparison data is available for this complaint
  if (!comparison && !hosted) {
    return (
      <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-2.5">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#11162A] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[#6457E8]" />
            <span>Vision Model Comparison</span>
          </span>
          <span className="text-[10px] font-mono text-[#65708B] bg-slate-100 px-2 py-0.5 rounded border border-[#E4E7F1]">
            Side-by-Side Evaluation
          </span>
        </div>

        <div className="p-3.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] flex items-start gap-3 text-xs text-[#65708B]">
          <Info className="w-4 h-4 text-[#6457E8] shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-semibold text-[#11162A]">No hosted comparison is available for this complaint.</p>
            <p className="text-[11px] text-[#65708B] leading-relaxed">
              This grievance was processed using the standard production detector ({issue.visionModel || 'Local YOLO'}). Roboflow hosted comparisons are captured when comparison mode is active during complaint submission.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3.5">
      {/* 1. Header & Semantic Identification */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E4E7F1] pb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-[#6457E8]/10 text-[#6457E8] rounded-lg">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-[#11162A]">Vision Model Comparison</h4>
            <p className="text-[11px] text-[#65708B]">
              Production Baseline (Local YOLO) vs. Candidate (Roboflow Hosted Serverless)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <ShieldCheck className="w-3 h-3" />
            <span>Baseline Active</span>
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-50 text-[#6457E8] border border-indigo-200">
            <Sparkles className="w-3 h-3" />
            <span>Candidate Monitored</span>
          </span>
        </div>
      </div>

      {/* 2. Failure Handling Alert (if hosted inference failed) */}
      {isHostedFailed && (
        <div className="p-3 bg-amber-50/80 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="flex items-center gap-2 font-semibold text-amber-950">
              <span>Hosted Candidate Unavailable ({hosted?.errorCategory || 'API_ERROR'})</span>
              <span className="text-[10px] font-mono bg-amber-200/60 px-1.5 py-0.5 rounded text-amber-800">
                Status: {hosted?.status || 'ERROR'}
              </span>
            </div>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              {hosted?.error || 'Roboflow serverless gateway was unreachable or returned an error status during complaint ingestion.'}
            </p>
            <p className="text-[10px] text-amber-700 font-medium">
              ✓ Production Baseline (Local YOLO) gracefully preserved issue triage, visual severity, and dynamic priority.
            </p>
          </div>
        </div>
      )}

      {/* 3. Comparison Metric Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
        {/* Metric 1: Detections Count */}
        <div className="p-2.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-1">
          <span className="text-[10px] font-medium text-[#65708B] uppercase tracking-wider block">
            Detections
          </span>
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[11px] text-[#65708B] block">Baseline</span>
              <span className="text-sm font-bold font-mono text-[#11162A]">{localDetections.length}</span>
            </div>
            <span className="text-xs text-[#65708B]">vs</span>
            <div className="text-right">
              <span className="text-[11px] text-[#65708B] block">Hosted</span>
              <span className="text-sm font-bold font-mono text-[#6457E8]">
                {isHostedSuccess ? hostedDetections.length : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 2: Primary Confidence */}
        <div className="p-2.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-1">
          <span className="text-[10px] font-medium text-[#65708B] uppercase tracking-wider block">
            Max Confidence
          </span>
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[11px] text-[#65708B] block">Baseline</span>
              <span className="text-sm font-bold font-mono text-[#11162A]">
                {localConfidence > 0 ? `${(localConfidence * 100).toFixed(1)}%` : '0.0%'}
              </span>
            </div>
            <span className="text-xs text-[#65708B]">vs</span>
            <div className="text-right">
              <span className="text-[11px] text-[#65708B] block">Hosted</span>
              <span className="text-sm font-bold font-mono text-[#6457E8]">
                {isHostedSuccess && hostedConfidence > 0 ? `${(hostedConfidence * 100).toFixed(1)}%` : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 3: Latency */}
        <div className="p-2.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-1">
          <span className="text-[10px] font-medium text-[#65708B] uppercase tracking-wider block">
            Inference Latency
          </span>
          <div className="flex items-baseline justify-between">
            <div>
              <span className="text-[11px] text-[#65708B] block">Baseline</span>
              <span className="text-sm font-bold font-mono text-[#11162A]">{localLatency.toFixed(1)} ms</span>
            </div>
            <span className="text-xs text-[#65708B]">vs</span>
            <div className="text-right">
              <span className="text-[11px] text-[#65708B] block">Hosted</span>
              <span className="text-sm font-bold font-mono text-[#6457E8]">
                {isHostedSuccess ? `${hostedLatency.toFixed(1)} ms` : '—'}
              </span>
            </div>
          </div>
        </div>

        {/* Metric 4: Request Telemetry */}
        <div className="p-2.5 bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] space-y-1">
          <span className="text-[10px] font-medium text-[#65708B] uppercase tracking-wider block">
            Gateway Telemetry
          </span>
          <div>
            <span className="text-[11px] font-mono text-[#11162A] font-semibold block truncate">
              {hosted?.status || 'N/A'}
            </span>
            <span className="text-[10px] font-mono text-[#65708B] block truncate">
              {isHostedCached ? 'Cached (SHA-256)' : 'Live HTTP Call'}
            </span>
          </div>
        </div>
      </div>

      {/* Ground-truth caveat disclaimer */}
      <div className="px-3 py-1.5 bg-slate-50 border border-slate-200/80 rounded-lg text-[11px] text-[#65708B] flex items-center gap-2">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span className="leading-tight">
          <strong>Evaluation Policy:</strong> Confidence values are model-internal scores and are presented without synthetic assumptions or accuracy claims prior to ground-truth verification.
        </span>
      </div>

      {/* 4. Interactive Bounding Box Inspector */}
      {issue.imageUrl && (
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#11162A] flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5 text-[#6457E8]" />
              <span>Inspection Viewport</span>
            </span>

            {/* Model Toggle Tabs */}
            <div className="inline-flex p-0.5 rounded-lg bg-[#F0F2F9] border border-[#E4E7F1] text-xs">
              <button
                type="button"
                onClick={() => setActiveModelTab('local')}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                  activeModelTab === 'local'
                    ? 'bg-[#13152E] text-white shadow-xs'
                    : 'text-[#65708B] hover:text-[#11162A]'
                }`}
              >
                <span>🚗 Local Baseline</span>
                <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono bg-white/20">
                  {localDetections.length}
                </span>
              </button>

              <button
                type="button"
                onClick={() => setActiveModelTab('hosted')}
                disabled={isHostedFailed}
                className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition cursor-pointer flex items-center gap-1.5 ${
                  activeModelTab === 'hosted'
                    ? 'bg-[#6457E8] text-white shadow-xs'
                    : isHostedFailed
                    ? 'opacity-40 cursor-not-allowed text-[#65708B]'
                    : 'text-[#65708B] hover:text-[#11162A]'
                }`}
              >
                <span>⚡ Roboflow Hosted</span>
                <span className="px-1.5 py-0.2 rounded-full text-[9px] font-mono bg-white/20">
                  {isHostedSuccess ? hostedDetections.length : '0'}
                </span>
              </button>
            </div>
          </div>

          {/* Active Model Indicator Tag */}
          <div className="flex items-center justify-between text-[11px] px-1 text-[#65708B]">
            <span>
              Viewing output for:{' '}
              <strong className="text-[#11162A]">
                {activeModelTab === 'local'
                  ? `${localModelName} (Production)`
                  : `${hostedModelId} (Candidate)`}
              </strong>
            </span>
            <span className="text-[10px] text-[#65708B] italic">
              Models displayed independently to avoid visual clutter
            </span>
          </div>

          {/* Image Canvas with Overlay Bounding Boxes */}
          <div className="relative rounded-xl overflow-hidden border border-[#212348] bg-[#10162A] flex items-center justify-center min-h-[220px]">
            <img
              src={
                issue.imageUrl.startsWith('/') ||
                issue.imageUrl.startsWith('http') ||
                issue.imageUrl.startsWith('blob:')
                  ? issue.imageUrl
                  : `/${issue.imageUrl}`
              }
              alt="Model Comparison Target"
              className="w-full max-h-72 object-contain"
              onError={(e) => {
                ;(e.target as HTMLElement).style.display = 'none'
              }}
            />

            {/* Render Local Model Boxes */}
            {activeModelTab === 'local' && (
              <>
                {localDetections.length > 0 ? (
                  localDetections.map((obj, idx) => {
                    const [ymin, xmin, ymax, xmax] = obj.bbox || [0.25, 0.25, 0.75, 0.75]
                    const top = `${ymin * 100}%`
                    const left = `${xmin * 100}%`
                    const width = `${Math.max(6, (xmax - xmin) * 100)}%`
                    const height = `${Math.max(6, (ymax - ymin) * 100)}%`
                    return (
                      <div
                        key={idx}
                        style={{ top, left, width, height }}
                        className="absolute z-10 border-2 border-[#8B5CF6] bg-[#6457E8]/20 backdrop-blur-xs rounded-md shadow-lg pointer-events-none flex flex-col justify-between p-1"
                      >
                        <span className="text-[10px] bg-[#6457E8] text-white px-1.5 py-0.5 rounded font-semibold uppercase tracking-tight self-start truncate max-w-full">
                          {obj.label}
                        </span>
                        <span className="text-[9px] bg-black/75 text-indigo-200 font-mono px-1 rounded self-end">
                          {(obj.confidence * 100).toFixed(1)}% (Local)
                        </span>
                      </div>
                    )
                  })
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-4">
                    <div className="p-3 bg-black/70 border border-slate-700 rounded-lg text-center backdrop-blur-xs max-w-xs">
                      <span className="text-xs text-slate-200 font-semibold block">
                        No Targets Detected by Local YOLO
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                        {localModelName} &bull; Below threshold or clear surface
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Render Hosted Candidate Boxes */}
            {activeModelTab === 'hosted' && (
              <>
                {hostedDetections.length > 0 ? (
                  hostedDetections.map((obj, idx) => {
                    const [ymin, xmin, ymax, xmax] = obj.bbox || [0.25, 0.25, 0.75, 0.75]
                    const top = `${ymin * 100}%`
                    const left = `${xmin * 100}%`
                    const width = `${Math.max(6, (xmax - xmin) * 100)}%`
                    const height = `${Math.max(6, (ymax - ymin) * 100)}%`
                    return (
                      <div
                        key={idx}
                        style={{ top, left, width, height }}
                        className="absolute z-10 border-2 border-[#06B6D4] bg-[#06B6D4]/20 backdrop-blur-xs rounded-md shadow-lg pointer-events-none flex flex-col justify-between p-1"
                      >
                        <span className="text-[10px] bg-[#0891B2] text-white px-1.5 py-0.5 rounded font-semibold uppercase tracking-tight self-start truncate max-w-full">
                          {obj.label}
                        </span>
                        <span className="text-[9px] bg-black/75 text-cyan-200 font-mono px-1 rounded self-end">
                          {(obj.confidence * 100).toFixed(1)}% (Hosted)
                        </span>
                      </div>
                    )
                  })
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none p-4">
                    <div className="p-3 bg-black/70 border border-slate-700 rounded-lg text-center backdrop-blur-xs max-w-xs">
                      <span className="text-xs text-slate-200 font-semibold block">
                        No Targets Detected by Hosted Model
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">
                        {hostedModelId} &bull; Serverless RF inference returned 0 boxes
                      </span>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* 5. Separated Model Panels (A vs B) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
        {/* Panel A: Production Baseline */}
        <div className="p-3.5 bg-slate-50/70 border border-[#E4E7F1] rounded-xl space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#E4E7F1] pb-2">
            <span className="text-xs font-bold text-[#11162A] flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              <span>Production Baseline</span>
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100/70 text-emerald-800">
              Active in Scoring
            </span>
          </div>

          <div className="space-y-1.5 text-xs text-[#65708B]">
            <div className="flex items-center justify-between">
              <span>Model Name:</span>
              <span className="font-mono font-semibold text-[#11162A]">{localModelName}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Runtime Mode:</span>
              <span className="font-mono text-[#11162A]">
                {local?.visionExecutionMode || issue.visionMode || 'real_yolo_inference'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Detected Targets:</span>
              <span className="font-mono font-semibold text-[#11162A]">
                {localDetections.length > 0 ? `${localDetections.length} item(s)` : 'None detected'}
              </span>
            </div>
            {localClasses.length > 0 && (
              <div className="pt-1 flex flex-wrap gap-1">
                {localClasses.map((cls, idx) => (
                  <span key={idx} className="px-1.5 py-0.5 rounded bg-white border border-[#E4E7F1] text-[10px] font-mono text-[#11162A]">
                    {cls}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="p-2 bg-emerald-50/80 rounded-lg border border-emerald-200/80 text-[11px] text-emerald-900 leading-tight">
            <strong>System Impact:</strong> Authoritative baseline. Drives visual severity scoring ({issue.priorityBreakdown?.visualSeverity !== undefined ? `${Number(issue.priorityBreakdown.visualSeverity).toFixed(1)} / 20 pts` : 'Active'}) and municipal department dispatch.
          </div>
        </div>

        {/* Panel B: Roboflow Hosted Candidate */}
        <div className="p-3.5 bg-slate-50/70 border border-[#E4E7F1] rounded-xl space-y-2.5">
          <div className="flex items-center justify-between border-b border-[#E4E7F1] pb-2">
            <span className="text-xs font-bold text-[#11162A] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#6457E8]" />
              <span>Roboflow Hosted Candidate</span>
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-100/70 text-[#6457E8]">
              Experimental Comparison
            </span>
          </div>

          <div className="space-y-1.5 text-xs text-[#65708B]">
            <div className="flex items-center justify-between">
              <span>Model ID:</span>
              <span className="font-mono font-semibold text-[#11162A] truncate max-w-[180px]">
                {hostedModelId}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Architecture:</span>
              <span className="font-mono text-[#11162A]">{hostedArchitecture}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>API Gateway:</span>
              <span className="font-mono text-[#11162A]">serverless.roboflow.com</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Request Status:</span>
              <span className="font-mono font-semibold text-[#11162A]">
                {hosted?.status || 'N/A'} {isHostedSuccess ? '(HTTP 200)' : ''}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Inference Source:</span>
              <span className="font-mono text-[#11162A]">
                {isHostedCached ? 'SHA-256 Local Cache' : 'Live Outbound HTTP Call'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span>Candidate Targets:</span>
              <span className="font-mono font-semibold text-[#6457E8]">
                {isHostedSuccess ? `${hostedDetections.length} item(s)` : 'Unavailable'}
              </span>
            </div>
            {hostedClasses.length > 0 && (
              <div className="pt-1 flex flex-wrap gap-1">
                {hostedClasses.map((cls, idx) => (
                  <span key={idx} className="px-1.5 py-0.5 rounded bg-white border border-[#E4E7F1] text-[10px] font-mono text-[#6457E8]">
                    {cls}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="p-2 bg-indigo-50/80 rounded-lg border border-indigo-200/80 text-[11px] text-[#6457E8] leading-tight">
            <strong>System Impact:</strong> Read-only experimental telemetry. Zero mutation to production priority, severity, or routing logic.
          </div>
        </div>
      </div>
    </div>
  )
}

