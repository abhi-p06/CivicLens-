import { Issue, HotspotInfo, RecurrenceInfo, EvaluationMetrics } from '../types'

const BASE_URL = '/api/v1'

export const api = {
  async getHealth(): Promise<{ status: string; models: Record<string, string>; activeIssues: number }> {
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

  async submitIssue(payload: {
    complaintText: string
    location?: string
    imageUrl?: string
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
    const res = await fetch(`${BASE_URL}/issues/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note }),
    })
    if (!res.ok) throw new Error('Failed to update status')
    return res.json()
  },

  async verifyResolution(id: string, postActionImageUrl: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/issues/${id}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ postActionImageUrl }),
    })
    if (!res.ok) throw new Error('Failed to verify resolution')
    return res.json()
  },

  async getRoutingConfig(): Promise<Record<string, any>> {
    const res = await fetch(`${BASE_URL}/routing/config`)
    if (!res.ok) throw new Error('Failed to fetch routing config')
    return res.json()
  },

  async updateRoutingConfig(category: string, config: any): Promise<any> {
    const res = await fetch(`${BASE_URL}/routing/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, config }),
    })
    if (!res.ok) throw new Error('Failed to update routing config')
    return res.json()
  },

  async getEvaluationMetrics(): Promise<EvaluationMetrics> {
    const res = await fetch(`${BASE_URL}/evaluation/metrics`)
    if (!res.ok) throw new Error('Failed to fetch evaluation metrics')
    return res.json()
  },

  async resetDemo(): Promise<any> {
    const res = await fetch(`${BASE_URL}/demo/reset`, { method: 'POST' })
    if (!res.ok) throw new Error('Failed to reset demo')
    return res.json()
  },
}
