import { Issue, HotspotInfo, RecurrenceInfo } from '../types'

export const DEMO_SCENARIO = {
  complaintText:
    'There is a large pothole near a school gate on the main road. Vehicles are struggling to pass and it has become dangerous during rain.',
  location: 'Somaiya Vidyavihar School Gate Road, N-Ward, Mumbai',
  latitude: 19.0760,
  longitude: 72.8850,
  ward: 'N-Ward',
  imageUrl: 'data/sample_pothole.jpg',
  repairedImageUrl: 'data/sample_repaired_pothole.jpg',

  // Analysis Result
  analysisResult: {
    category: 'Pothole / Road Damage',
    urgency: 0.92,
    urgencyLevel: 'HIGH',
    severity: 0.85,
    severityLevel: 'HIGH',
    overallSeverity: 0.85,
    resolvedLocation: 'Somaiya Vidyavihar School Gate Road, N-Ward, Mumbai',
    latitude: 19.0760,
    longitude: 72.8850,
    ward: 'N-Ward',
    visualDetection: 'Pothole Cavity (YOLOv8s Confirmed)',
    visualConfidence: 0.94,
    detectedObjects: [
      {
        label: 'pothole_cavity',
        confidence: 0.94,
        bbox: [0.35, 0.25, 0.72, 0.78],
      },
    ],
    evidenceConsistency: 0.94,
    consistencyLevel: 'HIGH',
    consistencyFlag: 'CONSISTENT',
    priorityScore: 91,
    priorityLevel: 'CRITICAL',
    priorityBreakdown: {
      urgencyScore: 20,
      textSeverityScore: 16,
      visualSeverityScore: 17,
      relatedReportsScore: 12,
      recencyScore: 9,
      locationRiskScore: 9,
    },
    priorityReasoning:
      'Critical risk score driven by severe accident hazard adjacent to school gate with 4 nearby citizen reports and heavy monsoon waterlogging risk.',
    department: 'Roads Department',
    recommendedAction: 'Inspect and schedule pothole repair.',
    slaHours: 12,
  },

  // Complete Issue Record for Intelligence Dossier & Map
  issueRecord: {
    issueId: 'ISS-DEMO-2026',
    complaintText:
      'There is a large pothole near a school gate on the main road. Vehicles are struggling to pass and it has become dangerous during rain.',
    category: 'Roads & Footpaths' as any,
    urgency: 0.92,
    severity: 0.85,
    priorityScore: 91,
    priorityLevel: 'CRITICAL' as any,
    priorityBreakdown: {
      urgency: 20,
      textSeverity: 16,
      visualSeverity: 17,
      relatedReports: 12,
      recency: 9,
      locationRisk: 9,
    },
    priorityReasoning:
      'Critical risk score driven by severe accident hazard adjacent to school gate with 4 nearby citizen reports and heavy monsoon waterlogging risk.',
    status: 'ACTION IN PROGRESS' as any,
    location: 'Somaiya Vidyavihar School Gate Road',
    latitude: 19.0760,
    longitude: 72.8850,
    ward: 'N-Ward',
    timestamp: new Date().toISOString(),
    department: 'Roads Department (BMC)',
    recommendedAction: 'Inspect and schedule pothole repair.',
    slaHours: 12,
    source: 'citizen_mobile',
    isDuplicate: false,
    duplicateGroupId: 'DUP-POTHOLE-VIDYAVIHAR',
    imageUrl: 'data/sample_pothole.jpg',
    visualDetection: 'Pothole Cavity (YOLOv8s Confirmed)',
    visualConfidence: 0.94,
    evidenceConsistency: 0.94,
    consistencyFlag: 'CONSISTENT',
    isHotspot: true,
    hotspotClusterId: 'HS-VIDYAVIHAR-01',
    metadata: {
      nearDuplicateCount: 4,
      schoolZone: true,
      monsoonRisk: 'SEVERE',
    },
  } as Issue,

  // Hotspot Context
  hotspotContext: {
    hotspotId: 'HS-VIDYAVIHAR-01',
    center: { lat: 19.0760, lng: 72.8850 },
    radiusMeters: 650,
    issueCount: 14,
    dominantCategory: 'Pothole / Road Damage',
    averagePriority: 86.4,
    growthRate: 24,
    hotspotLevel: 'CRITICAL' as any,
  } as HotspotInfo,

  // Recurrence Context
  recurrenceContext: {
    recurringIssue: true,
    location: 'Somaiya Vidyavihar School Gate Road',
    category: 'Roads & Footpaths',
    reportCount: 5,
    firstReported: '2026-08-14T10:00:00Z',
    lastReported: new Date().toISOString(),
    recurrenceScore: 82,
    trend: 'INCREASING' as any,
  } as RecurrenceInfo,

  // Resolution Verification Context
  resolutionContext: {
    resolutionStatus: 'LIKELY RESOLVED',
    resolutionConfidence: 0.942,
    ssimScore: 0.89,
    verificationSummary:
      'Visual survey demonstrates complete asphalt cold-mix infill. Structural SSIM: 0.89. Road surface continuity restored. Likely resolved pending final post-curing rainfall inspection.',
    preRepairImageUrl: 'data/test_samples/repair_pothole_before.jpg',
    postRepairImageUrl: 'data/test_samples/repair_pothole_after_repaired.jpg',
  },
}

export const DEMO_SCENARIOS = {
  pothole: {
    id: 'pothole',
    title: 'Pothole & Road Damage Detection (RDD2022 YOLOv8s)',
    complaintText:
      'Critical deep pothole crater breaking wheel rims and causing major skidding risk near school entrance.',
    location: 'Somaiya Vidyavihar Main Gate, Vidyavihar East',
    imageUrl: 'data/test_samples/repair_pothole_before.jpg',
    category: 'Roads & Footpaths',
    department: 'Roads & Traffic Infrastructure Dept (MCGM)',
    model: 'YOLOv8s RDD2022',
  },
  garbage: {
    id: 'garbage',
    title: 'Garbage & Street Litter Detection (TACO YOLO11s)',
    complaintText:
      'Accumulated municipal garbage dump with discarded plastic bottles, cups, and decaying cartons along sidewalk creating extreme stench.',
    location: 'Station Road, Kurla West',
    imageUrl: 'data/test_samples/bottle.jpg',
    category: 'Sanitation & Garbage',
    department: 'Solid Waste Management (SWM Dept)',
    model: 'YOLO11s TACO',
    note: 'Transparent local street precision (~27.3% Prec@50); human supervisory review retained.',
  },
  mismatch: {
    id: 'mismatch',
    title: 'Cross-Category Mismatch Validation (Road Claim + Garbage Image)',
    complaintText:
      'Massive asphalt crater and structural road fissure breaking vehicle suspensions on main transit corridor.',
    location: 'S.V. Road, Santacruz',
    imageUrl: 'data/test_samples/bottle.jpg',
    category: 'Roads & Footpaths',
    department: 'Roads & Traffic Infrastructure Dept (MCGM)',
    expectedConsistency: 'INCONSISTENT',
    reason:
      'Evidence discrepancy: Attached photograph indicates sanitation / waste debris rather than road defect. Routed for manual supervisory triage.',
  },
  resolution: {
    id: 'resolution',
    title: 'Pothole Before & After Lifecycle Verification',
    preRepairImageUrl: 'data/test_samples/repair_pothole_before.jpg',
    postRepairImageUrl: 'data/test_samples/repair_pothole_after_repaired.jpg',
    expectedStatus: 'LIKELY RESOLVED',
    ssimScore: 0.83,
  },
}

