export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type IssueStatus =
  | 'OPEN'
  | 'ANALYZED'
  | 'PRIORITIZED'
  | 'ASSIGNED'
  | 'ACTION IN PROGRESS'
  | 'VERIFICATION'
  | 'RESOLVED'
  | 'TRIAGED'
  | 'DUPLICATE'

export type IssueCategory =
  | 'Roads & Footpaths'
  | 'Sanitation & Garbage'
  | 'Water Supply & Drainage'
  | 'Street Lighting'
  | 'Storm Water Drains'
  | 'Traffic & Safety'

export type ConsistencyLevel =
  | 'CONSISTENT'
  | 'PARTIALLY CONSISTENT'
  | 'INCONSISTENT'
  | 'MANUAL REVIEW'

export type ResolutionStatus =
  | 'LIKELY RESOLVED'
  | 'STILL PRESENT'
  | 'REQUIRES MANUAL VERIFICATION'

export type HotspotLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL'
export type RecurrenceTrend = 'INCREASING' | 'STABLE' | 'DECREASING'

export interface PriorityBreakdown {
  urgency: number
  textSeverity: number
  visualSeverity: number
  relatedReports: number
  recency: number
  locationRisk: number
}

export interface HotspotInfo {
  hotspotId: string
  center: { lat: number; lng: number }
  radiusMeters: number
  issueCount: number
  dominantCategory: string
  averagePriority: number
  growthRate: number
  hotspotLevel: HotspotLevel
}

export interface RecurrenceInfo {
  recurringIssue: boolean
  location: string
  category: string
  reportCount: number
  firstReported: string
  lastReported: string
  recurrenceScore: number
  trend: RecurrenceTrend
}

export interface EvidenceConsistencyResult {
  consistencyScore: number
  consistencyLevel: ConsistencyLevel
  textEvidence: string
  visualEvidence: string
  reason: string
}

export interface ResolutionEvidence {
  resolutionStatus: ResolutionStatus
  resolutionConfidence: number
  remainingDetection: string | null
  verificationSummary: string
  verifiedAt?: string
  verified_at?: string
  inspector_id?: string
  original_image_url?: string
  original_upload_id?: string
  resolution_image_url?: string
  resolution_upload_id?: string
  original_detection?: string
  post_action_detection?: string | null
  verificationMethod?: string
  sceneComparable?: boolean
  comparisonMetrics?: {
    ssim?: number
    histogramCorrelation?: number
    featureMatchRatio?: number
    featureMatchCount?: number
    aspectRatioDiff?: number
    comparabilityScore?: number
    reason?: string
  }
  beforeDetections?: Array<{ label: string; confidence: number; bbox: number[] }>
  afterDetections?: Array<{ label: string; confidence: number; bbox: number[] }>
  requiresManualReview?: boolean
  post_repair_cv_cleared?: boolean
  postActionImageUrl?: string
}

export interface UploadResponse {
  uploadId: string
  previewUrl: string
  contentType: string
  sizeBytes: number
}

export interface VisualDetectionDetail {
  label: string
  confidence: number
  bbox: number[]
  task?: string
  class_id?: number
  class_name?: string
  source_model?: string
  execution_mode?: string
}

export interface Issue {
  issueId: string
  complaintText: string
  category: IssueCategory
  urgency: number
  severity: number
  priorityScore: number
  priorityLevel: PriorityLevel
  priorityBreakdown?: PriorityBreakdown
  priorityReasoning?: string
  status: IssueStatus
  location: string
  latitude: number
  longitude: number
  ward: string
  timestamp: string
  department: string
  recommendedAction: string
  slaHours: number
  source: string
  isDuplicate: boolean
  duplicateGroupId?: string
  imageUrl?: string
  uploadId?: string
  visualDetection?: string
  visualConfidence?: number
  detectedObjects?: VisualDetectionDetail[]
  visualSeverity?: number
  visionMode?: string
  visionModel?: string
  visionTask?: string
  evidenceConsistency?: number
  consistencyFlag?: string
  consistencyDetail?: EvidenceConsistencyResult
  isHotspot?: boolean
  hotspotClusterId?: string
  hotspotDetail?: HotspotInfo
  recurringDetail?: RecurrenceInfo
  resolutionEvidence?: ResolutionEvidence
  resolutionHistory?: ResolutionEvidence[]
  statusHistory?: Array<{ status: IssueStatus; timestamp: string; note?: string }>
  metadata?: Record<string, any>
}

export interface EvaluationMetrics {
  classification?: {
    accuracy?: number
    precision_macro?: number
    macro_precision?: number
    recall_macro?: number
    macro_recall?: number
    f1_macro?: number
    macro_f1?: number
    total_evaluated?: number
    sample_count?: number
  }
  priority?: {
    mae?: number
    rmse?: number
    top_k_precision?: number
    top_k_recall?: number
  }
  priority_mae?: {
    mae?: number
    rmse?: number
    top_k_precision?: number
    top_k_recall?: number
  }
  hotspot_clustering?: {
    silhouette_score?: number
    total_samples?: number
    total_points?: number
  }
  department_routing?: {
    accuracy?: number
    f1_macro?: number
    macro_f1?: number
  }
  text_image_consistency?: {
    accuracy?: number
    precision_macro?: number
    macro_precision?: number
    recall_macro?: number
    macro_recall?: number
    f1_macro?: number
    macro_f1?: number
  }
  resolution_verification?: {
    accuracy?: number
    precision_macro?: number
    macro_precision?: number
    recall_macro?: number
    macro_recall?: number
    f1_macro?: number
    macro_f1?: number
  }
}

export interface SubsystemTelemetry {
  name: string
  tech: string
  status: string
  mode: string
  is_model_available: boolean
  metric_name: string
  metric_value: number | null
  metric_display: string
  metric_provenance: string
  measurement_status: 'measured' | 'configured' | 'unavailable'
}

export interface SystemHealth {
  status: string
  service: string
  version: string
  totalIssuesTracked: number
  activeIssues: number
  storageMode: string
  subsystems: Record<string, SubsystemTelemetry>
}

