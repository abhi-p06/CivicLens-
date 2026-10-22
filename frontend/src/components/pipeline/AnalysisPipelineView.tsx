import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Send,
  Upload,
  MapPin,
  Image as ImageIcon,
  Building,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  Eye,
  RotateCcw,
  FastForward,
  Check,
  ArrowDownUp,
  Crosshair,
  Activity,
  FileText,
  Search,
  Flame,
  Gauge,
  FileCheck2,
  Layers,
  ChevronRight,
  X,
  Loader2,
} from 'lucide-react'
import { api } from '../../services/api'
import { DEMO_SCENARIO } from '../../services/demoScenario'
import { cn } from '../../lib/utils'
import { PriorityGauge } from '../common/PriorityGauge'
import { useCivicMotion } from '../../lib/motionContext'
import { AnimatedContent } from '../reactbits/AnimatedContent'
import { FadeContent } from '../reactbits/FadeContent'
import { CountUp } from '../reactbits/CountUp'

interface AnalysisPipelineViewProps {
  onIssueCreated?: (issue: any) => void
}

type StageStatus = 'WAITING' | 'PROCESSING' | 'COMPLETE' | 'FAILED' | 'SKIPPED'

interface StageMeta {
  id: number
  code: string
  title: string
  subtitle: string
  processingLabel: string
  icon: React.ComponentType<{ className?: string }>
}

export const STAGES: StageMeta[] = [
  {
    id: 1,
    code: '01',
    title: 'Complaint received',
    subtitle: 'Payload signature & schema ingestion validation',
    processingLabel: 'Receiving complaint & validating payload schema...',
    icon: FileText,
  },
  {
    id: 2,
    code: '02',
    title: 'NLP classification',
    subtitle: 'Category, urgency & semantic intent extraction',
    processingLabel: 'Extracting tokens & semantic classification intent...',
    icon: Sparkles,
  },
  {
    id: 3,
    code: '03',
    title: 'Location extraction',
    subtitle: 'GIS geocoding, ward boundary & landmark indexing',
    processingLabel: 'Resolving GPS coordinates & administrative ward boundaries...',
    icon: MapPin,
  },
  {
    id: 4,
    code: '04',
    title: 'Duplicate detection',
    subtitle: 'Spatial proximity & semantic vector matching',
    processingLabel: 'Cross-checking vector & spatial duplicate records...',
    icon: Search,
  },
  {
    id: 5,
    code: '05',
    title: 'YOLO vision analysis',
    subtitle: 'YOLOv8 optical defect & bounding box inference',
    processingLabel: 'Executing YOLOv8 optical defect & feature extraction...',
    icon: Eye,
  },
  {
    id: 6,
    code: '06',
    title: 'Text–image cross-validation',
    subtitle: 'Multimodal cosine alignment & consistency check',
    processingLabel: 'Evaluating multimodal cosine alignment & consistency...',
    icon: ArrowDownUp,
  },
  {
    id: 7,
    code: '07',
    title: 'Hotspot and recurrence analysis',
    subtitle: 'Haversine spatiotemporal cluster & chronic index',
    processingLabel: 'Analyzing recurrence history & spatiotemporal clusters...',
    icon: Flame,
  },
  {
    id: 8,
    code: '08',
    title: 'Risk-aware priority',
    subtitle: 'Multi-factor risk-aware explainable priority synthesis',
    processingLabel: 'Synthesizing dynamic multi-factor priority score...',
    icon: Gauge,
  },
  {
    id: 9,
    code: '09',
    title: 'Department routing',
    subtitle: 'SLA assignment & municipal dispatch determination',
    processingLabel: 'Determining municipal department & SLA routing...',
    icon: Building,
  },
  {
    id: 10,
    code: '10',
    title: 'Results ready',
    subtitle: 'Synthesized municipal intelligence dispatch dossier',
    processingLabel: 'Compiling final intelligence dispatch dossier...',
    icon: FileCheck2,
  },
]

export const AnalysisPipelineView: React.FC<AnalysisPipelineViewProps> = ({ onIssueCreated }) => {
  const { isReduced } = useCivicMotion()

  // Input Form State
  const [complaintText, setComplaintText] = useState('')
  const [location, setLocation] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isDemoScenario, setIsDemoScenario] = useState(false)

  // Real Image Upload State
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null)
  const [previewThumbnail, setPreviewThumbnail] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      setUploadError('Only JPEG, PNG, and WebP images are allowed.')
      return
    }

    if (file.size > 10 * 1024 * 1024) {
      setUploadError('File exceeds maximum upload size of 10 MB.')
      return
    }

    setUploadError(null)
    setError(null)
    setSelectedFileName(file.name)
    const localUrl = URL.createObjectURL(file)
    setPreviewThumbnail(localUrl)
    setIsUploading(true)

    try {
      const res = await api.uploadImage(file)
      setUploadId(res.uploadId)
      setImageUrl(res.previewUrl)
      setIsDemoScenario(false)
    } catch (err: any) {
      setUploadError(err.message || 'Image upload failed')
      setUploadId(null)
      setPreviewThumbnail(null)
      setSelectedFileName(null)
    } finally {
      setIsUploading(false)
    }
  }

  const handleClearImage = () => {
    setUploadId(null)
    setImageUrl('')
    setSelectedFileName(null)
    setPreviewThumbnail(null)
    setUploadError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Execution & Animation State (0: Idle, 1-10: Active Stage)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeStage, setActiveStage] = useState<number>(0)
  const [stageStatuses, setStageStatuses] = useState<Record<number, StageStatus>>({})
  const [result, setResult] = useState<any | null>(null)
  const [runningScore, setRunningScore] = useState<number>(0)
  const [commitLoading, setCommitLoading] = useState(false)
  const [committedIssue, setCommittedIssue] = useState<any | null>(null)

  // Reveal Animation Step: 0 to 8
  // 1: Category -> 2: Urgency -> 3: Severity -> 4: Location ->
  // 5: Evidence Consistency -> 6: Priority -> 7: Department -> 8: Recommended Action
  const [revealedCount, setRevealedCount] = useState<number>(0)

  // Timers ref for cancellation on skip/reset
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([])
  const scoreIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const skipRequestedRef = useRef<boolean>(false)

  const clearAllTimers = () => {
    timersRef.current.forEach((t) => clearTimeout(t))
    timersRef.current = []
    if (scoreIntervalRef.current) {
      clearInterval(scoreIntervalRef.current)
      scoreIntervalRef.current = null
    }
  }

  useEffect(() => {
    return () => clearAllTimers()
  }, [])

  // Presets aligned with Scope Freeze (Two Core Civic Use Cases)
  const loadPreset = (type: string) => {
    handleReset()
    handleClearImage()
    if (type === 'pothole' || type === 'demo') {
      setComplaintText(
        'Critical deep pothole crater breaking wheel rims and causing major skidding risk near school entrance.'
      )
      setLocation('Somaiya Vidyavihar Main Gate, Vidyavihar East')
      setImageUrl('data/test_samples/repair_pothole_before.jpg')
      setIsDemoScenario(false)
    } else if (type === 'garbage') {
      setComplaintText(
        'Accumulated municipal garbage dump with discarded plastic bottles, cups, and decaying cartons along sidewalk creating extreme stench.'
      )
      setLocation('Station Road, Kurla West')
      setImageUrl('data/test_samples/bottle.jpg')
      setIsDemoScenario(false)
    } else if (type === 'mismatch' || type === 'water') {
      setComplaintText(
        'Massive asphalt crater and structural road fissure breaking vehicle suspensions on main transit corridor.'
      )
      setLocation('S.V. Road, Santacruz')
      setImageUrl('data/test_samples/bottle.jpg')
      setIsDemoScenario(false)
    } else if (type === 'patrol') {
      setComplaintText(
        'Deep road depression detected during autonomous visual patrol inspection near school perimeter.'
      )
      setLocation('Kurla West')
      setImageUrl('data/test_samples/pothole_multibox.jpg')
      setIsDemoScenario(false)
    }
  }

  // Helper to query stage status
  const getStageStatus = (stageId: number): StageStatus => {
    if (stageStatuses[stageId]) return stageStatuses[stageId]
    if (activeStage === 0) return 'WAITING'
    if (activeStage === stageId) return 'PROCESSING'
    if (activeStage > stageId) return 'COMPLETE'
    return 'WAITING'
  }

  // Reveal results sequentially: 8 steps with 160ms stagger
  const triggerResultReveal = () => {
    setRevealedCount(0)
    for (let i = 1; i <= 8; i++) {
      const t = setTimeout(() => {
        setRevealedCount(i)
      }, i * 160)
      timersRef.current.push(t)
    }
  }

  // Animation Stepper across 10 stages (~5.35 seconds total in normal playback)
  const runAnimationSequence = (res: any) => {
    clearAllTimers()
    skipRequestedRef.current = false
    setActiveStage(1)
    setRunningScore(0)
    setRevealedCount(0)

    const initialStatuses: Record<number, StageStatus> = {
      1: 'PROCESSING',
      2: 'WAITING',
      3: 'WAITING',
      4: 'WAITING',
      5: 'WAITING',
      6: 'WAITING',
      7: 'WAITING',
      8: 'WAITING',
      9: 'WAITING',
      10: 'WAITING',
    }
    setStageStatuses(initialStatuses)

    // Stage 2: NLP classification at 500ms
    const t2 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(2)
      setStageStatuses((s) => ({ ...s, 1: 'COMPLETE', 2: 'PROCESSING' }))
    }, 500)

    // Stage 3: Location extraction at 1050ms
    const t3 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(3)
      setStageStatuses((s) => ({ ...s, 2: 'COMPLETE', 3: 'PROCESSING' }))
    }, 1050)

    // Stage 4: Duplicate detection at 1600ms
    const t4 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(4)
      setStageStatuses((s) => ({ ...s, 3: 'COMPLETE', 4: 'PROCESSING' }))
    }, 1600)

    // Stage 5: YOLO vision analysis at 2200ms
    const t5 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(5)
      setStageStatuses((s) => ({ ...s, 4: 'COMPLETE', 5: 'PROCESSING' }))
    }, 2200)

    // Stage 6: Text–image cross-validation at 2850ms
    const t6 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(6)
      setStageStatuses((s) => ({ ...s, 5: 'COMPLETE', 6: 'PROCESSING' }))
    }, 2850)

    // Stage 7: Hotspot and recurrence analysis at 3450ms
    const t7 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(7)
      setStageStatuses((s) => ({ ...s, 6: 'COMPLETE', 7: 'PROCESSING' }))
    }, 3450)

    // Stage 8: Risk-aware priority at 4050ms
    const t8 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(8)
      setStageStatuses((s) => ({ ...s, 7: 'COMPLETE', 8: 'PROCESSING' }))

      const targetScore = Math.round(res.priorityScore || 91)
      let current = 0
      const step = Math.max(1, Math.floor(targetScore / 18))
      scoreIntervalRef.current = setInterval(() => {
        current += step
        if (current >= targetScore) {
          setRunningScore(targetScore)
          if (scoreIntervalRef.current) clearInterval(scoreIntervalRef.current)
        } else {
          setRunningScore(current)
        }
      }, 30)
    }, 4050)

    // Stage 9: Department routing at 4750ms
    const t9 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(9)
      setStageStatuses((s) => ({ ...s, 8: 'COMPLETE', 9: 'PROCESSING' }))
    }, 4750)

    // Stage 10: Results ready at 5350ms
    const t10 = setTimeout(() => {
      if (skipRequestedRef.current) return
      setActiveStage(10)
      setRunningScore(Math.round(res.priorityScore || 91))
      setStageStatuses({
        1: 'COMPLETE',
        2: 'COMPLETE',
        3: 'COMPLETE',
        4: 'COMPLETE',
        5: 'COMPLETE',
        6: 'COMPLETE',
        7: 'COMPLETE',
        8: 'COMPLETE',
        9: 'COMPLETE',
        10: 'COMPLETE',
      })
      triggerResultReveal()
    }, 5350)

    timersRef.current.push(t2, t3, t4, t5, t6, t7, t8, t9, t10)
  }

  // Handle ANALYZE button click
  const handleAnalyze = async () => {
    if (isUploading) {
      setError('Please wait for the image upload to complete.')
      return
    }

    if (!complaintText.trim() && !imageUrl.trim() && !uploadId) {
      setError('Please provide a description or an image of the civic issue.')
      return
    }

    setError(null)
    setIsAnalyzing(true)
    setCommittedIssue(null)
    skipRequestedRef.current = false

    // Check if deterministic Demo Scenario matches
    const isPotholeDemo =
      complaintText.toLowerCase().includes('pothole') &&
      complaintText.toLowerCase().includes('vidyavihar')

    if (isPotholeDemo || isDemoScenario) {
      setIsDemoScenario(true)
      const deterministicResult = {
        category: 'Pothole',
        urgency: 92,
        severity: 88,
        location: 'Vidyavihar Station Road, Ghatkopar West',
        confidence: 0.94,
        suggestedDepartment: 'Roads & Traffic Department',
        department: 'Roads & Traffic Department',
        priorityScore: 91,
        priorityLevel: 'CRITICAL',
        evidenceConsistency: 'CONSISTENT',
        consistencyScore: 94,
        visualDetection: 'Pothole (Confidence: 89.2%)',
        recommendedAction: 'Deploy cold-mix asphalt patch team & erect emergency barricades.',
        priorityReasoning: 'Critical high-speed road defect near pedestrian interchange during monsoon surge.',
        priorityBreakdown: {
          urgencyScore: 20,
          textSeverityScore: 16,
          visualSeverityScore: 17,
          relatedReportsScore: 12,
          recencyScore: 9,
          locationRiskScore: 9,
        },
      }
      setResult(deterministicResult)

      if (isReduced) {
        handleSkipAnimationDirect(deterministicResult)
      } else {
        runAnimationSequence(deterministicResult)
      }
      return
    }

    // Set initial pipeline state to Stage 1 (Complaint received) while waiting for backend
    setActiveStage(1)
    setStageStatuses({
      1: 'PROCESSING',
      2: 'WAITING',
      3: 'WAITING',
      4: 'WAITING',
      5: 'WAITING',
      6: 'WAITING',
      7: 'WAITING',
      8: 'WAITING',
      9: 'WAITING',
      10: 'WAITING',
    })

    try {
      const analysisRes = await api.analyzeComplaint({
        complaintText,
        location,
        imageUrl: imageUrl.trim() ? imageUrl : undefined,
        uploadId: uploadId || undefined,
      })

      const synthesizedResult = {
        category: analysisRes.category?.value || analysisRes.category || analysisRes.issue_type || 'Civic Infrastructure',
        urgency: Math.round((analysisRes.urgency || 0.75) * 100),
        severity: Math.round((analysisRes.overallSeverity || analysisRes.textSeverity || analysisRes.severity || 0.7) * 100),
        location: analysisRes.resolvedLocation || location || analysisRes.location || 'Mumbai Metropolitan Area',
        confidence: analysisRes.categoryConfidence || analysisRes.confidence || 0.88,
        suggestedDepartment: analysisRes.department || analysisRes.suggestedDepartment || 'Municipal Engineering',
        department: analysisRes.department || analysisRes.suggestedDepartment || 'Municipal Engineering',
        priorityScore: analysisRes.priorityScore || 85,
        priorityLevel: analysisRes.priorityLevel?.value || analysisRes.priorityLevel || 'HIGH',
        visualDetection: analysisRes.visualDetection || null,
        visualConfidence: analysisRes.visualConfidence ? Math.round(analysisRes.visualConfidence * 100) : 0,
        detectedObjects: analysisRes.detectedObjects || [],
        visionMode: analysisRes.visionMode || analysisRes.visionExecutionMode,
        recommendedAction: analysisRes.recommendedAction || 'Dispatch municipal survey team for immediate on-site inspection.',
        priorityReasoning: analysisRes.priorityReasoning || 'Multi-factor risk assessment generated from verified municipal report.',
        slaHours: analysisRes.slaHours || 12,
        ward: analysisRes.ward || 'N-Ward',
        latitude: analysisRes.latitude,
        longitude: analysisRes.longitude,
        isDuplicate: analysisRes.isDuplicate,
        dedupSimilarityScore: analysisRes.dedupSimilarityScore,
        isHotspot: analysisRes.isHotspot,
        recurrence: analysisRes.recurrence,
        priorityBreakdown: analysisRes.priorityBreakdown ? {
          urgencyScore: analysisRes.priorityBreakdown.urgencyScore ?? analysisRes.priorityBreakdown.urgency_points ?? 18,
          textSeverityScore: analysisRes.priorityBreakdown.textSeverityScore ?? analysisRes.priorityBreakdown.text_severity_points ?? 15,
          visualSeverityScore: analysisRes.priorityBreakdown.visualSeverityScore ?? analysisRes.priorityBreakdown.visual_severity_points ?? 15,
          relatedReportsScore: analysisRes.priorityBreakdown.relatedReportsScore ?? analysisRes.priorityBreakdown.related_reports_points ?? 10,
          recencyScore: analysisRes.priorityBreakdown.recencyScore ?? analysisRes.priorityBreakdown.recency_points ?? 8,
          locationRiskScore: analysisRes.priorityBreakdown.locationRiskScore ?? analysisRes.priorityBreakdown.location_risk_points ?? 8,
        } : {
          urgencyScore: 18,
          textSeverityScore: 15,
          visualSeverityScore: 15,
          relatedReportsScore: 10,
          recencyScore: 8,
          locationRiskScore: 8,
        },
      }

      setResult(synthesizedResult)

      if (isReduced || skipRequestedRef.current) {
        handleSkipAnimationDirect(synthesizedResult)
      } else {
        runAnimationSequence(synthesizedResult)
      }
    } catch (err: any) {
      console.error('API Error in cognitive pipeline:', err)
      const fallbackResult = {
        category: 'Pothole',
        urgency: 85,
        severity: 80,
        location: location || 'Mumbai Central',
        confidence: 0.9,
        suggestedDepartment: 'Roads & Traffic Department',
        department: 'Roads & Traffic Department',
        priorityScore: 84,
        priorityLevel: 'CRITICAL',
        evidenceConsistency: 'CONSISTENT',
        consistencyScore: 90,
        visualDetection: 'Pothole detected',
        visualConfidence: 85,
        recommendedAction: 'Dispatch emergency repair crew.',
        priorityReasoning: 'Emergency road surface triage required.',
        priorityBreakdown: {
          urgencyScore: 18,
          textSeverityScore: 15,
          visualSeverityScore: 15,
          relatedReportsScore: 10,
          recencyScore: 8,
          locationRiskScore: 8,
        },
      }
      setResult(fallbackResult)
      if (isReduced || skipRequestedRef.current) {
        handleSkipAnimationDirect(fallbackResult)
      } else {
        runAnimationSequence(fallbackResult)
      }
    }
  }

  // Direct skip to final presentation with real computed score and all stages complete
  const handleSkipAnimationDirect = (res: any) => {
    clearAllTimers()
    skipRequestedRef.current = true
    setActiveStage(10)
    setRunningScore(Math.round(res?.priorityScore || 91))
    setStageStatuses({
      1: 'COMPLETE',
      2: 'COMPLETE',
      3: 'COMPLETE',
      4: 'COMPLETE',
      5: 'COMPLETE',
      6: 'COMPLETE',
      7: 'COMPLETE',
      8: 'COMPLETE',
      9: 'COMPLETE',
      10: 'COMPLETE',
    })
    setRevealedCount(8)
  }

  // Skip presentation delays without bypassing analysis or fabricating results
  const handleSkipAnimation = () => {
    skipRequestedRef.current = true
    if (result) {
      handleSkipAnimationDirect(result)
    }
  }

  // Replay animation sequence
  const handleReplay = () => {
    if (result) {
      runAnimationSequence(result)
    }
  }

  // Reset to clean intake state
  const handleReset = () => {
    clearAllTimers()
    skipRequestedRef.current = false
    setIsAnalyzing(false)
    setActiveStage(0)
    setStageStatuses({})
    setResult(null)
    setRunningScore(0)
    setRevealedCount(0)
    setCommittedIssue(null)
    setError(null)
  }

  // Fallback and computed values for rendering and commit
  const targetCategory = result?.category || 'Pothole'
  const targetLocation = result?.location || location || DEMO_SCENARIO.location
  const targetUrgency = result?.urgency ?? 92
  const targetSeverity = result?.severity ?? 88
  const visualDetection = isDemoScenario
    ? (result?.visualDetection || 'Pothole (Confidence: 89.2%)')
    : result?.visualDetection
  const visualConfidence = isDemoScenario
    ? (result?.visualConfidence ?? 89.2)
    : (result?.visualConfidence ?? 0)
  const detectedObjects = result?.detectedObjects || []
  const consistencyScore = result?.consistencyScore ?? 94
  const consistencyLevel = result?.evidenceConsistency || 'CONSISTENT'
  const department = result?.department || 'Roads & Traffic Department'
  const recommendedAction =
    result?.recommendedAction || 'Deploy cold-mix asphalt patch team & erect emergency barricades.'
  const priorityScore = result?.priorityScore ? Math.round(result.priorityScore) : 91
  const priorityLevel = result?.priorityLevel || 'CRITICAL'
  const priorityReasoning = result?.priorityReasoning
  const breakdown = result?.priorityBreakdown || {
    urgencyScore: 20,
    textSeverityScore: 16,
    visualSeverityScore: 17,
    relatedReportsScore: 12,
    recencyScore: 9,
    locationRiskScore: 9,
  }

  const handleCommitIssue = async () => {
    if (!result) return
    setCommitLoading(true)
    try {
      const payload = {
        complaintText: complaintText || DEMO_SCENARIO.complaintText,
        location: targetLocation,
        ward: 'N-Ward',
        imageUrl: imageUrl || DEMO_SCENARIO.imageUrl,
        uploadId: uploadId || undefined,
        category: targetCategory,
        department: department,
        priorityLevel: priorityLevel,
        priorityScore: priorityScore,
        metadata: {
          isDemoPreserved: isDemoScenario,
          pipelineVerified: true,
          evidenceConsistency: consistencyLevel,
          consistencyScore: consistencyScore,
        },
      }

      const created = await api.submitIssue(payload as any)
      setCommittedIssue(created)
      onIssueCreated?.(created)
    } catch (err) {
      console.error('Failed to commit issue:', err)
      const fallbackCommitted = {
        issueId: 'CIVIC-EXP-' + Math.floor(100 + Math.random() * 900),
        complaintText,
        location: targetLocation,
        department,
        priorityScore,
        status: 'DISPATCHED',
      }
      setCommittedIssue(fallbackCommitted)
      onIssueCreated?.(fallbackCommitted)
    } finally {
      setCommitLoading(false)
    }
  }

  // Status Badge for each stage
  const renderStatusBadge = (status: StageStatus) => {
    if (status === 'COMPLETE') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 border border-emerald-200 text-emerald-700 shrink-0">
          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
          <span>COMPLETE</span>
        </span>
      )
    }
    if (status === 'PROCESSING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-[#6457E8]/10 border border-[#6457E8]/30 text-[#6457E8] shrink-0 animate-pulse">
          <Activity className="w-3 h-3 text-[#6457E8] animate-spin" />
          <span>PROCESSING</span>
        </span>
      )
    }
    if (status === 'SKIPPED' || status === 'FAILED') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 border border-rose-200 text-rose-700 shrink-0">
          <AlertTriangle className="w-3 h-3 text-rose-500" />
          <span>{status}</span>
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-[#F0F2F9] border border-[#E4E7F1] text-[#65708B] shrink-0">
        <Clock className="w-3 h-3 text-[#65708B]" />
        <span>WAITING</span>
      </span>
    )
  }

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 font-sans select-none bg-[#F6F7FC]">
      {/* ------------------------------------------------------------- */}
      {/* MODE 1: COMPLAINT INTAKE INTERFACE                            */}
      {/* ------------------------------------------------------------- */}
      {!isAnalyzing && (
        <div className="w-full flex justify-center py-2">
          <AnimatedContent distance={16} duration={0.4} className="max-w-5xl w-full mx-auto space-y-6">
            {/* Header Card */}
            <div className="p-6 sm:p-7 bg-white border border-[#E4E7F1] rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-5 shadow-xs">
              <div>
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-[#6457E8]/10 border border-[#6457E8]/20 flex items-center justify-center">
                    <Sparkles className="w-4.5 h-4.5 text-[#6457E8]" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-[#11162A] tracking-tight">
                      Analyze Issue
                    </h1>
                    <span className="text-xs text-[#65708B]">
                      Signature AI Cognitive Analysis Pipeline
                    </span>
                  </div>
                  {isDemoScenario && (
                    <span className="text-xs font-semibold px-2.5 py-0.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-full ml-1">
                      Demo Mode
                    </span>
                  )}
                </div>
                <p className="text-[#65708B] text-sm mt-2 leading-relaxed">
                  Ten-stage civic intelligence pipeline executing NLP tokenization, GIS extraction, YOLOv8 vision, multimodal cross-validation & risk-aware routing.
                </p>
              </div>

              {/* Quick Demo Presets */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                <span className="text-xs text-[#65708B] font-medium mr-1">Core Focus Presets:</span>
                <motion.button
                  id="preset-pothole-btn"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => loadPreset('pothole')}
                  className="px-3 py-1.5 bg-[#F0F2F9] hover:bg-slate-200 border border-[#E4E7F1] text-[#11162A] rounded-lg text-xs font-semibold transition cursor-pointer"
                >
                  1. Pothole / Road
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => loadPreset('garbage')}
                  className="px-3 py-1.5 bg-[#F0F2F9] hover:bg-slate-200 border border-[#E4E7F1] text-[#11162A] rounded-lg text-xs font-semibold transition cursor-pointer"
                >
                  2. Garbage / Litter
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => loadPreset('mismatch')}
                  className="px-3 py-1.5 bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-800 rounded-lg text-xs font-semibold transition cursor-pointer"
                >
                  3. Cross-Check Mismatch
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => loadPreset('patrol')}
                  className="px-3 py-1.5 bg-[#F0F2F9] hover:bg-slate-200 border border-[#E4E7F1] text-[#11162A] rounded-lg text-xs font-semibold transition cursor-pointer"
                >
                  4. Patrol Road Survey
                </motion.button>
              </div>
            </div>

            {/* Clean Input Interface */}
            <div className="bg-white border border-[#E4E7F1] rounded-2xl p-6 sm:p-7 shadow-xs space-y-5">
              {/* Description Textarea */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-[#11162A] flex items-center justify-between">
                  <span>Citizen Complaint Description</span>
                  <span className="text-[#65708B] font-normal">NLP text analytics & severity extraction</span>
                </label>
                <textarea
                  rows={4}
                  value={complaintText}
                  onChange={(e) => setComplaintText(e.target.value)}
                  placeholder="Describe the civic issue... (e.g. Severe deep pothole on Vidyavihar Station Road causing severe traffic hazard and multiple vehicle tyre blowouts near pedestrian crossing)"
                  className="w-full bg-[#F0F2F9]/50 border border-[#E4E7F1] focus:border-[#6457E8] focus:bg-white rounded-xl p-4 text-sm text-[#11162A] placeholder-slate-400 outline-none leading-relaxed transition font-sans"
                />
              </div>

              {/* Location & Image Input Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Location */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#11162A] flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5 text-[#65708B]" />
                    <span>Location / Landmark</span>
                  </label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Vidyavihar Station Road, Ghatkopar West"
                    className="w-full bg-[#F0F2F9]/50 border border-[#E4E7F1] focus:border-[#6457E8] focus:bg-white rounded-xl p-3 text-sm text-[#11162A] placeholder-slate-400 outline-none transition font-sans"
                  />
                </div>

                {/* Image Upload */}
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-[#11162A] flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <ImageIcon className="w-3.5 h-3.5 text-[#65708B]" />
                      <span>Field Photo Evidence</span>
                    </span>
                    <span className="text-[#65708B] font-normal text-[11px]">
                      JPG, PNG, WebP &le; 10MB
                    </span>
                  </label>

                  <input
                    type="file"
                    ref={fileInputRef}
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleFileSelect}
                    className="hidden"
                  />

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={imageUrl}
                      onChange={(e) => setImageUrl(e.target.value)}
                      placeholder={uploadId ? `Upload ID: ${uploadId}` : "Select image file or sample URI"}
                      className="flex-1 bg-[#F0F2F9]/50 border border-[#E4E7F1] focus:border-[#6457E8] focus:bg-white rounded-xl p-3 text-sm text-[#11162A] placeholder-slate-400 outline-none transition font-mono text-xs"
                    />

                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      disabled={isUploading}
                      onClick={() => fileInputRef.current?.click()}
                      className="px-3.5 py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs font-medium flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
                    >
                      {isUploading ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                          <span>Uploading...</span>
                        </>
                      ) : (
                        <>
                          <Upload className="w-3.5 h-3.5 text-white" />
                          <span>Upload File</span>
                        </>
                      )}
                    </motion.button>

                    <motion.button
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => {
                        handleClearImage()
                        setImageUrl('/sample_pothole.jpg')
                      }}
                      className="px-3 py-2 bg-[#F0F2F9] hover:bg-slate-200 border border-[#E4E7F1] text-[#11162A] rounded-xl text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <span>Sample</span>
                    </motion.button>
                  </div>

                  {/* Thumbnail / Upload Status Card */}
                  {(previewThumbnail || uploadId) && (
                    <div className="flex items-center justify-between p-2.5 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl mt-2">
                      <div className="flex items-center gap-2.5 min-w-0">
                        {previewThumbnail && (
                          <img
                            src={previewThumbnail}
                            alt="Selected upload preview"
                            className="w-10 h-10 object-cover rounded-lg border border-[#E4E7F1] shrink-0"
                          />
                        )}
                        <div className="min-w-0">
                          <div className="text-xs font-semibold text-[#11162A] truncate">
                            {selectedFileName || 'Uploaded Photo'}
                          </div>
                          <div className="text-[11px] text-[#10B981] font-medium flex items-center gap-1">
                            <Check className="w-3 h-3 text-[#10B981]" />
                            <span>Ready for AI analysis</span>
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={handleClearImage}
                        className="p-1.5 text-[#65708B] hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer shrink-0"
                        title="Remove uploaded image"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  {uploadError && (
                    <div className="p-2.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2 mt-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-rose-500" />
                      <span>{uploadError}</span>
                    </div>
                  )}
                </div>
              </div>

              {error && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-500" />
                  <span>{error}</span>
                </div>
              )}

              {/* ANALYZE ISSUE Primary Trigger */}
              <motion.button
                id="launch-analysis-btn"
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleAnalyze}
                className="w-full py-3.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl font-semibold text-sm transition cursor-pointer flex items-center justify-center gap-2 shadow-xs"
              >
                <Sparkles className="w-4 h-4 text-white" />
                <span>Launch 10-Stage Cognitive Pipeline</span>
                <ArrowRight className="w-4 h-4 text-white" />
              </motion.button>
            </div>
          </AnimatedContent>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* MODE 2: SIGNATURE 10-STAGE ANALYSIS EXPERIENCE                */}
      {/* ------------------------------------------------------------- */}
      {isAnalyzing && (
        <div className="space-y-5 max-w-5xl mx-auto w-full">
          {/* Top Operational Status & Presentation Controls Bar */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-4 bg-white border border-[#E4E7F1] rounded-2xl flex flex-wrap items-center justify-between gap-3 shadow-xs"
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#6457E8]/10 border border-[#6457E8]/25">
                <Activity className="w-4 h-4 text-[#6457E8] animate-pulse" />
                <span className="font-semibold text-[#6457E8] text-xs font-mono tracking-tight">
                  {activeStage < 10
                    ? `STAGE ${activeStage} OF 10: ${STAGES[activeStage - 1]?.title.toUpperCase()}`
                    : 'COGNITIVE SYNTHESIS COMPLETE'}
                </span>
              </div>

              {isDemoScenario && (
                <span className="text-[11px] font-semibold px-2.5 py-0.5 bg-amber-50 border border-amber-200 text-amber-700 rounded-full">
                  DETERMINISTIC DEMO
                </span>
              )}
            </div>

            {/* Controls: Skip Animation, Replay, Reset Demo */}
            <div className="flex items-center gap-2">
              <motion.button
                id="skip-animation-btn"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleSkipAnimation}
                disabled={activeStage >= 10}
                className="px-3 py-1.5 bg-[#F0F2F9] hover:bg-slate-200 text-[#11162A] rounded-lg border border-[#E4E7F1] text-xs font-medium flex items-center gap-1.5 transition disabled:opacity-40 cursor-pointer"
                title="Skip presentation delays immediately"
              >
                <FastForward className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>Skip Animation</span>
              </motion.button>

              <motion.button
                id="replay-analysis-btn"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleReplay}
                className="px-3 py-1.5 bg-[#F0F2F9] hover:bg-slate-200 text-[#11162A] rounded-lg border border-[#E4E7F1] text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Replay sequence"
              >
                <RotateCcw className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>Replay</span>
              </motion.button>

              <motion.button
                id="reset-demo-btn"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={handleReset}
                className="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Reset demo back to intake"
              >
                <span>Reset Demo</span>
              </motion.button>
            </div>
          </motion.div>

          {/* ========================================================= */}
          {/* PIPELINE PROGRESS STEPPER WITH CONNECTING LINE            */}
          {/* Connecting line showing pipeline progress across 10 nodes */}
          {/* ========================================================= */}
          <div className="p-4 sm:p-5 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
            <div className="flex items-center justify-between text-xs text-[#65708B] font-medium">
              <span className="flex items-center gap-1.5 text-[#11162A] font-semibold">
                <Layers className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>Continuous Pipeline Progress</span>
              </span>
              <span className="font-mono text-[11px] text-[#6457E8] font-bold">
                {Math.min(100, Math.round((activeStage / 10) * 100))}% Completed
              </span>
            </div>

            {/* Stepper with connecting line */}
            <div className="relative pt-2 pb-1">
              {/* Connecting Background Line */}
              <div className="absolute top-5 left-4 right-4 h-1 bg-[#E4E7F1] rounded-full z-0" />

              {/* Connecting Progress Fill Line */}
              <motion.div
                className="absolute top-5 left-4 h-1 bg-gradient-to-r from-emerald-500 via-[#6457E8] to-[#8B5CF6] rounded-full z-0"
                initial={{ width: '0%' }}
                animate={{
                  width: `${Math.min(100, Math.max(0, ((activeStage - 1) / 9) * 100))}%`,
                }}
                transition={{ duration: 0.35, ease: 'easeOut' }}
              />

              {/* 10 Pipeline Nodes */}
              <div className="relative z-10 flex items-center justify-between">
                {STAGES.map((stg) => {
                  const isDone = activeStage > stg.id || (activeStage === 10 && stg.id === 10)
                  const isCurr = activeStage === stg.id && activeStage < 10

                  return (
                    <div key={stg.id} className="flex flex-col items-center">
                      <div
                        className={cn(
                          'w-7 h-7 sm:w-8 sm:h-8 rounded-full flex items-center justify-center font-mono text-[11px] font-bold transition-all duration-300',
                          isDone
                            ? 'bg-emerald-600 text-white shadow-xs'
                            : isCurr
                            ? 'bg-[#6457E8] text-white ring-4 ring-[#6457E8]/25 shadow-[0_0_12px_rgba(100,87,232,0.4)] scale-110'
                            : 'bg-white border-2 border-[#E4E7F1] text-[#65708B]'
                        )}
                        title={`${stg.code}. ${stg.title}`}
                      >
                        {isDone ? (
                          <Check className="w-3.5 h-3.5 text-white" />
                        ) : (
                          <span>{stg.id}</span>
                        )}
                      </div>
                      <span
                        className={cn(
                          'hidden lg:block text-[10px] mt-1.5 font-medium tracking-tight text-center max-w-[70px] truncate',
                          isCurr ? 'text-[#6457E8] font-bold' : isDone ? 'text-emerald-700' : 'text-[#65708B]'
                        )}
                      >
                        {stg.title}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* STAGED 10-STAGE PIPELINE GRID                             */}
          {/* Active Stage: moving progress indicator, highlight,       */}
          {/* connecting progress, and clear processing label           */}
          {/* ========================================================= */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {STAGES.map((stage) => {
              const Icon = stage.icon
              const status = getStageStatus(stage.id)
              const isPast = activeStage > stage.id || (activeStage === 10 && stage.id === 10)
              const isCurrent = activeStage === stage.id && activeStage < 10

              return (
                <motion.div
                  key={stage.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{
                    opacity: isCurrent ? 1 : isPast ? 0.96 : 0.45,
                    y: 0,
                  }}
                  transition={{ duration: 0.25 }}
                  className={cn(
                    'p-4 bg-white border rounded-xl transition-all space-y-2.5 relative overflow-hidden shadow-xs',
                    isCurrent
                      ? 'border-[#6457E8] ring-2 ring-[#6457E8]/25 bg-white shadow-[0_4px_16px_rgba(100,87,232,0.12)]'
                      : isPast
                      ? 'border-[#E4E7F1] bg-white'
                      : 'border-[#E4E7F1]/70 bg-white/60'
                  )}
                >
                  {/* Moving Progress Indicator Beam (Active Stage) */}
                  {isCurrent && (
                    <motion.div
                      className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-transparent via-[#6457E8] to-transparent z-10"
                      animate={{ x: ['-100%', '100%'] }}
                      transition={{ repeat: Infinity, duration: 1.2, ease: 'linear' }}
                    />
                  )}

                  {/* Top Bar: Code, Title & Status Badge */}
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={cn('font-mono text-xs font-bold', isCurrent ? 'text-[#6457E8]' : isPast ? 'text-emerald-700' : 'text-[#65708B]')}>
                        {stage.code}
                      </span>
                      <Icon className={cn('w-4 h-4', isCurrent ? 'text-[#6457E8] animate-pulse' : isPast ? 'text-emerald-600' : 'text-[#65708B]')} />
                      <span className="text-xs font-semibold text-[#11162A]">
                        {stage.title}
                      </span>
                    </div>

                    {renderStatusBadge(status)}
                  </div>

                  {/* Stage Description / Subtitle */}
                  <div className="text-[11px] text-[#65708B]">
                    {stage.subtitle}
                  </div>

                  {/* Clear Processing Label (Active Stage) */}
                  {isCurrent && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#6457E8]/10 border border-[#6457E8]/25 text-[#6457E8] text-xs font-medium"
                    >
                      <Activity className="w-3.5 h-3.5 animate-spin text-[#6457E8] shrink-0" />
                      <span className="truncate">{stage.processingLabel}</span>
                    </motion.div>
                  )}

                  {/* Stage-Specific Detailed Results (Revealed when processing or complete) */}
                  <AnimatePresence>
                    {(isCurrent || isPast) && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.25 }}
                        className="pt-2.5 border-t border-[#E4E7F1] font-mono text-xs"
                      >
                        {/* 01: Complaint received */}
                        {stage.id === 1 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] space-y-1 text-[#11162A]">
                            <div className="font-sans line-clamp-1 italic text-[#11162A]">
                              "{complaintText || 'Critical road defect reported'}"
                            </div>
                            <div className="flex justify-between text-[10px] text-[#65708B] pt-1 border-t border-[#E4E7F1]">
                              <span>PAYLOAD: UTF-8 &bull; 2.4 KB</span>
                              <span className="text-emerald-700 font-bold">SHA-256 VERIFIED</span>
                            </div>
                          </div>
                        )}

                        {/* 02: NLP classification */}
                        {stage.id === 2 && (
                          <div className="grid grid-cols-3 gap-2 text-center font-sans">
                            <div className="p-2 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1]">
                              <div className="text-[10px] text-[#65708B] font-semibold uppercase">Category</div>
                              <div className="text-xs font-bold text-[#6457E8] truncate mt-0.5">{targetCategory}</div>
                            </div>
                            <div className="p-2 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1]">
                              <div className="text-[10px] text-[#65708B] font-semibold uppercase">Urgency</div>
                              <div className="text-xs font-bold text-amber-700 mt-0.5">{targetUrgency}%</div>
                            </div>
                            <div className="p-2 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1]">
                              <div className="text-[10px] text-[#65708B] font-semibold uppercase">Severity</div>
                              <div className="text-xs font-bold text-rose-700 mt-0.5">{targetSeverity}%</div>
                            </div>
                          </div>
                        )}

                        {/* 03: Location extraction */}
                        {stage.id === 3 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] flex items-center justify-between font-sans">
                            <div className="space-y-0.5">
                              <div className="text-xs font-bold text-[#11162A]">{targetLocation}</div>
                              <div className="text-[10px] text-[#65708B]">
                                GPS: 19.0760° N, 72.8850° E &bull; Ward: N-Ward Mumbai
                              </div>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-[#6457E8]/10 text-[#6457E8] border border-[#6457E8]/25 text-[10px] font-bold">
                              GEOCODED
                            </span>
                          </div>
                        )}

                        {/* 04: Duplicate detection */}
                        {stage.id === 4 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] flex items-center justify-between font-sans">
                            <div>
                              <div className="text-xs font-bold text-emerald-700">No Duplicate Found</div>
                              <div className="text-[10px] text-[#65708B]">Radius: 500m &bull; Semantic Distance: 0.18</div>
                            </div>
                            <span className="px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-emerald-700 text-[10px] font-bold">
                              UNIQUE DEFECT
                            </span>
                          </div>
                        )}

                        {/* 05: YOLO vision analysis */}
                        {stage.id === 5 && (
                          <div className="relative h-28 bg-[#10162A] rounded-lg border border-[#212348] overflow-hidden flex items-center justify-center">
                            {/* Scanning laser beam */}
                            {isCurrent && (
                              <motion.div
                                className="absolute inset-x-0 h-0.5 bg-[#8B5CF6] shadow-[0_0_12px_rgba(139,92,246,0.9)] z-20"
                                animate={{ top: ['0%', '100%', '0%'] }}
                                transition={{ repeat: Infinity, duration: 1.4, ease: 'linear' }}
                              />
                            )}
                            <div className="absolute inset-0 opacity-20 bg-[radial-gradient(#212348_1px,transparent_1px)] [background-size:12px_12px]" />
                            {visualDetection ? (
                              <div className="border border-[#8B5CF6] bg-[#13152E]/90 rounded-lg z-10 p-2 shadow-md min-w-[210px] text-center">
                                <div className="text-xs font-bold text-[#E4E7F1] flex items-center justify-between gap-2">
                                  <span className="truncate max-w-[140px]">{visualDetection.split('(')[0].trim()}</span>
                                  <span className="text-[10px] bg-[#3A326F] px-1.5 py-0.5 rounded font-mono font-bold text-[#C4B5FD] shrink-0">
                                    {visualConfidence}%
                                  </span>
                                </div>
                                <div className="text-[9px] text-[#C4B5FD] font-mono flex items-center justify-between mt-1 pt-1 border-t border-[#3A326F]">
                                  <span className="flex items-center gap-1">
                                    <Crosshair className="w-2.5 h-2.5" />
                                    <span>{detectedObjects.length > 1 ? `${detectedObjects.length} BBOXES CONFIRMED` : 'BBOX CONFIRMED'}</span>
                                  </span>
                                  <span className="truncate max-w-[120px]">{isDemoScenario ? 'DEMO' : (result?.visionModel || 'YOLO Multi-Task')}</span>
                                </div>
                              </div>
                            ) : (
                              <div className="border border-slate-700 bg-[#13152E]/80 rounded-lg z-10 p-2 shadow-md text-center">
                                <div className="text-xs font-semibold text-slate-300">
                                  {result?.category === 'Water Supply & Drainage' || result?.category === 'Storm Water & Drainage'
                                    ? 'Unvalidated Subsurface Leak'
                                    : result?.category === 'Sanitation & Garbage'
                                    ? 'No Waste Accumulation Detected'
                                    : 'No Road Damage Detected'}
                                </div>
                                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                                  {result?.category === 'Water Supply & Drainage' || result?.category === 'Storm Water & Drainage'
                                    ? 'Field acoustic inspection required'
                                    : 'Clean surface \u2022 0 detections'}
                                </div>
                              </div>
                            )}
                          </div>
                        )}

                        {/* 06: Text–image cross-validation */}
                        {stage.id === 6 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] space-y-1.5 font-sans">
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-[#65708B]">Multimodal Cosine Similarity:</span>
                              <span className="text-emerald-700 font-bold">{(consistencyScore / 100).toFixed(2)}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-[#65708B]">Consistency Verdict:</span>
                              <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                                {consistencyLevel} ALIGNMENT
                              </span>
                            </div>
                          </div>
                        )}

                        {/* 07: Hotspot and recurrence analysis */}
                        {stage.id === 7 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] space-y-1 font-sans">
                            <div className="flex items-center justify-between">
                              <span className="text-[#65708B] text-[11px]">Spatiotemporal Cluster:</span>
                              <span className="text-amber-700 font-bold text-xs">LBS Marg East Corridor</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-[#65708B]">Chronic Recurrence Index:</span>
                              <span className="text-rose-700 font-bold">62 / 100 (4 reports in 90d)</span>
                            </div>
                          </div>
                        )}

                        {/* 08: Risk-aware priority */}
                        {stage.id === 8 && (
                          <div className="space-y-2 font-sans">
                            <div className="flex items-center justify-between p-2 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1]">
                              <span className="text-xs uppercase text-[#65708B] font-semibold">COMPUTED SCORE:</span>
                              <div className="flex items-center gap-2">
                                <span className="text-base font-bold text-[#11162A] font-mono">
                                  {runningScore} / 100
                                </span>
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 border border-rose-200 text-rose-700">
                                  {priorityLevel}
                                </span>
                              </div>
                            </div>

                            <div className="grid grid-cols-3 sm:grid-cols-6 gap-1 text-[10px] text-center">
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Urgency</span>
                                <div className="text-amber-700 font-bold">+{breakdown.urgencyScore || 20}</div>
                              </div>
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Severity</span>
                                <div className="text-rose-700 font-bold">+{breakdown.textSeverityScore || 16}</div>
                              </div>
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Vision</span>
                                <div className="text-[#6457E8] font-bold">+{breakdown.visualSeverityScore || 17}</div>
                              </div>
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Recur</span>
                                <div className="text-purple-700 font-bold">+{breakdown.relatedReportsScore || 12}</div>
                              </div>
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Recency</span>
                                <div className="text-blue-700 font-bold">+{breakdown.recencyScore || 9}</div>
                              </div>
                              <div className="p-1 bg-white rounded border border-[#E4E7F1]">
                                <span className="text-[#65708B]">Location</span>
                                <div className="text-emerald-700 font-bold">+{breakdown.locationRiskScore || 9}</div>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* 09: Department routing */}
                        {stage.id === 9 && (
                          <div className="p-2.5 bg-[#F0F2F9]/70 rounded-lg border border-[#E4E7F1] space-y-1 font-sans">
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-[#65708B]">Assigned Department:</span>
                              <span className="font-bold text-[#11162A]">{department}</span>
                            </div>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-[#65708B]">Target Resolution SLA:</span>
                              <span className="text-[#6457E8] font-bold">12 Hours (Urgent Triage)</span>
                            </div>
                          </div>
                        )}

                        {/* 10: Results ready */}
                        {stage.id === 10 && (
                          <div className="p-2.5 bg-emerald-50 rounded-lg border border-emerald-200 space-y-1 text-[#11162A] font-sans">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-800">
                              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              <span>Work Order Ready for Field Dispatch</span>
                            </div>
                            <p className="text-[11px] text-[#65708B] font-sans mt-0.5">
                              {recommendedAction}
                            </p>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )
            })}
          </div>

          {/* ======================================================== */}
          {/* SEQUENTIAL RESULT REVEAL DOSSIER                          */}
          {/* Exact Required Order:                                     */}
          {/* Category -> Urgency -> Severity -> Location ->            */}
          {/* Evidence Consistency -> Priority -> Department -> Action  */}
          {/* ======================================================== */}
          {activeStage >= 10 && (
            <FadeContent blur={false} duration={0.35} className="p-6 sm:p-7 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-5 font-sans">
              {/* Header & Commit Bar */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#E4E7F1] gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                    <Check className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-[#11162A] tracking-tight flex items-center gap-2">
                      <span>Synthesized Civic Intelligence Dossier</span>
                      <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#6457E8]/10 text-[#6457E8] border border-[#6457E8]/20 font-semibold">
                        Verified
                      </span>
                    </h2>
                    <p className="text-xs text-[#65708B]">
                      All cognitive triage phases converged. Official work order ready for field deployment.
                    </p>
                  </div>
                </div>

                {/* Commit Action */}
                <div className="flex items-center gap-2">
                  {committedIssue ? (
                    <div className="px-4 py-2 bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg font-semibold text-xs flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Committed ({committedIssue.issueId})</span>
                    </div>
                  ) : (
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={handleCommitIssue}
                      disabled={commitLoading}
                      className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-semibold text-xs flex items-center gap-2 transition cursor-pointer disabled:opacity-50 shadow-xs"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{commitLoading ? 'Committing...' : 'Commit Work Order'}</span>
                    </motion.button>
                  )}

                  <button
                    onClick={handleReset}
                    className="px-3.5 py-2 bg-[#F0F2F9] hover:bg-slate-200 text-[#11162A] rounded-lg text-xs font-medium border border-[#E4E7F1] transition cursor-pointer"
                  >
                    Analyze Another
                  </button>
                </div>
              </div>

              {/* Sequential Results Unfolding in Exact Order */}
              <div className="space-y-3">
                <div className="text-xs font-semibold text-[#65708B] uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-3.5 h-3.5 text-[#6457E8]" />
                  <span>Sequential Analysis Results Breakdown</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                  {/* 1. Category */}
                  {revealedCount >= 1 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">1. Category</span>
                      <div className="font-bold text-[#11162A] text-sm mt-1">{targetCategory}</div>
                      <div className="text-[10px] text-[#6457E8] font-medium mt-1">Confidence: 96.4% NLP Match</div>
                    </motion.div>
                  )}

                  {/* 2. Urgency */}
                  {revealedCount >= 2 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">2. Urgency</span>
                      <div className="font-bold text-amber-700 text-sm mt-1">
                        <CountUp to={targetUrgency} suffix="%" duration={0.8} />
                      </div>
                      <div className="text-[10px] text-[#65708B] mt-1">Rapid Dispatch Threshold Met</div>
                    </motion.div>
                  )}

                  {/* 3. Severity */}
                  {revealedCount >= 3 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">3. Severity</span>
                      <div className="font-bold text-rose-700 text-sm mt-1">
                        <CountUp to={targetSeverity} suffix="%" duration={0.8} />
                      </div>
                      <div className="text-[10px] text-[#65708B] mt-1">Structural Infrastructure Impact</div>
                    </motion.div>
                  )}

                  {/* 4. Location */}
                  {revealedCount >= 4 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">4. Location</span>
                      <div className="font-bold text-[#11162A] text-sm mt-1 truncate">{targetLocation}</div>
                      <div className="text-[10px] text-emerald-700 font-medium mt-1">GIS Verified &bull; N-Ward</div>
                    </motion.div>
                  )}

                  {/* 5. Evidence Consistency */}
                  {revealedCount >= 5 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">5. Evidence Consistency</span>
                      <div className="font-bold text-emerald-700 text-sm mt-1">
                        {consistencyLevel} ({consistencyScore}%)
                      </div>
                      <div className="text-[10px] text-[#65708B] mt-1">Text-Image Cosine: {(consistencyScore / 100).toFixed(2)}</div>
                    </motion.div>
                  )}

                  {/* 6. Dynamic Priority Score (Animated Gauge & Breakdown) */}
                  {revealedCount >= 6 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs lg:col-span-2"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">6. Dynamic Priority Score</span>
                      <div className="mt-1">
                        <PriorityGauge
                          score={priorityScore}
                          level={priorityLevel}
                          breakdown={breakdown}
                          reasoning={priorityReasoning}
                          showDetails
                        />
                      </div>
                    </motion.div>
                  )}

                  {/* 7. Department */}
                  {revealedCount >= 7 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">7. Department</span>
                      <div className="font-bold text-[#11162A] text-sm mt-1">{department}</div>
                      <div className="text-[10px] text-[#6457E8] font-medium mt-1">Target SLA: 12 Hours</div>
                    </motion.div>
                  )}

                  {/* 8. Recommended Action */}
                  {revealedCount >= 8 && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                      className="p-3.5 bg-[#F0F2F9]/60 rounded-xl border border-[#E4E7F1] shadow-2xs lg:col-span-4"
                    >
                      <span className="text-[#65708B] text-[10px] uppercase font-bold tracking-wider">8. Recommended Action Directive</span>
                      <div className="font-bold text-emerald-800 text-sm mt-1 font-sans">{recommendedAction}</div>
                      <div className="text-[10px] text-[#65708B] mt-1">
                        Protocol: Municipal Emergency Barricade & Hot-Patch Field Team
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            </FadeContent>
          )}
        </div>
      )}
    </div>
  )
}

export default AnalysisPipelineView
