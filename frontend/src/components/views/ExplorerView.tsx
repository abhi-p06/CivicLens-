import React, { useState, useMemo } from 'react'
import {
  Search,
  Filter,
  MapPin,
  Clock,
  ArrowUpDown,
  Building,
  Wrench,
  Calendar,
  ClipboardList,
  Eye,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Shield,
  Lock,
  Layers,
  Briefcase,
  UserCheck,
} from 'lucide-react'
import { Issue } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'
import { cn } from '../../lib/utils'
import { useAuth } from '../../context/AuthContext'

interface ExplorerViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

type ActionQueueTab =
  | 'ALL'
  | 'UNASSIGNED'
  | 'AWAITING_INSPECTION'
  | 'ASSIGNED'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'AWAITING_CONFIRMATION'
  | 'REOPENED'
  | 'JURISDICTION_REVIEW'

export const ExplorerView: React.FC<ExplorerViewProps> = ({ issues, onSelectIssue }) => {
  const { user } = useAuth()
  const isInspector = user?.role === 'inspector'
  const assignedWard = user?.jurisdiction?.ward_code || (isInspector ? 'N-Ward' : '')
  const assignedSubWard = user?.jurisdiction?.sub_ward_id
  const isRestrictedInspector = isInspector && Boolean(assignedWard)

  const [activeTab, setActiveTab] = useState<ActionQueueTab>('ALL')
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedWard, setSelectedWard] = useState<string>(isRestrictedInspector ? assignedWard : 'ALL')
  const [selectedSubWard, setSelectedSubWard] = useState<string>(
    user?.jurisdiction?.jurisdiction_level === 'SUB_WARD_SUPERVISOR' && assignedSubWard
      ? assignedSubWard
      : 'ALL'
  )
  const [selectedLocality, setSelectedLocality] = useState<string>('ALL')
  const [selectedDepartment, setSelectedDepartment] = useState<string>('ALL')
  const [sortField, setSortField] = useState<'priority' | 'time'>('priority')

  // Extract unique administrative wards
  const availableWards = useMemo(() => {
    const set = new Set<string>()
    issues.forEach((i) => {
      if (i.ward) set.add(i.ward)
    })
    return Array.from(set).sort()
  }, [issues])

  // Extract unique sub-wards, filtered by selected ward
  const availableSubWards = useMemo(() => {
    const map = new Map<string, string>()
    issues.forEach((i) => {
      if (selectedWard !== 'ALL' && i.ward !== selectedWard) return
      if (i.sub_ward_id && i.sub_ward_name) {
        map.set(i.sub_ward_id, i.sub_ward_name)
      }
    })
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
  }, [issues, selectedWard])

  // Extract unique localities, filtered by selected ward & sub-ward
  const availableLocalities = useMemo(() => {
    const set = new Set<string>()
    issues.forEach((i) => {
      if (selectedWard !== 'ALL' && i.ward !== selectedWard) return
      if (selectedSubWard !== 'ALL' && i.sub_ward_id !== selectedSubWard && i.sub_ward_name !== selectedSubWard) return
      if (i.locality_name) set.add(i.locality_name)
    })
    return Array.from(set).sort()
  }, [issues, selectedWard, selectedSubWard])

  // Helper filter logic for the operations queue filters
  const matchesTab = (issue: Issue, tab: ActionQueueTab): boolean => {
    const isResolved = issue.status === 'RESOLVED' || issue.status === 'Verified Closed'
    const statusNormalized = (issue.status || '').toUpperCase().replace(/[\s-]/g, '_')

    switch (tab) {
      case 'UNASSIGNED':
        return (!issue.assignment || !issue.assignment.team_name) && !isResolved
      case 'AWAITING_INSPECTION':
        return (
          statusNormalized === 'AWAITING_INSPECTION' ||
          (statusNormalized === 'OPEN' && !issue.timeline?.some((t) => t.event_type === 'INSPECTION_COMPLETED'))
        )
      case 'ASSIGNED':
        return statusNormalized === 'ASSIGNED'
      case 'SCHEDULED':
        return statusNormalized === 'SCHEDULED'
      case 'IN_PROGRESS':
        return (
          statusNormalized === 'IN_PROGRESS' ||
          statusNormalized === 'ACTION_IN_PROGRESS' ||
          statusNormalized === 'INPROGRESS'
        )
      case 'AWAITING_CONFIRMATION':
        return (
          statusNormalized === 'AWAITING_CONFIRMATION' ||
          statusNormalized === 'VERIFICATION'
        )
      case 'REOPENED':
        return statusNormalized === 'REOPENED'
      case 'JURISDICTION_REVIEW':
        return Boolean(issue.jurisdiction_review_required)
      case 'ALL':
      default:
        return true
    }
  }

  // Pre-calculate counts for each tab (within user's authorized scope if restricted)
  const scopedIssues = useMemo(() => {
    if (isRestrictedInspector && assignedWard) {
      return issues.filter((i) => i.ward === assignedWard)
    }
    return issues
  }, [issues, isRestrictedInspector, assignedWard])

  const counts: Record<ActionQueueTab, number> = {
    ALL: scopedIssues.length,
    UNASSIGNED: scopedIssues.filter((i) => matchesTab(i, 'UNASSIGNED')).length,
    AWAITING_INSPECTION: scopedIssues.filter((i) => matchesTab(i, 'AWAITING_INSPECTION')).length,
    ASSIGNED: scopedIssues.filter((i) => matchesTab(i, 'ASSIGNED')).length,
    SCHEDULED: scopedIssues.filter((i) => matchesTab(i, 'SCHEDULED')).length,
    IN_PROGRESS: scopedIssues.filter((i) => matchesTab(i, 'IN_PROGRESS')).length,
    AWAITING_CONFIRMATION: scopedIssues.filter((i) => matchesTab(i, 'AWAITING_CONFIRMATION')).length,
    REOPENED: scopedIssues.filter((i) => matchesTab(i, 'REOPENED')).length,
    JURISDICTION_REVIEW: scopedIssues.filter((i) => matchesTab(i, 'JURISDICTION_REVIEW')).length,
  }

  const tabs: { id: ActionQueueTab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'ALL', label: 'All Complaints', icon: Filter },
    { id: 'UNASSIGNED', label: 'Unassigned', icon: ClipboardList },
    { id: 'JURISDICTION_REVIEW', label: 'Review Required', icon: AlertTriangle },
    { id: 'AWAITING_INSPECTION', label: 'Awaiting Inspection', icon: Eye },
    { id: 'ASSIGNED', label: 'Assigned', icon: Wrench },
    { id: 'SCHEDULED', label: 'Scheduled', icon: Calendar },
    { id: 'IN_PROGRESS', label: 'In Progress', icon: Clock },
    { id: 'AWAITING_CONFIRMATION', label: 'Awaiting Confirmation', icon: CheckCircle2 },
    { id: 'REOPENED', label: 'Reopened', icon: RotateCcw },
  ]

  const categories = [
    { label: 'All Categories', value: 'ALL' },
    { label: 'Roads & Footpaths (Potholes / Damage)', value: 'Roads & Footpaths' },
    { label: 'Sanitation & Garbage (Litter / Dumps)', value: 'Sanitation & Garbage' },
    { label: 'Water Supply & Drainage', value: 'Water Supply & Drainage' },
    { label: 'Street Lighting', value: 'Street Lighting' },
  ]

  const departments = [
    { label: 'All Departments', value: 'ALL' },
    { label: 'Road Infrastructure Maintenance', value: 'Road Infrastructure Maintenance' },
    { label: 'Solid Waste Management & Sanitation', value: 'Solid Waste Management & Sanitation' },
    { label: 'Storm Water & Drainage', value: 'Storm Water & Drainage' },
    { label: 'Traffic & Street Furniture', value: 'Traffic & Street Furniture' },
  ]

  const filtered = issues.filter((i) => {
    // 1. Enforce inspector authorized ward boundary
    if (isRestrictedInspector && assignedWard && i.ward !== assignedWard) {
      return false
    }

    // 2. Ward filter
    const matchWard = selectedWard === 'ALL' || i.ward === selectedWard

    // 3. Sub-Ward filter
    const matchSubWard =
      selectedSubWard === 'ALL' ||
      i.sub_ward_id === selectedSubWard ||
      i.sub_ward_name === selectedSubWard

    // 4. Locality filter
    const matchLocality =
      selectedLocality === 'ALL' ||
      i.locality_name === selectedLocality

    // 5. Department filter
    const matchDepartment =
      selectedDepartment === 'ALL' ||
      i.department === selectedDepartment ||
      (selectedDepartment.includes('Road') && (i.department?.includes('Road') || i.category?.includes('Road'))) ||
      (selectedDepartment.includes('Waste') && (i.department?.includes('Waste') || i.category?.includes('Sanitation') || i.category?.includes('Garbage')))

    // 6. Search query
    const matchSearch =
      i.issueId.toLowerCase().includes(search.toLowerCase()) ||
      i.complaintText.toLowerCase().includes(search.toLowerCase()) ||
      i.location.toLowerCase().includes(search.toLowerCase()) ||
      (i.assignment?.team_name && i.assignment.team_name.toLowerCase().includes(search.toLowerCase())) ||
      (i.supervisor_name && i.supervisor_name.toLowerCase().includes(search.toLowerCase())) ||
      (i.locality_name && i.locality_name.toLowerCase().includes(search.toLowerCase())) ||
      (i.sub_ward_name && i.sub_ward_name.toLowerCase().includes(search.toLowerCase()))

    // 7. Category filter
    const matchCat =
      selectedCategory === 'ALL' ||
      i.category === selectedCategory ||
      (selectedCategory.includes('Road') && i.category?.includes('Road')) ||
      (selectedCategory.includes('Sanitation') && (i.category?.includes('Sanitation') || i.category?.includes('Garbage')))

    // 8. Tab / Queue status match
    const matchTab = matchesTab(i, activeTab)

    return matchWard && matchSubWard && matchLocality && matchDepartment && matchSearch && matchCat && matchTab
  })

  filtered.sort((a, b) => {
    if (sortField === 'priority') {
      return b.priorityScore - a.priorityScore
    }
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })

  return (
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-4 font-sans text-xs bg-[#F6F7FC]">
      {/* Header Banner */}
      <div className="bg-white border border-[#E4E7F1] rounded-2xl p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[#11162A]">
              My Action Queue
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-[#6457E8]/10 text-[#6457E8] border border-[#6457E8]/20 font-semibold">
              Ward Field Operations
            </span>

            {/* Jurisdiction Badge for Inspector */}
            {isInspector && (
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#13152E] text-white text-[11px] font-medium shadow-xs">
                <Shield className="w-3.5 h-3.5 text-[#6457E8]" />
                <span>Authorized Scope:</span>
                <span className="font-bold text-[#6457E8] font-mono">{assignedWard || 'N-Ward'}</span>
                {user?.jurisdiction?.sub_ward_id && (
                  <span className="text-[10px] bg-white/10 px-1.5 py-0.2 rounded font-mono text-slate-300">
                    {user.jurisdiction.sub_ward_id}
                  </span>
                )}
                <span className="text-[10px] text-slate-400">
                  ({user?.jurisdiction?.jurisdiction_level?.replace('_', ' ') || 'Ward Officer'})
                </span>
              </div>
            )}
          </div>
          <p className="text-xs text-[#65708B] mt-1">
            Manage complaints, verify geographical routing, dispatch field teams, schedule maintenance, and oversee repair workflows
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-[#F0F2F9] border border-[#E4E7F1] text-[#65708B] font-medium">
            Active Queue: <strong className="text-[#11162A] font-mono">{filtered.length}</strong> items
          </span>
        </div>
      </div>

      {/* 9 Filter Tabs (Horizontally Scrollable) */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs scrollbar-none">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          const count = counts[tab.id]
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-3.5 py-2 rounded-xl font-medium transition cursor-pointer whitespace-nowrap shadow-2xs',
                isActive
                  ? 'bg-[#13152E] text-white shadow-xs'
                  : 'bg-white border border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-[#F0F2F9]'
              )}
            >
              <Icon className={cn('w-3.5 h-3.5', isActive ? 'text-white' : 'text-[#6457E8]')} />
              <span>{tab.label}</span>
              <span
                className={cn(
                  'px-1.5 py-0.2 rounded-full text-[10px] font-semibold',
                  isActive ? 'bg-white/20 text-white' : 'bg-[#F0F2F9] text-[#65708B]'
                )}
              >
                {count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Hierarchical Geographical & Department Filter Controls */}
      <div className="bg-white border border-[#E4E7F1] rounded-2xl p-4 shadow-xs space-y-3">
        {/* Top Filter Row: Search + Category + Department */}
        <div className="flex flex-col md:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-[#65708B] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by keyword, issue ID, landmark, assigned team, supervisor, or locality..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl pl-9 pr-3 py-2 text-xs text-[#11162A] placeholder-[#65708B] outline-none focus:border-[#6457E8] font-sans"
            />
          </div>

          <div className="flex items-center gap-2 w-full md:w-auto flex-wrap">
            {/* Category Dropdown */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>

            {/* Department Dropdown */}
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl px-3 py-2 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              {departments.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>

            {/* Sort Toggle */}
            <button
              onClick={() => setSortField(sortField === 'priority' ? 'time' : 'priority')}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[#F0F2F9] hover:bg-slate-200 border border-[#E4E7F1] text-[#11162A] rounded-xl text-xs font-medium cursor-pointer transition whitespace-nowrap"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-[#6457E8]" />
              <span>Sort: {sortField === 'priority' ? 'Priority' : 'Time'}</span>
            </button>
          </div>
        </div>

        {/* Bottom Geographical Hierarchy Filter Row: Ward + Sub-Ward + Locality */}
        <div className="flex flex-col sm:flex-row items-center gap-2 pt-2 border-t border-[#E4E7F1]/60 text-xs">
          <div className="flex items-center gap-1.5 text-[#65708B] font-semibold text-[11px] uppercase tracking-wider shrink-0 mr-1">
            <Layers className="w-3.5 h-3.5 text-[#6457E8]" />
            <span>Jurisdiction:</span>
          </div>

          {/* Ward Selector (Locked for restricted inspector, selectable for admin) */}
          <div className="relative shrink-0">
            {isRestrictedInspector ? (
              <div className="flex items-center gap-1.5 bg-[#F0F2F9] border border-[#E4E7F1] px-3 py-1.5 rounded-xl text-xs font-semibold text-[#11162A]">
                <Lock className="w-3 h-3 text-amber-600" />
                <span>Ward: {assignedWard}</span>
                <span className="text-[10px] text-[#65708B] font-normal">(Authorized)</span>
              </div>
            ) : (
              <select
                value={selectedWard}
                onChange={(e) => {
                  setSelectedWard(e.target.value)
                  setSelectedSubWard('ALL')
                  setSelectedLocality('ALL')
                }}
                className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl px-3 py-1.5 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
              >
                <option value="ALL">All Administrative Wards</option>
                {availableWards.map((w) => (
                  <option key={w} value={w}>
                    {w}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Sub-Ward Selector */}
          <div className="shrink-0">
            <select
              value={selectedSubWard}
              onChange={(e) => {
                setSelectedSubWard(e.target.value)
                setSelectedLocality('ALL')
              }}
              className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl px-3 py-1.5 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              <option value="ALL">All Sub-Ward Beats ({availableSubWards.length})</option>
              {availableSubWards.map((sw) => (
                <option key={sw.id} value={sw.id}>
                  {sw.name} ({sw.id})
                </option>
              ))}
            </select>
          </div>

          {/* Locality Selector */}
          {availableLocalities.length > 0 && (
            <div className="shrink-0">
              <select
                value={selectedLocality}
                onChange={(e) => setSelectedLocality(e.target.value)}
                className="bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl px-3 py-1.5 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
              >
                <option value="ALL">All Localities ({availableLocalities.length})</option>
                {availableLocalities.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Reset Filters Shortcut */}
          {(selectedWard !== (isRestrictedInspector ? assignedWard : 'ALL') ||
            selectedSubWard !== 'ALL' ||
            selectedLocality !== 'ALL' ||
            selectedCategory !== 'ALL' ||
            selectedDepartment !== 'ALL' ||
            search) && (
            <button
              onClick={() => {
                if (!isRestrictedInspector) setSelectedWard('ALL')
                setSelectedSubWard('ALL')
                setSelectedLocality('ALL')
                setSelectedCategory('ALL')
                setSelectedDepartment('ALL')
                setSearch('')
              }}
              className="text-[#6457E8] hover:text-[#5145CF] font-medium text-xs ml-auto cursor-pointer flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Reset filters
            </button>
          )}
        </div>
      </div>

      {/* Action Queue Table */}
      <div className="bg-white border border-[#E4E7F1] rounded-2xl overflow-hidden shadow-xs flex-1 flex flex-col">
        <div className="px-5 py-3 bg-[#F0F2F9] border-b border-[#E4E7F1] flex items-center justify-between text-xs text-[#65708B]">
          <span>
            Displaying <strong className="text-[#11162A]">{filtered.length}</strong> of{' '}
            {scopedIssues.length} Complaints in Scope
          </span>
          <span className="text-[#6457E8] font-medium">Click any row or action button to open Issue Dossier</span>
        </div>

        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E4E7F1] bg-[#F6F7FC] text-xs font-semibold text-[#65708B]">
                <th className="py-3 px-4">Issue ID</th>
                <th className="py-3 px-4">Category & Details</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Geographical Routing</th>
                <th className="py-3 px-4">Assigned Team & Supervisor</th>
                <th className="py-3 px-4">Scheduled Date</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7F1]/70 text-xs">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-[#65708B] font-sans">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <ClipboardList className="w-8 h-8 text-slate-300" />
                      <div className="font-semibold text-[#11162A]">No complaints in this queue view</div>
                      <p className="text-xs text-[#65708B]">Try switching tabs or resetting the search/geographical filters.</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filtered.map((issue) => {
                  const isUnassigned = !issue.assignment || !issue.assignment.team_name
                  return (
                    <tr
                      key={issue.issueId}
                      onClick={() => onSelectIssue(issue)}
                      className="hover:bg-[#F0F2F9]/60 cursor-pointer transition group"
                    >
                      <td className="py-3.5 px-4 font-bold text-[#6457E8] font-mono whitespace-nowrap">
                        {issue.issueId}
                      </td>
                      <td className="py-3.5 px-4 font-sans text-[#11162A]">
                        <div className="font-semibold flex items-center gap-2">
                          <span>{issue.category}</span>
                          {issue.status === 'REOPENED' && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-bold">
                              REOPENED
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-[#65708B] truncate max-w-xs font-sans mt-0.5">
                          {issue.complaintText}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap text-[#11162A]">
                        <div className="font-medium flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-[#65708B] shrink-0" />
                          <span className="truncate max-w-[150px]">{issue.location}</span>
                        </div>
                        <div className="text-[11px] text-[#65708B] pl-4 flex items-center gap-1.5 flex-wrap mt-0.5">
                          <span className="font-semibold text-[#11162A]">{issue.authority_code || 'BMC'} &bull; {issue.ward || 'N-Ward'}</span>
                          {issue.sub_ward_name ? (
                            <>
                              <span>&bull;</span>
                              <span className="text-[#6457E8] font-medium">{issue.sub_ward_name}</span>
                            </>
                          ) : (
                            <>
                              <span>&bull;</span>
                              <span className="text-amber-600 italic">Pending Sub-Ward</span>
                            </>
                          )}
                          {issue.locality_name && (
                            <>
                              <span>&bull;</span>
                              <span className="text-[#10B981] font-medium">{issue.locality_name}</span>
                            </>
                          )}
                          {issue.jurisdiction_review_required && (
                            <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[10px] font-bold border border-amber-300">
                              Review Req
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {isUnassigned ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-amber-50 text-amber-700 font-medium border border-amber-200 text-xs">
                            <ClipboardList className="w-3 h-3 text-amber-600" />
                            Unassigned
                          </span>
                        ) : (
                          <div>
                            <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#6457E8]/10 text-[#6457E8] font-medium border border-[#6457E8]/20 text-xs">
                              <Wrench className="w-3 h-3 text-[#6457E8]" />
                              {issue.assignment?.team_name}
                            </div>
                            <div className="text-[11px] text-[#65708B] mt-0.5 flex flex-col">
                              <span>
                                Supervisor:{' '}
                                <strong className="text-[#11162A]">
                                  {issue.supervisor_name || 'Pending Allocation'}
                                </strong>
                              </span>
                              {issue.department && (
                                <span className="text-[10px] text-[#65708B]">{issue.department}</span>
                              )}
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap text-xs">
                        {issue.assignment?.scheduled_date ? (
                          <div className="flex items-center gap-1.5 text-[#11162A] font-medium">
                            <Calendar className="w-3.5 h-3.5 text-[#6457E8]" />
                            <span>{issue.assignment.scheduled_date}</span>
                          </div>
                        ) : (
                          <span className="text-[#65708B] italic">Not scheduled</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <StatusBadge status={issue.status} />
                      </td>
                      <td className="py-3.5 px-4 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => onSelectIssue(issue)}
                            className="px-3 py-1.5 rounded-lg bg-[#F0F2F9] hover:bg-[#6457E8] hover:text-white text-[#11162A] font-medium transition cursor-pointer flex items-center gap-1 text-xs"
                          >
                            <Eye className="w-3 h-3" />
                            <span>Open Dossier</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
