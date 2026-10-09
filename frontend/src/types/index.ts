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
  verifiedAt: string
  postActionImageUrl?: string
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
  visualDetection?: string
  visualConfidence?: number
  evidenceConsistency?: number
  consistencyFlag?: string
  consistencyDetail?: EvidenceConsistencyResult
  isHotspot?: boolean
  hotspotClusterId?: string
  hotspotDetail?: HotspotInfo
  recurringDetail?: RecurrenceInfo
  resolutionEvidence?: ResolutionEvidence
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
