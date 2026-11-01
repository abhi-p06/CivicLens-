import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  Settings2,
  Save,
  RotateCcw,
  Zap,
  AlertCircle,
  Users,
  Building,
  Wrench,
  Plus,
  Trash2,
  Edit2,
  Check,
  MapPin,
  Phone,
  Shield,
  Layers,
  BookOpen,
  Globe,
  RefreshCw,
  FileText,
} from 'lucide-react'
import { api } from '../../services/api'
import { IssueCategory, FieldTeam, WardConfig, GuidanceSource, GuidanceDocument } from '../../types'
import { useCivicMotion, MotionMode } from '../../lib/motionContext'
import { useAuth } from '../../context/AuthContext'
import { Portal } from './Portal'
import { cn } from '../../lib/utils'
import { GuidanceDocumentModal } from '../guidance/GuidanceDocumentModal'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onConfigSaved: () => void
}

type SettingsTab = 'routing' | 'teams' | 'wards' | 'guidance'

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onConfigSaved,
}) => {
  const { motionMode, setMotionMode } = useCivicMotion()
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [activeTab, setActiveTab] = useState<SettingsTab>('routing')

  // Routing Config State
  const [config, setConfig] = useState<Record<string, any>>({})
  const [selectedCategory, setSelectedCategory] = useState<string>('Roads & Footpaths')
  const [department, setDepartment] = useState('')
  const [code, setCode] = useState('')
  const [criticalAction, setCriticalAction] = useState('')
  const [criticalSla, setCriticalSla] = useState(12)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Teams Management State
  const [teams, setTeams] = useState<FieldTeam[]>([])
  const [loadingTeams, setLoadingTeams] = useState(false)
  const [showAddTeam, setShowAddTeam] = useState(false)
  const [newTeamName, setNewTeamName] = useState('')
  const [newTeamDept, setNewTeamDept] = useState('Roads & Footpaths')
  const [newTeamWard, setNewTeamWard] = useState('N-Ward')
  const [newTeamLead, setNewTeamLead] = useState('')
  const [submittingTeam, setSubmittingTeam] = useState(false)

  // Ward Settings State
  const [wards, setWards] = useState<WardConfig[]>([])
  const [loadingWards, setLoadingWards] = useState(false)
  const [editingWard, setEditingWard] = useState<string | null>(null)
  const [wardLeadOfficer, setWardLeadOfficer] = useState('')
  const [submittingWard, setSubmittingWard] = useState(false)

  // Guidance Sources & Documents State (AI Research)
  const [guidanceSources, setGuidanceSources] = useState<GuidanceSource[]>([])
  const [guidanceDocuments, setGuidanceDocuments] = useState<GuidanceDocument[]>([])
  const [loadingGuidance, setLoadingGuidance] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [ingestUrl, setIngestUrl] = useState('')
  const [ingestSourceId, setIngestSourceId] = useState('')
  const [ingestMessage, setIngestMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [previewDocId, setPreviewDocId] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadConfig()
      if (isAdmin) {
        loadTeams()
        loadWards()
        loadGuidance()
      }
    }
  }, [isOpen, isAdmin])

  const loadGuidance = async () => {
    setLoadingGuidance(true)
    try {
      const [srcs, docs] = await Promise.all([
        api.adminGuidance.listSources(),
        api.adminGuidance.listDocuments(),
      ])
      setGuidanceSources(srcs)
      setGuidanceDocuments(docs)
    } catch (err: any) {
      console.error('Failed to load guidance sources/documents:', err)
    } finally {
      setLoadingGuidance(false)
    }
  }

  const handleToggleSource = async (source: GuidanceSource) => {
    try {
      const updated = await api.adminGuidance.updateSource(source.id, {
        is_active: !source.is_active,
      })
      setGuidanceSources((prev) => prev.map((s) => (s.id === source.id ? updated : s)))
    } catch (err: any) {
      console.error(err)
    }
  }

  const handleUpdateDocumentStatus = async (docId: string, newStatus: string) => {
    try {
      const updated = await api.adminGuidance.updateDocument(docId, {
        document_status: newStatus,
      })
      setGuidanceDocuments((prev) => prev.map((d) => (d.id === docId ? updated : d)))
    } catch (err: any) {
      console.error(err)
    }
  }

  const handleTriggerIngest = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!ingestUrl.trim() && !ingestSourceId) return
    setIngesting(true)
    setIngestMessage(null)
    try {
      const res = await api.adminGuidance.ingestSource({
        source_url: ingestUrl.trim() || undefined,
        source_id: ingestSourceId || undefined,
        force_refresh: true,
      })
      setIngestMessage({ type: 'success', text: res.message || 'Source successfully ingested.' })
      setIngestUrl('')
      setIngestSourceId('')
      loadGuidance()
      setTimeout(() => setIngestMessage(null), 4000)
    } catch (err: any) {
      setIngestMessage({ type: 'error', text: err.message || 'Ingestion failed.' })
    } finally {
      setIngesting(false)
    }
  }

  const loadConfig = async () => {
    try {
      const cfg = await api.getRoutingConfig()
      setConfig(cfg)
      if (cfg[selectedCategory]) {
        updateFormFields(selectedCategory, cfg)
      }
    } catch (err: any) {
      console.error(err)
      setErrorMessage(err?.message || 'Failed to load configuration.')
    }
  }

  const loadTeams = async () => {
    setLoadingTeams(true)
    try {
      const data = await api.admin.getTeams()
      setTeams(data)
    } catch (err) {
      console.error('Failed to load teams:', err)
    } finally {
      setLoadingTeams(false)
    }
  }

  const loadWards = async () => {
    setLoadingWards(true)
    try {
      const data = await api.admin.getWards()
      setWards(data)
    } catch (err) {
      console.error('Failed to load wards:', err)
    } finally {
      setLoadingWards(false)
    }
  }

  const updateFormFields = (cat: string, cfg: Record<string, any>) => {
    const data = cfg[cat]
    if (data) {
      setDepartment(data.department || '')
      setCode(data.code || '')
      const crit = data.actions?.CRITICAL
      if (Array.isArray(crit)) {
        setCriticalAction(crit[0] || '')
        setCriticalSla(Number(crit[1]) || 12)
      } else {
        setCriticalAction(typeof crit === 'string' ? crit : '')
        setCriticalSla(Number(data.slaHours?.CRITICAL) || 12)
      }
    }
  }

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat)
    setErrorMessage(null)
    updateFormFields(cat, config)
  }

  const handleSaveRouting = async () => {
    setSaving(true)
    setSavedSuccess(false)
    setErrorMessage(null)
    try {
      const currentCatData = config[selectedCategory] || {}
      const updatedCatConfig = {
        ...currentCatData,
        department: department.trim(),
        code: code.trim(),
        actions: {
          ...currentCatData.actions,
          CRITICAL: [criticalAction.trim(), Number(criticalSla)],
        },
        slaHours: {
          ...currentCatData.slaHours,
          CRITICAL: Number(criticalSla),
        },
      }
      const res = await api.updateRoutingConfig(selectedCategory, updatedCatConfig)
      const updatedConfig = {
        ...config,
        [selectedCategory]: res?.config || updatedCatConfig,
      }
      setConfig(updatedConfig)
      setSavedSuccess(true)
      onConfigSaved()
      setTimeout(() => setSavedSuccess(false), 2500)
    } catch (err: any) {
      console.error('Failed to update routing configuration:', err)
      setErrorMessage(err?.message || 'Failed to update department routing rules.')
    } finally {
      setSaving(false)
    }
  }

  // Handle Team Availability Toggle
  const handleToggleTeamAvailability = async (team: FieldTeam) => {
    const nextStatus =
      team.status === 'AVAILABLE'
        ? 'BUSY'
        : team.status === 'BUSY'
        ? 'OFF_DUTY'
        : 'AVAILABLE'
    try {
      const updated = await api.admin.updateTeam(team.id, { status: nextStatus })
      setTeams((prev) => prev.map((t) => (t.id === team.id ? updated : t)))
    } catch (err) {
      console.error(err)
    }
  }

  // Handle Create Team
  const handleCreateTeamSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTeamName.trim() || !newTeamLead.trim()) return
    setSubmittingTeam(true)
    try {
      const created = await api.admin.createTeam({
        name: newTeamName.trim(),
        department: newTeamDept,
        category: newTeamDept.includes('Road') ? 'road_maintenance' : 'sanitation',
        ward: newTeamWard,
        contact_lead: newTeamLead.trim(),
        status: 'AVAILABLE',
      })
      setTeams((prev) => [...prev, created])
      setNewTeamName('')
      setNewTeamLead('')
      setShowAddTeam(false)
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingTeam(false)
    }
  }

  // Handle Delete Team
  const handleDeleteTeam = async (teamId: string) => {
    if (!confirm('Are you sure you want to remove this operational team?')) return
    try {
      await api.admin.deleteTeam(teamId)
      setTeams((prev) => prev.filter((t) => t.id !== teamId))
    } catch (err) {
      console.error(err)
    }
  }

  // Handle Ward Update
  const handleSaveWard = async (wardCode: string) => {
    if (!wardLeadOfficer.trim()) return
    setSubmittingWard(true)
    try {
      const updated = await api.admin.updateWard(wardCode, {
        lead_officer: wardLeadOfficer.trim(),
      })
      setWards((prev) => prev.map((w) => (w.ward_code === wardCode ? updated : w)))
      setEditingWard(null)
      setWardLeadOfficer('')
    } catch (err) {
      console.error(err)
    } finally {
      setSubmittingWard(false)
    }
  }

  const categories = Object.keys(config)

  return (
    <Portal>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[9000] layer-modal-backdrop bg-black/50 backdrop-blur-xs flex items-center justify-center p-4"
            onClick={onClose}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-[9001] layer-modal-content w-full max-w-3xl bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl overflow-hidden font-sans text-xs flex flex-col max-h-[85vh]"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-6 py-4 border-b border-[#E4E7F1] bg-[#F0F2F9] shrink-0">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-[#6457E8]/10 text-[#6457E8]">
                    <Settings2 className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="font-bold text-[#11162A] text-sm tracking-normal block">
                      Operations Management & Administration
                    </span>
                    <span className="text-[11px] text-[#65708B]">
                      {isAdmin ? 'Admin Console: Departments, Field Teams & Ward Settings' : 'Municipal Routing & Motion Configuration'}
                    </span>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="text-[#65708B] hover:text-[#11162A] p-1.5 rounded-lg hover:bg-black/5 transition cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Navigation Tabs */}
              {isAdmin && (
                <div className="px-6 pt-3 bg-white border-b border-[#E4E7F1] flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => setActiveTab('routing')}
                    className={cn(
                      'px-3.5 py-2 font-semibold text-xs border-b-2 transition cursor-pointer flex items-center gap-1.5',
                      activeTab === 'routing'
                        ? 'border-[#6457E8] text-[#6457E8]'
                        : 'border-transparent text-[#65708B] hover:text-[#11162A]'
                    )}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>Department Routing</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('teams')}
                    className={cn(
                      'px-3.5 py-2 font-semibold text-xs border-b-2 transition cursor-pointer flex items-center gap-1.5',
                      activeTab === 'teams'
                        ? 'border-[#6457E8] text-[#6457E8]'
                        : 'border-transparent text-[#65708B] hover:text-[#11162A]'
                    )}
                  >
                    <Users className="w-3.5 h-3.5" />
                    <span>Field Teams ({teams.length})</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('wards')}
                    className={cn(
                      'px-3.5 py-2 font-semibold text-xs border-b-2 transition cursor-pointer flex items-center gap-1.5',
                      activeTab === 'wards'
                        ? 'border-[#6457E8] text-[#6457E8]'
                        : 'border-transparent text-[#65708B] hover:text-[#11162A]'
                    )}
                  >
                    <Building className="w-3.5 h-3.5" />
                    <span>Ward Settings ({wards.length})</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('guidance')}
                    className={cn(
                      'px-3.5 py-2 font-semibold text-xs border-b-2 transition cursor-pointer flex items-center gap-1.5',
                      activeTab === 'guidance'
                        ? 'border-[#6457E8] text-[#6457E8]'
                        : 'border-transparent text-[#65708B] hover:text-[#11162A]'
                    )}
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    <span>Guidance Sources ({guidanceSources.length})</span>
                  </button>
                </div>
              )}

              {/* Tab 1: Routing Configuration */}
              {activeTab === 'routing' && (
                <div className="p-6 space-y-4 overflow-y-auto bg-[#F6F7FC] flex-1">
                  <div className="text-[#65708B] text-xs font-sans leading-relaxed">
                    Configure dynamic department assignments, automated action directives, and target SLA hours. This decouples administrative dispatch protocols from machine learning inference.
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-[#65708B] font-semibold text-xs">Select Target Domain</label>
                    <div className="flex flex-wrap gap-1.5">
                      {categories.map((cat) => (
                        <button
                          key={cat}
                          type="button"
                          onClick={() => handleCategoryChange(cat)}
                          className={cn(
                            'px-3 py-1.5 rounded-lg text-xs border transition cursor-pointer',
                            selectedCategory === cat
                              ? 'bg-[#6457E8] border-[#6457E8] text-white font-semibold shadow-xs'
                              : 'bg-white border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50'
                          )}
                        >
                          {cat}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <label className="text-[#11162A] font-semibold text-xs">Responsible Department</label>
                      <input
                        type="text"
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] shadow-xs"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[#11162A] font-semibold text-xs">Department Agency Code</label>
                      <input
                        type="text"
                        value={code}
                        onChange={(e) => setCode(e.target.value)}
                        className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] shadow-xs"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="text-[#11162A] font-semibold text-xs">Emergency Action Directive (Critical Incidents)</label>
                    <textarea
                      rows={2}
                      value={criticalAction}
                      onChange={(e) => setCriticalAction(e.target.value)}
                      className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] shadow-xs font-sans leading-relaxed"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-[#11162A] font-semibold text-xs">Target Resolution Window (Hours SLA)</label>
                    <input
                      type="number"
                      value={criticalSla}
                      onChange={(e) => setCriticalSla(Number(e.target.value))}
                      className="w-32 bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] shadow-xs"
                    />
                  </div>

                  {/* Animation & Accessibility Preferences */}
                  <div className="pt-3 border-t border-[#E4E7F1] space-y-2">
                    <div className="flex items-center gap-1.5 text-[#11162A] font-semibold text-xs">
                      <Zap className="w-3.5 h-3.5 text-[#6457E8]" />
                      <span>UI Animations & Motion Accessibility</span>
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      {(['full', 'system', 'reduced'] as MotionMode[]).map((mode) => (
                        <button
                          key={mode}
                          type="button"
                          onClick={() => setMotionMode(mode)}
                          className={cn(
                            'p-2.5 rounded-lg border text-xs font-medium transition cursor-pointer text-center',
                            motionMode === mode
                              ? 'bg-[#6457E8] border-[#6457E8] text-white font-semibold shadow-xs'
                              : 'bg-white border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50'
                          )}
                        >
                          {mode === 'full' ? 'Full Motion' : mode === 'system' ? 'System Match' : 'Reduced'}
                        </button>
                      ))}
                    </div>
                  </div>

                  {savedSuccess && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
                      <span>Routing rule successfully updated in active system registry.</span>
                    </div>
                  )}

                  {errorMessage && (
                    <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                      <span>{errorMessage}</span>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Field Teams Management */}
              {activeTab === 'teams' && (
                <div className="p-6 space-y-4 overflow-y-auto bg-[#F6F7FC] flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-[#11162A]">Predefined Municipal Field Teams</h3>
                      <p className="text-xs text-[#65708B] mt-0.5">
                        Manage teams, toggle real-time operational availability, and assign ward jurisdictions
                      </p>
                    </div>

                    <button
                      onClick={() => setShowAddTeam(!showAddTeam)}
                      className="px-3 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-xl text-xs font-semibold shadow-xs transition flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{showAddTeam ? 'Cancel' : 'Add Team'}</span>
                    </button>
                  </div>

                  {/* Add Team Inline Form */}
                  {showAddTeam && (
                    <form onSubmit={handleCreateTeamSubmit} className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-3">
                      <span className="text-xs font-bold text-[#11162A] block">Add New Operational Team</span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div>
                          <label className="text-[11px] text-[#65708B] font-semibold block mb-1">Team Name</label>
                          <input
                            type="text"
                            placeholder="e.g., Road Resurfacing Crew Gamma"
                            value={newTeamName}
                            onChange={(e) => setNewTeamName(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-lg p-2 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] text-[#65708B] font-semibold block mb-1">Department</label>
                          <select
                            value={newTeamDept}
                            onChange={(e) => setNewTeamDept(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-lg p-2 text-xs outline-none focus:border-[#6457E8]"
                          >
                            <option value="Roads & Footpaths">Roads & Footpaths</option>
                            <option value="Sanitation & Garbage">Sanitation & Garbage</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[11px] text-[#65708B] font-semibold block mb-1">Assigned Ward</label>
                          <input
                            type="text"
                            placeholder="e.g., N-Ward, L-Ward"
                            value={newTeamWard}
                            onChange={(e) => setNewTeamWard(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-lg p-2 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>
                        <div>
                          <label className="text-[11px] text-[#65708B] font-semibold block mb-1">Team Contact Lead</label>
                          <input
                            type="text"
                            placeholder="e.g., Vikram Shinde (+91 98200 11223)"
                            value={newTeamLead}
                            onChange={(e) => setNewTeamLead(e.target.value)}
                            className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-lg p-2 text-xs outline-none focus:border-[#6457E8]"
                          />
                        </div>
                      </div>

                      <div className="flex justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setShowAddTeam(false)}
                          className="px-3 py-1.5 text-xs text-[#65708B] hover:text-[#11162A]"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          disabled={submittingTeam || !newTeamName.trim()}
                          className="px-4 py-1.5 bg-[#6457E8] text-white rounded-lg text-xs font-semibold hover:bg-[#5145CF] disabled:opacity-50 transition cursor-pointer"
                        >
                          {submittingTeam ? 'Adding...' : 'Create Team'}
                        </button>
                      </div>
                    </form>
                  )}

                  {/* Teams Table */}
                  <div className="bg-white border border-[#E4E7F1] rounded-xl overflow-hidden shadow-xs">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-[#E4E7F1] bg-[#F6F7FC] text-[#65708B] font-semibold">
                          <th className="py-2.5 px-3">Team Name</th>
                          <th className="py-2.5 px-3">Department</th>
                          <th className="py-2.5 px-3">Ward</th>
                          <th className="py-2.5 px-3">Lead / Contact</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E4E7F1]/70">
                        {teams.map((t) => (
                          <tr key={t.id} className="hover:bg-[#F0F2F9]/50 transition">
                            <td className="py-3 px-3 font-semibold text-[#11162A]">
                              <div className="flex items-center gap-1.5">
                                <Wrench className="w-3.5 h-3.5 text-[#6457E8]" />
                                <span>{t.name}</span>
                              </div>
                            </td>
                            <td className="py-3 px-3 text-[#65708B]">{t.department}</td>
                            <td className="py-3 px-3 font-medium text-[#11162A]">{t.ward}</td>
                            <td className="py-3 px-3 text-[#65708B]">{t.contact_lead}</td>
                            <td className="py-3 px-3">
                              <button
                                onClick={() => handleToggleTeamAvailability(t)}
                                title="Click to cycle status: AVAILABLE -> BUSY -> OFF_DUTY"
                                className={cn(
                                  'px-2.5 py-0.5 rounded-full text-[11px] font-semibold border transition cursor-pointer',
                                  t.status === 'AVAILABLE'
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                                    : t.status === 'BUSY'
                                    ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                                    : 'bg-slate-100 text-slate-600 border-slate-300 hover:bg-slate-200'
                                )}
                              >
                                {t.status}
                              </button>
                            </td>
                            <td className="py-3 px-3 text-right">
                              <button
                                onClick={() => handleDeleteTeam(t.id)}
                                className="p-1 rounded-md text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition cursor-pointer"
                                title="Remove team"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Tab 3: Ward Settings */}
              {activeTab === 'wards' && (
                <div className="p-6 space-y-4 overflow-y-auto bg-[#F6F7FC] flex-1">
                  <div>
                    <h3 className="text-sm font-bold text-[#11162A]">Municipal Ward Jurisdictions</h3>
                    <p className="text-xs text-[#65708B] mt-0.5">
                      Configure ward lead officers, response zones, and team allocations
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-3">
                    {wards.map((w) => {
                      const isEditing = editingWard === w.ward_code
                      return (
                        <div key={w.ward_code} className="p-4 bg-white border border-[#E4E7F1] rounded-xl shadow-xs space-y-2">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <Building className="w-4 h-4 text-[#6457E8]" />
                              <span className="font-bold text-[#11162A] text-xs">
                                {w.ward_name} ({w.ward_code})
                              </span>
                            </div>

                            {!isEditing ? (
                              <button
                                onClick={() => {
                                  setEditingWard(w.ward_code)
                                  setWardLeadOfficer(w.lead_officer)
                                }}
                                className="p-1.5 rounded-lg text-slate-400 hover:text-[#6457E8] hover:bg-[#6457E8]/10 transition cursor-pointer"
                                title="Edit Ward Officer"
                              >
                                <Edit2 className="w-3.5 h-3.5" />
                              </button>
                            ) : (
                              <div className="flex items-center gap-1.5">
                                <button
                                  onClick={() => setEditingWard(null)}
                                  className="px-2 py-1 text-slate-500 hover:text-slate-800 text-xs"
                                >
                                  Cancel
                                </button>
                                <button
                                  onClick={() => handleSaveWard(w.ward_code)}
                                  disabled={submittingWard}
                                  className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs font-semibold hover:bg-emerald-700 disabled:opacity-50"
                                >
                                  Save
                                </button>
                              </div>
                            )}
                          </div>

                          <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-[#E4E7F1]">
                            <div>
                              <span className="text-[#65708B] block text-[11px]">Ward Lead Officer</span>
                              {!isEditing ? (
                                <strong className="text-[#11162A]">{w.lead_officer}</strong>
                              ) : (
                                <input
                                  type="text"
                                  value={wardLeadOfficer}
                                  onChange={(e) => setWardLeadOfficer(e.target.value)}
                                  className="w-full bg-[#F0F2F9] border border-[#E4E7F1] rounded-md px-2 py-1 text-xs outline-none focus:border-[#6457E8]"
                                />
                              )}
                            </div>

                            <div>
                              <span className="text-[#65708B] block text-[11px]">Jurisdiction</span>
                              <span className="text-[#11162A] font-medium">Mumbai Metropolitan</span>
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* Tab 4: Official Guidance Sources & Knowledge Base */}
              {activeTab === 'guidance' && (
                <div className="p-6 space-y-5 overflow-y-auto bg-[#F6F7FC] flex-1 text-xs">
                  {/* Top Explainer & Live Ingestion Card */}
                  <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                    <div>
                      <span className="font-bold text-sm text-[#11162A] block">
                        Government Source Allowlist & Live Web Ingestion
                      </span>
                      <p className="text-[#65708B] text-xs mt-0.5 leading-relaxed">
                        CIVILENS AI Field Guidance retrieves and synthesizes recommendations exclusively from authorized
                        government portals (MoRTH, MCGM, CPCB, CPHEEO, MPCB). Commercial blogs and social media are strictly prohibited.
                      </p>
                    </div>

                    {/* Ingestion Trigger Form */}
                    <form onSubmit={handleTriggerIngest} className="p-3 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-3">
                      <div className="flex items-center gap-2 text-xs font-bold text-[#11162A]">
                        <RefreshCw className="w-4 h-4 text-[#6457E8]" />
                        <span>Scrape & Ingest Official Document</span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                        <div className="sm:col-span-2">
                          <label className="text-[11px] font-semibold text-[#65708B] block mb-1">
                            Direct Government URL (HTML or PDF)
                          </label>
                          <input
                            type="url"
                            value={ingestUrl}
                            onChange={(e) => setIngestUrl(e.target.value)}
                            placeholder="https://morth.nic.in/... or https://portal.mcgm.gov.in/..."
                            className="w-full bg-white border border-[#E4E7F1] rounded-lg px-2.5 py-1.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8]"
                          />
                        </div>

                        <div>
                          <label className="text-[11px] font-semibold text-[#65708B] block mb-1">
                            Or Select Registered Source
                          </label>
                          <select
                            value={ingestSourceId}
                            onChange={(e) => setIngestSourceId(e.target.value)}
                            className="w-full bg-white border border-[#E4E7F1] rounded-lg p-1.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8]"
                          >
                            <option value="">-- Choose Source --</option>
                            {guidanceSources.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.name} ({s.domain})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <div className="flex items-center justify-between pt-1">
                        {ingestMessage ? (
                          <span
                            className={`text-[11px] font-semibold ${
                              ingestMessage.type === 'success' ? 'text-emerald-700' : 'text-rose-700'
                            }`}
                          >
                            {ingestMessage.text}
                          </span>
                        ) : (
                          <span className="text-[11px] text-[#65708B]">
                            SHA-256 change detection automatically archives updated circulars as new versions.
                          </span>
                        )}

                        <button
                          type="submit"
                          disabled={ingesting || (!ingestUrl.trim() && !ingestSourceId)}
                          className="px-4 py-1.5 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-lg text-xs font-semibold shadow-2xs transition cursor-pointer disabled:opacity-50 flex items-center gap-1.5 shrink-0"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${ingesting ? 'animate-spin' : ''}`} />
                          <span>{ingesting ? 'Scraping & Parsing...' : 'Ingest Document'}</span>
                        </button>
                      </div>
                    </form>
                  </div>

                  {/* Registered Sources Table */}
                  <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#11162A] uppercase tracking-wider">
                        Authorized Government Sources ({guidanceSources.length})
                      </span>
                      <button
                        type="button"
                        onClick={loadGuidance}
                        className="text-[11px] text-[#6457E8] hover:underline flex items-center gap-1 font-semibold"
                      >
                        <RefreshCw className="w-3 h-3" /> Refresh Registry
                      </button>
                    </div>

                    <div className="divide-y divide-[#E4E7F1] border border-[#E4E7F1] rounded-xl overflow-hidden">
                      {guidanceSources.map((source) => (
                        <div
                          key={source.id}
                          className="p-3 bg-white hover:bg-[#F6F7FC] transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                        >
                          <div className="space-y-0.5">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-[#11162A]">{source.name}</span>
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-violet-50 text-[#6457E8] border border-[#6457E8]/20">
                                {source.domain}
                              </span>
                              {source.is_allowlisted && (
                                <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                  Allowlisted
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-[#65708B] flex items-center gap-2">
                              <span>Domain: {source.category}</span>
                              <span>&bull;</span>
                              <span>Status: <strong className="text-emerald-700">{source.last_status || 'OK'}</strong></span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleToggleSource(source)}
                              className={`px-3 py-1 rounded-md text-xs font-semibold transition cursor-pointer ${
                                source.is_active
                                  ? 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200'
                                  : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                              }`}
                            >
                              {source.is_active ? 'Active' : 'Disabled'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Ingested Documents Catalog */}
                  <div className="p-4 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#11162A] uppercase tracking-wider">
                        Indexed Specifications Catalog ({guidanceDocuments.length})
                      </span>
                      <span className="text-[11px] text-[#65708B]">
                        Active documents queried for grounded field advice
                      </span>
                    </div>

                    <div className="space-y-2">
                      {guidanceDocuments.map((doc) => (
                        <div
                          key={doc.id}
                          className="p-3 bg-white border border-[#E4E7F1] rounded-xl hover:border-[#6457E8]/40 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-2xs"
                        >
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-[#11162A] truncate">{doc.title}</span>
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                                  doc.document_status === 'CURRENT'
                                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                    : doc.document_status === 'SUPERSEDED'
                                    ? 'bg-slate-100 text-slate-600 border border-slate-200'
                                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                                }`}
                              >
                                {doc.document_status}
                              </span>
                            </div>
                            <div className="text-[11px] text-[#65708B] flex items-center gap-2">
                              <span>{doc.source_org}</span>
                              <span>&bull;</span>
                              <span className="font-mono">{doc.document_version}</span>
                              <span>&bull;</span>
                              <span>{doc.applicable_category}</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <select
                              value={doc.document_status}
                              onChange={(e) => handleUpdateDocumentStatus(doc.id, e.target.value)}
                              className="bg-[#F0F2F9] border border-[#E4E7F1] rounded-md px-2 py-1 text-[11px] font-semibold text-[#11162A] outline-none"
                            >
                              <option value="CURRENT">CURRENT</option>
                              <option value="SUPERSEDED">SUPERSEDED</option>
                              <option value="DRAFT">DRAFT</option>
                            </select>

                            <button
                              type="button"
                              onClick={() => setPreviewDocId(doc.id)}
                              className="px-2.5 py-1 bg-[#F0F2F9] hover:bg-[#6457E8] hover:text-white text-[#11162A] font-semibold rounded-md text-xs transition cursor-pointer"
                            >
                              View
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Footer */}
              <div className="px-6 py-4 bg-white border-t border-[#E4E7F1] flex items-center justify-between shrink-0">
                <span className="text-xs text-[#65708B]">Civilens Operations Engine &bull; Aurora Indigo</span>
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-3.5 py-2 bg-transparent hover:bg-slate-100 text-[#65708B] hover:text-[#11162A] rounded-lg text-xs font-medium transition cursor-pointer"
                  >
                    Close
                  </button>
                  {activeTab === 'routing' && (
                    <button
                      onClick={handleSaveRouting}
                      disabled={saving}
                      className="flex items-center gap-1.5 px-4 py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-lg font-semibold text-xs transition disabled:opacity-50 shadow-xs cursor-pointer"
                    >
                      <Save className="w-3.5 h-3.5" />
                      <span>{saving ? 'Saving...' : 'Apply Protocol'}</span>
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Official Specification Preview Modal */}
      <GuidanceDocumentModal
        docId={previewDocId}
        onClose={() => setPreviewDocId(null)}
      />
    </Portal>
  )
}

export default SettingsModal
