import {
  Issue,
  HotspotInfo,
  RecurrenceInfo,
  EvaluationMetrics,
  SystemHealth,
  ResolutionEvidence,
  AuthResponse,
  AuthUser,
  UserRole,
  FieldTeam,
  WardConfig,
  OperationsKpis,
  FieldGuidance,
  GuidanceSource,
  GuidanceDocument,
  OfficerDecisionType,
  MunicipalAuthority,
  AdminWard,
  SubWard,
  LocalityBeat,
  HierarchyTreeNode,
  JurisdictionAuditLog,
  LocationVerificationResult
} from '../types'

const BASE_URL = '/api/v1'

/**
 * Resolves authorization headers for authenticated operations.
 * - In genuine sessions: checks civilens_auth_token.
 * - In local demo/development mode: falls back to documented demo tokens if enabled.
 * - In production mode: strictly requires an authenticated session/token from storage.
 */
function getAuthHeader(role?: UserRole): string | undefined {
  if (typeof window !== 'undefined') {
    const sessionToken =
      localStorage.getItem('civilens_auth_token') ||
      (role ? localStorage.getItem(`civilens_${role}_token`) : null)
    if (sessionToken) {
      return sessionToken.startsWith('Bearer ') ? sessionToken : `Bearer ${sessionToken}`
    }
  }

  // Allow development tokens only in development or when explicitly enabled in environment
  const isDev = import.meta.env.DEV
  const demoAuthAllowed = isDev || import.meta.env.VITE_CIVILENS_DEMO_AUTH === 'true'

  if (demoAuthAllowed && role) {
    if (role === 'admin') return 'Bearer demo-admin-token'
    if (role === 'inspector') return 'Bearer demo-inspector-token'
    if (role === 'citizen') return 'Bearer demo-citizen-token'
  }

  return undefined
}

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${BASE_URL}/health`)
    if (!res.ok) throw new Error('Health check failed')
    return res.json()
  },

  async getIssues(params?: {
    category?: string
    priority?: string
    status?: string
    ward?: string
    sub_ward_id?: string
    locality_id?: string
    department?: string
    assignment_status?: string
  }): Promise<Issue[]> {
    const query = new URLSearchParams()
    if (params?.category && params.category !== 'ALL') query.append('category', params.category)
    if (params?.priority && params.priority !== 'ALL') query.append('priority', params.priority)
    if (params?.status && params.status !== 'ALL') query.append('status', params.status)
    if (params?.ward && params.ward !== 'ALL' && !params.ward.includes('ALL WARDS')) query.append('ward', params.ward)
    if (params?.sub_ward_id && params.sub_ward_id !== 'ALL') query.append('sub_ward_id', params.sub_ward_id)
    if (params?.locality_id && params.locality_id !== 'ALL') query.append('locality_id', params.locality_id)
    if (params?.department && params.department !== 'ALL') query.append('department', params.department)
    if (params?.assignment_status && params.assignment_status !== 'ALL') query.append('assignment_status', params.assignment_status)

    const headers: Record<string, string> = {}
    const auth = getAuthHeader()
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues?${query.toString()}`, { headers })
    if (!res.ok) throw new Error('Failed to fetch issues')
    return res.json()
  },

  async getIssue(id: string): Promise<Issue> {
    const res = await fetch(`${BASE_URL}/issues/${id}`)
    if (!res.ok) throw new Error('Failed to fetch issue')
    return res.json()
  },

  async uploadImage(file: File): Promise<{
    uploadId: string
    previewUrl: string
    contentType: string
    sizeBytes: number
  }> {
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const errBody = await res.json().catch(() => null)
      const detail = Array.isArray(errBody?.detail) ? errBody.detail[0]?.msg : errBody?.detail
      throw new Error(detail || 'Image upload failed')
    }
    return res.json()
  },

  async submitIssue(payload: {
    complaintText: string
    location?: string
    latitude?: number
    longitude?: number
    location_method?: 'gps' | 'manual'
    locationMethod?: 'gps' | 'manual'
    imageUrl?: string
    uploadId?: string
    category?: string
    ward?: string
    selected_ward?: string
    sub_ward_id?: string
    locality_id?: string
    source?: string
  }): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader()
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const errBody = await res.json().catch(() => null)
      const detail = Array.isArray(errBody?.detail) ? errBody.detail[0]?.msg : errBody?.detail
      throw new Error(detail || 'Failed to submit issue')
    }
    return res.json()
  },

  async getGeoBounds(): Promise<{ region: string; min_lat: number; max_lat: number; min_lng: number; max_lng: number }> {
    const res = await fetch(`${BASE_URL}/geo/bounds`)
    if (!res.ok) throw new Error('Failed to fetch geographic bounds')
    return res.json()
  },

  async reverseGeocode(lat: number, lng: number): Promise<{ valid: boolean; address?: string; ward?: string; error?: string; latitude: number; longitude: number }> {
    const res = await fetch(`${BASE_URL}/geo/reverse-geocode?lat=${lat}&lng=${lng}`)
    if (!res.ok) throw new Error('Failed to reverse-geocode coordinates')
    return res.json()
  },

  async searchLocations(query: string, limit: number = 6): Promise<Array<{ name: string; ward: string; latitude: number; longitude: number }>> {
    const res = await fetch(`${BASE_URL}/geo/search?query=${encodeURIComponent(query)}&limit=${limit}`)
    if (!res.ok) throw new Error('Failed to search locations')
    return res.json()
  },

  async getMyIssues(): Promise<Issue[]> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader('citizen')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/my`, { headers })
    if (!res.ok) throw new Error('Failed to fetch your submitted complaints')
    return res.json()
  },

  async analyzeComplaint(payload: {
    complaintText: string
    location?: string
    imageUrl?: string
    uploadId?: string
    category?: string
    ward?: string
  }): Promise<any> {
    const res = await fetch(`${BASE_URL}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Failed to analyze complaint')
    return res.json()
  },

  async getHotspots(): Promise<HotspotInfo[]> {
    const res = await fetch(`${BASE_URL}/hotspots`)
    if (!res.ok) throw new Error('Failed to fetch hotspots')
    const data = await res.json()
    return (data || []).map((h: any) => {
      const lat = Array.isArray(h.center) ? Number(h.center[0]) : Number(h.center?.lat ?? 19.076)
      const lng = Array.isArray(h.center) ? Number(h.center[1]) : Number(h.center?.lng ?? 72.885)
      return {
        ...h,
        center: { lat: isNaN(lat) ? 19.076 : lat, lng: isNaN(lng) ? 72.885 : lng },
        radiusMeters: h.radiusMeters || h.radius || 300,
        hotspotLevel: h.hotspotLevel === 'SEVERE' ? 'CRITICAL' : (h.hotspotLevel || 'MODERATE'),
      }
    })
  },

  async getRecurringIssues(): Promise<RecurrenceInfo[]> {
    const res = await fetch(`${BASE_URL}/recurring`)
    if (!res.ok) throw new Error('Failed to fetch recurring issues')
    return res.json()
  },

  async updateStatus(id: string, status: string, note?: string): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${id}/status`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ status, note }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to update status')
    }
    return res.json()
  },

  async verifyResolution(id: string, postActionImageUrl?: string, uploadId?: string, notes?: string): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${id}/verify`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ postActionImageUrl, uploadId, notes }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to verify resolution')
    }
    return res.json()
  },

  async getVerificationHistory(id: string): Promise<ResolutionEvidence[]> {
    const res = await fetch(`${BASE_URL}/issues/${id}/verifications`)
    if (!res.ok) throw new Error('Failed to fetch verification history')
    return res.json()
  },

  async getRoutingConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${BASE_URL}/routing/config`)
    if (!res.ok) throw new Error('Failed to fetch routing config')
    return res.json()
  },

  async updateRoutingConfig(category: string, config: any): Promise<any> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('admin')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/routing/config`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ category, config }),
    })
    if (!res.ok) {
      const errBody = await res.json().catch(() => null)
      const detail = Array.isArray(errBody?.detail) ? errBody.detail[0]?.msg : errBody?.detail
      throw new Error(detail || 'Failed to update routing config')
    }
    return res.json()
  },

  async getEvaluationMetrics(): Promise<EvaluationMetrics> {
    const res = await fetch(`${BASE_URL}/evaluation/metrics`)
    if (!res.ok) throw new Error('Failed to fetch evaluation metrics')
    return res.json()
  },

  async resetDemo(): Promise<any> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader('admin')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/demo/reset`, {
      method: 'POST',
      headers,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to reset demo')
    }
    return res.json()
  },

  async getAdminUsers(): Promise<Array<{ id: string; username: string; email: string; name: string; role: string; is_active: boolean; created_at: string }>> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader('admin')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/admin/users`, { headers })
    if (!res.ok) throw new Error('Failed to fetch user accounts')
    return res.json()
  },

  // --------------------------------------------------------------------------
  // Ward Operations Management
  // --------------------------------------------------------------------------

  async getOperationsKpis(): Promise<OperationsKpis> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader()
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/operations/kpis`, { headers })
    if (!res.ok) throw new Error('Failed to fetch operational KPIs')
    return res.json()
  },

  async getFieldTeams(
    params?:
      | {
          category?: string
          ward?: string
          sub_ward_id?: string
          department?: string
        }
      | string
  ): Promise<FieldTeam[]> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader()
    if (auth) headers['Authorization'] = auth

    const query = new URLSearchParams()
    if (typeof params === 'string') {
      if (params) query.append('category', params)
    } else if (params) {
      if (params.category && params.category !== 'ALL') query.append('category', params.category)
      if (params.ward && params.ward !== 'ALL') query.append('ward', params.ward)
      if (params.sub_ward_id && params.sub_ward_id !== 'ALL') query.append('sub_ward_id', params.sub_ward_id)
      if (params.department && params.department !== 'ALL') query.append('department', params.department)
    }

    const qStr = query.toString() ? `?${query.toString()}` : ''
    const res = await fetch(`${BASE_URL}/teams${qStr}`, { headers })
    if (!res.ok) throw new Error('Failed to fetch field teams')
    return res.json()
  },

  async assignTask(
    issueId: string,
    payload: {
      department: string
      team_name: string
      team_id?: string
      assigned_officer?: string
      priority?: string
      scheduled_date?: string
      instructions?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/assign`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to assign task')
    }
    return res.json()
  },

  async scheduleTask(
    issueId: string,
    payload: {
      scheduled_date: string
      schedule_type?: string
      instructions?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/schedule`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to schedule task')
    }
    return res.json()
  },

  async recordAction(
    issueId: string,
    payload: {
      action_type: string
      measures?: string[]
      stage?: string
      scheduled_date?: string
      frequency?: string
      notes?: string
      photo_url?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/action`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to record action')
    }
    return res.json()
  },

  async completeTask(
    issueId: string,
    payload: {
      completion_note: string
      closure_reason?: string
      completion_photo_url?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/complete`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to complete complaint')
    }
    return res.json()
  },

  async reopenTask(
    issueId: string,
    payload: {
      reason: string
      note?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/reopen`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to reopen complaint')
    }
    return res.json()
  },

  async verifyJurisdiction(issueId: string, notes?: string): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/verify-jurisdiction`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ notes }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to verify geographical jurisdiction')
    }
    return res.json()
  },

  async submitCitizenFeedback(
    issueId: string,
    payload: {
      feedback: 'CONFIRMED_RESOLVED' | 'REOPEN_REQUESTED'
      note?: string
      citizen_name?: string
    }
  ): Promise<Issue> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('citizen')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/feedback`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to submit citizen feedback')
    }
    return res.json()
  },

  admin: {
    async getTeams(): Promise<FieldTeam[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/teams`, { headers })
      if (!res.ok) throw new Error('Failed to fetch teams')
      return res.json()
    },

    async createTeam(payload: Partial<FieldTeam>): Promise<FieldTeam> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/admin/teams`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to create team')
      }
      return res.json()
    },

    async updateTeam(teamId: string, payload: Partial<FieldTeam>): Promise<FieldTeam> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/admin/teams/${teamId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to update team')
      }
      return res.json()
    },

    async deleteTeam(teamId: string): Promise<void> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/admin/teams/${teamId}`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to delete team')
      }
    },

    async getWards(): Promise<WardConfig[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/admin/wards`, { headers })
      if (!res.ok) throw new Error('Failed to fetch wards')
      return res.json()
    },

    async updateWard(wardCode: string, payload: Partial<WardConfig>): Promise<WardConfig> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/admin/wards/${wardCode}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to update ward')
      }
      return res.json()
    },
  },

  // ---------------------------------------------------------------------------
  // AI Field Guidance & Government Research
  // ---------------------------------------------------------------------------
  async getFieldGuidance(issueId: string, forceRegenerate = false): Promise<FieldGuidance> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const url = `${BASE_URL}/issues/${issueId}/guidance${forceRegenerate ? '?force_regenerate=true' : ''}`
    const res = await fetch(url, { headers })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to fetch field guidance')
    }
    return res.json()
  },

  async regenerateFieldGuidance(issueId: string): Promise<FieldGuidance> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/guidance/regenerate`, {
      method: 'POST',
      headers,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to regenerate field guidance')
    }
    return res.json()
  },

  async recordGuidanceDecision(
    issueId: string,
    payload: {
      item_id: string
      decision: OfficerDecisionType
      edited_text?: string
      reason?: string
    }
  ): Promise<FieldGuidance> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const auth = getAuthHeader('inspector')
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/issues/${issueId}/guidance/decision`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to record guidance decision')
    }
    return res.json()
  },

  async getGuidanceDocument(docId: string): Promise<GuidanceDocument> {
    const headers: Record<string, string> = {}
    const auth = getAuthHeader()
    if (auth) headers['Authorization'] = auth

    const res = await fetch(`${BASE_URL}/guidance/documents/${docId}`, { headers })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to load guidance document')
    }
    return res.json()
  },

  // Admin Guidance Management
  adminGuidance: {
    async listSources(): Promise<GuidanceSource[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/admin/guidance/sources`, { headers })
      if (!res.ok) throw new Error('Failed to fetch guidance sources')
      return res.json()
    },

    async updateSource(sourceId: string, updates: { is_active?: boolean; category?: string }): Promise<GuidanceSource> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/admin/guidance/sources/${sourceId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(updates),
      })
      if (!res.ok) throw new Error('Failed to update guidance source')
      return res.json()
    },

    async listDocuments(category?: string, status?: string): Promise<GuidanceDocument[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const query = new URLSearchParams()
      if (category) query.append('category', category)
      if (status) query.append('status', status)

      const res = await fetch(`${BASE_URL}/admin/guidance/documents?${query.toString()}`, { headers })
      if (!res.ok) throw new Error('Failed to fetch guidance documents')
      return res.json()
    },

    async updateDocument(docId: string, updates: { document_status?: string; is_approved?: boolean }): Promise<GuidanceDocument> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/admin/guidance/documents/${docId}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(updates),
      })
      if (!res.ok) throw new Error('Failed to update guidance document')
      return res.json()
    },

    async ingestSource(payload: { source_url?: string; source_id?: string; force_refresh?: boolean }): Promise<any> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/admin/guidance/ingest`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Document ingestion failed')
      }
      return res.json()
    },
  },

  hierarchy: {
    async getTree(params?: { authority?: string; ward?: string }): Promise<HierarchyTreeNode[]> {
      const query = new URLSearchParams()
      if (params?.authority) query.append('authority', params.authority)
      if (params?.ward) query.append('ward', params.ward)
      const qStr = query.toString() ? `?${query.toString()}` : ''

      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/tree${qStr}`, { headers })
      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Access restricted: Citizens cannot view the administrative hierarchy tree.')
        }
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to fetch hierarchy tree')
      }
      const data = await res.json()
      const normalizeNode = (n: any): HierarchyTreeNode => ({
        ...n,
        name: n.name || n.label || '',
        label: n.label || n.name || '',
        level: n.level || n.type || 'ward',
        type: n.type || n.level || 'ward',
        supervisor: n.supervisor || n.supervisor_name || '',
        supervisor_name: n.supervisor_name || n.supervisor || '',
        available_crews: n.available_crews ?? n.assigned_crews_count ?? 0,
        children: (n.children || []).map(normalizeNode),
      })
      return data.map(normalizeNode)
    },

    async getAuthorities(): Promise<MunicipalAuthority[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth
      const res = await fetch(`${BASE_URL}/hierarchy/authorities`, { headers })
      if (!res.ok) throw new Error('Failed to fetch authorities')
      return res.json()
    },

    async getAdminWards(authorityId?: string): Promise<AdminWard[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth
      const query = authorityId ? `?authority_id=${encodeURIComponent(authorityId)}` : ''
      const res = await fetch(`${BASE_URL}/hierarchy/wards${query}`, { headers })
      if (!res.ok) throw new Error('Failed to fetch admin wards')
      return res.json()
    },

    async getSubWards(wardId?: string): Promise<SubWard[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth
      const query = wardId ? `?ward_id=${encodeURIComponent(wardId)}` : ''
      const res = await fetch(`${BASE_URL}/hierarchy/sub-wards${query}`, { headers })
      if (!res.ok) throw new Error('Failed to fetch sub-wards')
      return res.json()
    },

    async createSubWard(payload: {
      ward_id: string
      code?: string
      sub_ward_code?: string
      name: string
      center_lat?: number
      center_lng?: number
      supervisor_name?: string
      assigned_department?: string
      boundary_geojson?: Record<string, any>
    }): Promise<SubWard> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const body = {
        ward_id: payload.ward_id,
        sub_ward_code: payload.sub_ward_code || payload.code || 'SW-NEW',
        name: payload.name,
        supervisor_name: payload.supervisor_name || 'Area Supervisor',
        is_active: true,
        boundary_geojson: payload.boundary_geojson,
      }

      const res = await fetch(`${BASE_URL}/hierarchy/sub-wards`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to create operational sub-ward')
      }
      return res.json()
    },

    async updateSubWard(subWardId: string, payload: Partial<SubWard>): Promise<SubWard> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/sub-wards/${encodeURIComponent(subWardId)}`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to update operational sub-ward')
      }
      return res.json()
    },

    async deleteSubWard(subWardId: string): Promise<{ success: boolean; message: string }> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/sub-wards/${encodeURIComponent(subWardId)}`, {
        method: 'DELETE',
        headers,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to delete operational sub-ward')
      }
      return res.json()
    },

    async getLocalities(subWardId?: string): Promise<LocalityBeat[]> {
      const query = subWardId ? `?sub_ward_id=${encodeURIComponent(subWardId)}` : ''
      const res = await fetch(`${BASE_URL}/hierarchy/localities${query}`)
      if (!res.ok) throw new Error('Failed to fetch localities')
      return res.json()
    },

    async createLocality(payload: {
      sub_ward_id: string
      code: string
      name: string
      center_lat: number
      center_lng: number
      radius_meters?: number
      beat_type?: string
    }): Promise<LocalityBeat> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/localities`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to create locality/beat')
      }
      return res.json()
    },

    async verifyLocation(lat: number, lng: number, selectedWard?: string): Promise<LocationVerificationResult> {
      const res = await fetch(`${BASE_URL}/hierarchy/verify-location`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          latitude: lat,
          longitude: lng,
          selected_ward: selectedWard,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Location verification failed')
      }
      return res.json()
    },

    async getMyJurisdiction(): Promise<{
      id?: string
      user_id: string
      authority_id?: string
      ward_code?: string
      sub_ward_id?: string
      jurisdiction_level?: string
      role?: string
      assigned_ward_id?: string
      assigned_sub_ward_id?: string
    } | null> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/jurisdiction/me`, { headers })
      if (!res.ok) throw new Error('Failed to fetch officer jurisdiction')
      return res.json()
    },

    async assignSupervisor(payload: {
      user_id: string
      ward_id?: string
      sub_ward_id?: string
      role_title?: string
    }): Promise<{ success: boolean; message: string }> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader('admin')
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/hierarchy/supervisors/assign`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to assign supervisor')
      }
      return res.json()
    },

    async correctIssueJurisdiction(
      issueId: string,
      payload: {
        new_authority_id?: string
        new_ward?: string
        ward_code?: string
        new_sub_ward_id?: string
        sub_ward_id?: string
        reason: string
      }
    ): Promise<Issue> {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      const body = {
        ward_code: payload.ward_code || payload.new_ward,
        sub_ward_id: payload.sub_ward_id || payload.new_sub_ward_id,
        reason: payload.reason,
      }

      const res = await fetch(`${BASE_URL}/issues/${encodeURIComponent(issueId)}/jurisdiction`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Failed to correct issue jurisdiction')
      }
      return res.json()
    },

    async getIssueJurisdictionHistory(issueId: string): Promise<JurisdictionAuditLog[]> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/issues/${encodeURIComponent(issueId)}/jurisdiction-history`, { headers })
      if (!res.ok) throw new Error('Failed to fetch jurisdiction history')
      return res.json()
    },

    async getGisBoundaries(): Promise<any> {
      const res = await fetch(`${BASE_URL}/gis/boundaries`)
      if (!res.ok) throw new Error('Failed to fetch GIS boundaries')
      return res.json()
    },
  },

  auth: {
    async login(payload: { usernameOrEmail: string; password: string; expectedRole?: string }): Promise<AuthResponse> {
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Login failed. Please check your credentials.')
      }
      return res.json()
    },

    async register(payload: { username: string; email: string; password: string; name: string }): Promise<AuthResponse> {
      const res = await fetch(`${BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...payload, role: 'citizen' }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Registration failed. Please try again.')
      }
      return res.json()
    },

    async me(): Promise<AuthUser> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      const res = await fetch(`${BASE_URL}/auth/me`, { headers })
      if (!res.ok) throw new Error('Unauthorized session')
      return res.json()
    },

    async logout(): Promise<void> {
      const headers: Record<string, string> = {}
      const auth = getAuthHeader()
      if (auth) headers['Authorization'] = auth

      await fetch(`${BASE_URL}/auth/logout`, { method: 'POST', headers }).catch(() => {})
      if (typeof window !== 'undefined') {
        localStorage.removeItem('civilens_auth_token')
        localStorage.removeItem('civilens_user_profile')
      }
    },
  },
}
