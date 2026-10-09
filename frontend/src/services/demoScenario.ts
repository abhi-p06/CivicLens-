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
    preRepairImageUrl: 'data/sample_pothole.jpg',
    postRepairImageUrl: 'data/sample_repaired_pothole.jpg',
  },
}
