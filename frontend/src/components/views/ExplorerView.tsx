import React, { useState } from 'react'
import {
  Search,
  Filter,
  ListFilter,
  MapPin,
  Clock,
  ArrowUpDown,
  Building,
} from 'lucide-react'
import { Issue, IssueCategory, PriorityLevel, IssueStatus } from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { ConsistencyBadge } from '../common/ConsistencyBadge'

interface ExplorerViewProps {
  issues: Issue[]
  onSelectIssue: (issue: Issue) => void
}

export const ExplorerView: React.FC<ExplorerViewProps> = ({ issues, onSelectIssue }) => {
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL')
  const [selectedPriority, setSelectedPriority] = useState<string>('ALL')
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL')
  const [sortField, setSortField] = useState<'priority' | 'time'>('priority')

  const categories = [
    { label: 'ALL Categories', value: 'ALL' },
    { label: 'Roads & Footpaths (Core Focus 1)', value: 'Roads & Footpaths' },
    { label: 'Sanitation & Garbage (Core Focus 2)', value: 'Sanitation & Garbage' },
    { label: 'Water Supply & Drainage (Out of Scope)', value: 'Water Supply & Drainage' },
    { label: 'Street Lighting (Out of Scope)', value: 'Street Lighting' },
    { label: 'Storm Water Drains (Out of Scope)', value: 'Storm Water Drains' },
    { label: 'Traffic & Safety (Out of Scope)', value: 'Traffic & Safety' },
  ]

  const priorities = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
  const statuses = ['ALL', 'OPEN', 'ANALYZED', 'PRIORITIZED', 'ASSIGNED', 'ACTION IN PROGRESS', 'VERIFICATION', 'RESOLVED']

  const filtered = issues.filter((i) => {
    const matchSearch =
      i.issueId.toLowerCase().includes(search.toLowerCase()) ||
      i.complaintText.toLowerCase().includes(search.toLowerCase()) ||
      i.location.toLowerCase().includes(search.toLowerCase())
    const matchCat = selectedCategory === 'ALL' || i.category === selectedCategory
    const matchPri = selectedPriority === 'ALL' || i.priorityLevel === selectedPriority
    const matchStat = selectedStatus === 'ALL' || i.status === selectedStatus
    return matchSearch && matchCat && matchPri && matchStat
  })

  filtered.sort((a, b) => {
    if (sortField === 'priority') {
      return b.priorityScore - a.priorityScore
    }
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })

  return (
    <div className="h-full flex flex-col overflow-y-auto p-6 space-y-4 font-sans text-xs bg-[#F6F7FC]">
      {/* Search & Filter Bar */}
      <div className="bg-white border border-[#E4E7F1] rounded-2xl p-5 space-y-3.5 shadow-xs">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-[#65708B] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by keyword, issue ID, or landmark..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl pl-9 pr-3 py-2 text-xs text-[#11162A] placeholder-[#65708B] outline-none focus:border-[#6457E8] font-sans"
            />
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={() => setSortField(sortField === 'priority' ? 'time' : 'priority')}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[#F0F2F9] hover:bg-slate-200/70 border border-[#E4E7F1] text-[#11162A] rounded-xl text-xs font-medium cursor-pointer transition"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-[#6457E8]" />
              <span>Sort: {sortField === 'priority' ? 'Priority Score' : 'Timestamp'}</span>
            </button>
          </div>
        </div>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
          <div>
            <label className="text-xs font-semibold text-[#65708B] block mb-1">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              {categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#65708B] block mb-1">
              Priority Level
            </label>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              {priorities.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#65708B] block mb-1">
              Lifecycle Stage
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-[#F0F2F9] border border-[#E4E7F1] text-[#11162A] rounded-xl p-2 text-xs outline-none focus:border-[#6457E8] cursor-pointer"
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Issues Table */}
      <div className="bg-white border border-[#E4E7F1] rounded-2xl overflow-hidden shadow-xs flex-1 flex flex-col">
        <div className="px-5 py-3 bg-[#F0F2F9] border-b border-[#E4E7F1] flex items-center justify-between text-xs text-[#65708B]">
          <span>
            Displaying <strong className="text-[#11162A]">{filtered.length}</strong> of{' '}
            {issues.length} Registered Issues
          </span>
          <span className="text-[#6457E8] font-medium">Click row to inspect complete audit trace</span>
        </div>

        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E4E7F1] bg-[#F6F7FC] text-xs font-semibold text-[#65708B]">
                <th className="py-3 px-4">Issue ID</th>
                <th className="py-3 px-4">Category</th>
                <th className="py-3 px-4">Priority</th>
                <th className="py-3 px-4">Location & Ward</th>
                <th className="py-3 px-4">Assigned Department</th>
                <th className="py-3 px-4">Evidence</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E4E7F1]/70 text-xs">
              {filtered.map((issue) => (
                <tr
                  key={issue.issueId}
                  onClick={() => onSelectIssue(issue)}
                  className="hover:bg-[#F0F2F9]/60 cursor-pointer transition"
                >
                  <td className="py-3.5 px-4 font-bold text-[#6457E8] font-mono whitespace-nowrap">
                    {issue.issueId}
                  </td>
                  <td className="py-3.5 px-4 font-sans text-[#11162A]">
                    <div className="font-semibold">{issue.category}</div>
                    <div className="text-xs text-[#65708B] truncate max-w-xs font-sans">
                      {issue.complaintText}
                    </div>
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap text-[#11162A]">
                    <div className="font-medium">{issue.location}</div>
                    <div className="text-xs text-[#65708B]">{issue.ward}</div>
                  </td>
                  <td className="py-3.5 px-4 text-[#11162A] text-xs">
                    <div className="truncate max-w-[180px] font-medium">{issue.department}</div>
                    <div className="text-xs text-emerald-700 font-mono">SLA: {issue.slaHours}h</div>
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                  </td>
                  <td className="py-3.5 px-4 whitespace-nowrap">
                    <StatusBadge status={issue.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
