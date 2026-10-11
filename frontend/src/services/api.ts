import { Issue, HotspotInfo, RecurrenceInfo, EvaluationMetrics, SystemHealth, ResolutionEvidence } from '../types'

const BASE_URL = '/api/v1'

/**
 * Resolves authorization headers for role-restricted operations.
 * - In local demo/development mode: falls back to documented demo tokens if enabled.
 * - In production mode: strictly requires an authenticated session/token from storage
 *   and NEVER ships functional static privileged credentials.
 */
function getAuthHeader(role: 'inspector' | 'admin'): string | undefined {
  if (typeof window !== 'undefined') {
    const sessionToken = localStorage.getItem(`civilens_${role}_token`) || localStorage.getItem('civilens_auth_token')
    if (sessionToken) {
      return sessionToken.startsWith('Bearer ') ? sessionToken : `Bearer ${sessionToken}`
    }
  }

  // Allow development tokens only in development or when explicitly enabled in environment
  const isDev = import.meta.env.DEV
  const demoAuthAllowed = isDev || import.meta.env.VITE_CIVILENS_DEMO_AUTH === 'true'

  if (demoAuthAllowed) {
    return role === 'admin' ? 'Bearer demo-admin-token' : 'Bearer demo-inspector-token'
  }

  return undefined
}

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${BASE_URL}/health`)
    if (!res.ok) throw new Error('Health check failed')
    return res.json()
  },

  async getIssues(params?: { category?: string; priority?: string; status?: string; ward?: string }): Promise<Issue[]> {
    const query = new URLSearchParams()
    if (params?.category) query.append('category', params.category)
    if (params?.priority) query.append('priority', params.priority)
    if (params?.status) query.append('status', params.status)
    if (params?.ward) query.append('ward', params.ward)

    const res = await fetch(`${BASE_URL}/issues?${query.toString()}`)
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
    imageUrl?: string
    uploadId?: string
    source?: string
  }): Promise<Issue> {
    const res = await fetch(`${BASE_URL}/issues`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error('Failed to submit issue')
    return res.json()
  },

  async analyzeComplaint(payload: {
    complaintText: string
    location?: string
    imageUrl?: string
    uploadId?: string
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
}
