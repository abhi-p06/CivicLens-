export type PriorityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type IssueStatus =
  | 'OPEN'
  | 'ANALYZED'
  | 'PRIORITIZED'
  | 'ASSIGNED'
  | 'SCHEDULED'
  | 'ACTION IN PROGRESS'
  | 'VERIFICATION'
  | 'RESOLVED'
  | 'REOPENED'
  | 'TRIAGED'
  | 'DUPLICATE'
  | 'AWAITING INSPECTION'
  | 'AWAITING CONFIRMATION'
  | 'Verified Closed'
  | 'In Progress'

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

export interface HostedCandidateResult {
  provider: string
  status: 'SUCCESS' | 'EMPTY' | 'ERROR' | 'UNAVAILABLE'
  modelId: string
  architecture: string
  task: string
  visualDetection?: string | null
  visualConfidence?: number
  detectedObjects?: VisualDetectionDetail[]
  detectedClasses?: string[]
  classCounts?: Record<string, number>
  imageDimensions?: [number, number]
  inferenceTimeMs?: number
  cached?: boolean
  rawPredictionCount?: number
  error?: string
  errorCategory?: string
}

export interface ComparisonSummary {
  localModel: string
  hostedModel: string
  task: string
  localDetectionCount: number
  hostedDetectionCount: number
  localPrimaryDetection: string | null
  hostedPrimaryDetection: string | null
  localConfidence: number
  hostedConfidence: number
  localLatencyMs: number
  hostedLatencyMs: number
  hostedStatus: string
  hostedCached: boolean
}

export interface VisionComparisonData {
  mode: string
  imagePath?: string
  categoryHint?: string
  comparisonSummary?: ComparisonSummary
  local?: {
    visualDetection?: string | null
    visualConfidence?: number
    detectedObjects?: VisualDetectionDetail[]
    visionExecutionMode?: string
    imageDimensions?: [number, number]
    inferenceTimeMs?: number
    detectedClasses?: string[]
    classCounts?: Record<string, number>
    task?: string
    sourceModel?: string
  }
  hosted?: HostedCandidateResult
}

export interface TaskAssignment {
  department: string
  team_name: string
  team_id?: string
  assigned_officer: string
  priority: string
  scheduled_date?: string
  instructions?: string
  assigned_at?: string
  assigned_by?: string
}

export interface TimelineEvent {
  id: string
  event_type: string
  title: string
  description: string
  actor: string
  role: string
  timestamp: string
  evidence_url?: string
  metadata?: Record<string, any>
}

export interface TemporaryMeasures {
  measures: string[]
  notes?: string
  recorded_at: string
  recorded_by: string
}

export interface RepeatCollection {
  is_scheduled: boolean
  frequency: string
  next_collection_date?: string
  instructions?: string
  scheduled_at?: string
  scheduled_by?: string
}

export interface CompletionDetails {
  completed_at: string
  completed_by: string
  completion_note: string
  completion_photo_url?: string
  closure_reason: string
}

export interface CitizenFeedback {
  status: 'CONFIRMED_RESOLVED' | 'REOPEN_REQUESTED'
  note?: string
  submitted_at: string
  citizen_name: string
}

export interface FieldTeam {
  id: string
  name: string
  department: string
  category: string
  status: 'AVAILABLE' | 'BUSY' | 'OFF_DUTY'
  ward: string
  sub_ward_id?: string
  authority_id?: string
  supervisor_name?: string
  capacity?: number
  contact_lead: string
  active_tasks_count?: number
}

export interface WardConfig {
  ward_code: string
  ward_name: string
  lead_officer: string
  active_teams: string[]
}

export interface OperationsKpis {
  unassigned_complaints: number
  high_priority_complaints: number
  work_in_progress: number
  resolved_this_month: number
  category_workload: {
    roads: number
    sanitation: number
    total: number
  }
  ward_distribution: Record<string, number>
  total_complaints: number
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
  location_method?: 'gps' | 'manual'
  locationMethod?: 'gps' | 'manual'
  ward: string
  timestamp: string
  department: string
  recommendedAction: string
  slaHours: number
  source: string
  isDuplicate: boolean
  duplicateGroup?: string
  duplicateGroupId?: string
  nearDuplicateCount?: number
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
  citizen_id?: string
  citizenId?: string
  
  // Hierarchical Ward Routing & Governance Fields
  authority_id?: string
  authority_code?: string
  authority_name?: string
  zone_id?: string
  zone_name?: string
  ward_id?: string
  sub_ward_id?: string
  sub_ward_name?: string
  locality_id?: string
  locality_name?: string
  supervisor_name?: string
  supervisor_id?: string
  routing_path?: string
  jurisdiction_verified?: boolean
  jurisdiction_review_required?: boolean
  jurisdiction_review_reason?: string
  jurisdiction_history?: JurisdictionAuditLog[]

  // Lightweight Ward Operations Management Fields
  assignment?: TaskAssignment
  timeline?: TimelineEvent[]
  temporary_measures?: TemporaryMeasures
  repeat_collection?: RepeatCollection
  completion_details?: CompletionDetails
  citizen_feedback?: CitizenFeedback
  
  metadata?: Record<string, any>
}

export type UserRole = 'citizen' | 'inspector' | 'admin'

export interface AuthUser {
  userId: string
  username: string
  email: string
  name: string
  role: UserRole
  jurisdiction?: {
    user_id: string
    authority_id: string
    ward_code: string
    sub_ward_id?: string
    jurisdiction_level: string
  }
}

export interface AuthResponse {
  token: string
  tokenType: string
  user: AuthUser
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

// -----------------------------------------------------------------------------
// AI Field Guidance & Government Research Types
// -----------------------------------------------------------------------------

export type RecommendationType = 'PRECAUTION' | 'ACTION' | 'CHECKLIST'
export type OfficerDecisionType = 'PENDING' | 'ACCEPTED' | 'EDITED' | 'DISMISSED'

export interface GuidanceCitation {
  doc_id: string
  doc_title: string
  source_org: string
  url: string
  section: string
  page_number?: number | null
  document_version?: string | null
  document_status?: string
  is_statutory_requirement?: boolean
}

export interface GuidanceActionItem {
  id: string
  item_type: RecommendationType
  title: string
  description: string
  steps: string[]
  equipment: string[]
  handling_precautions: string[]
  citation: GuidanceCitation
  is_requirement: boolean
  officer_decision: OfficerDecisionType
  edited_text?: string | null
  decision_reason?: string | null
  decided_by?: string | null
  decided_at?: string | null
}

export interface ConflictingSourceTopic {
  topic: string
  source_a: string
  position_a: string
  source_b: string
  position_b: string
  recommended_reconciliation: string
}

export interface FieldGuidance {
  guidance_id: string
  issue_id: string
  category: string
  generated_at: string
  situation_summary: string
  recommendation_rationale: string
  immediate_precautions: GuidanceActionItem[]
  recommended_field_actions: GuidanceActionItem[]
  equipment_and_resources: string[]
  handling_precautions: string[]
  completion_checklist: Array<{ item: string; statutory?: boolean }>
  retrieved_references: GuidanceCitation[]
  disagreements: ConflictingSourceTopic[]
  is_hazardous_escalation: boolean
  escalation_notice?: string | null
  has_insufficient_sources: boolean
  fallback_message?: string | null
  engineering_disclaimer?: string | null
}

export interface GuidanceSource {
  id: string
  name: string
  domain: string
  base_url: string
  category: string
  is_active: boolean
  is_allowlisted: boolean
  last_status: string
  last_retrieved_at?: string | null
  error_message?: string | null
}

export interface GuidanceDocument {
  id: string
  source_id: string
  source_domain: string
  source_org: string
  title: string
  url: string
  publication_date: string
  document_version: string
  document_status: string
  applicable_category: string
  content_type: string
  file_hash: string
  summary: string
  sections?: Array<{
    section_id?: string
    section_title?: string
    page_number?: number
    content?: string
    is_statutory?: boolean
  }>
  sections_count?: number
  is_approved: boolean
  last_retrieved_at?: string | null
}

export interface MunicipalAuthority {
  id: string
  code: string
  name: string
  short_name: string
  state: string
  headquarters?: string
  center_lat: number
  center_lng: number
  is_active: boolean
  boundary_geojson?: Record<string, any>
}

export interface AdminZone {
  id: string
  authority_id: string
  code: string
  name: string
  zone_number: number
  is_active: boolean
  boundary_geojson?: Record<string, any>
}

export interface AdminWard {
  id: string
  authority_id: string
  zone_id?: string
  code: string
  name: string
  office_location?: string
  officer_in_charge?: string
  contact_phone?: string
  center_lat: number
  center_lng: number
  is_active: boolean
  boundary_geojson?: Record<string, any>
}

export interface SubWard {
  id: string
  ward_id: string
  code: string
  name: string
  is_official: boolean
  operational_type: string
  center_lat: number
  center_lng: number
  supervisor_name?: string
  assigned_department?: string
  is_active: boolean
  boundary_geojson?: Record<string, any>
  created_at?: string
}

export interface LocalityBeat {
  id: string
  sub_ward_id: string
  code: string
  name: string
  beat_type: string
  center_lat: number
  center_lng: number
  radius_meters?: number
  is_active: boolean
}

export interface HierarchyTreeNode {
  id: string
  label?: string
  name: string
  code: string
  type?: 'city' | 'authority' | 'zone' | 'ward' | 'sub_ward' | 'locality'
  level: 'city' | 'authority' | 'zone' | 'ward' | 'sub_ward' | 'locality'
  parent_id?: string
  is_official: boolean
  is_active: boolean
  boundary_geojson?: Record<string, any>
  lead_officer?: string
  supervisor_name?: string
  supervisor?: string
  department?: string
  assigned_crews_count?: number
  assigned_crews?: any[]
  assigned_teams?: FieldTeam[]
  available_crews?: number
  total_complaints: number
  direct_complaints?: number
  unassigned_complaints: number
  assigned_complaints: number
  in_progress_tasks: number
  completed_complaints: number
  is_authorized?: boolean
  is_readonly?: boolean
  has_authorized_descendant?: boolean
  authority_code?: string
  ward_code?: string
  children: HierarchyTreeNode[]
}

export interface JurisdictionAuditLog {
  id: string
  issue_id: string
  previous_authority_id?: string
  previous_ward?: string
  previous_sub_ward_id?: string
  new_authority_id: string
  new_ward: string
  new_sub_ward_id?: string
  new_routing_path?: string
  changed_by: string
  changed_by_role: string
  reason: string
  timestamp: string
}

export interface LocationVerificationResult {
  is_valid: boolean
  error?: string | null
  latitude?: number
  longitude?: number
  authority_id?: string
  authority_code?: string
  authority_name?: string
  zone_id?: string
  zone_code?: string
  zone_name?: string
  ward_id?: string
  ward_code?: string
  ward_name?: string
  sub_ward_id?: string
  sub_ward_code?: string
  sub_ward_name?: string
  is_official_sub_ward?: boolean
  locality_id?: string
  locality_name?: string
  landmark?: string
  supervisor_name?: string
  is_ambiguous?: boolean
  requires_admin_review?: boolean
  review_reason?: string
  has_ward_mismatch?: boolean
  selected_ward?: string
  warning_message?: string
  // Aliases for convenience
  is_valid_jurisdiction?: boolean
  is_mismatch?: boolean
  derived_ward?: string
  mismatch_message?: string
  review_required?: boolean
  geographic_path?: string
}



