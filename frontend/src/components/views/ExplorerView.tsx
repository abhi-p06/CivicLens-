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
    'ALL',
    'Roads & Footpaths',
    'Sanitation & Garbage',
    'Water Supply & Drainage',
    'Street Lighting',
    'Storm Water Drains',
    'Traffic & Safety',
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
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-4 font-mono text-xs">
      {/* Search & Filter Bar */}
      <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 space-y-3 shadow-xl">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Filter by keyword, issue ID, or landmark..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700/80 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 outline-none focus:border-cyan-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 self-end sm:self-auto">
            <button
              onClick={() => setSortField(sortField === 'priority' ? 'time' : 'priority')}
              className="flex items-center gap-1.5 px-3 py-2 bg-[#121824] hover:bg-[#162030] border border-slate-700 text-slate-300 rounded-lg text-xs"
            >
              <ArrowUpDown className="w-3.5 h-3.5 text-cyan-400" />
              <span>Sort: {sortField === 'priority' ? 'Priority Score' : 'Timestamp'}</span>
            </button>
          </div>
        </div>

        {/* Filter Dropdowns */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
          <div>
            <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700 text-slate-300 rounded p-1.5 text-xs outline-none focus:border-cyan-500"
            >
              {categories.map((c) => (
                <option key={c} value={c} className="bg-[#0e131d]">
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
              Priority Level
            </label>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700 text-slate-300 rounded p-1.5 text-xs outline-none focus:border-cyan-500"
            >
              {priorities.map((p) => (
                <option key={p} value={p} className="bg-[#0e131d]">
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
              Lifecycle Stage
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700 text-slate-300 rounded p-1.5 text-xs outline-none focus:border-cyan-500"
            >
              {statuses.map((s) => (
                <option key={s} value={s} className="bg-[#0e131d]">
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Issues Table */}
      <div className="bg-[#0e131d] border border-slate-800 rounded-xl overflow-hidden shadow-xl flex-1 flex flex-col">
        <div className="px-4 py-2.5 bg-[#121824] border-b border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
          <span>
            Displaying <strong className="text-slate-100">{filtered.length}</strong> of{' '}
            {issues.length} Registered Issues
          </span>
          <span className="text-cyan-400">Click row to inspect complete audit trace</span>
        </div>

        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0a0d14] text-[10px] uppercase tracking-wider text-slate-400">
                <th className="py-2.5 px-3">Issue ID</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3">Priority</th>
                <th className="py-2.5 px-3">Location & Ward</th>
                <th className="py-2.5 px-3">Assigned Department</th>
                <th className="py-2.5 px-3">Evidence</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-xs">
              {filtered.map((issue) => (
                <tr
                  key={issue.issueId}
                  onClick={() => onSelectIssue(issue)}
                  className="hover:bg-[#131926] cursor-pointer transition"
                >
                  <td className="py-3 px-3 font-bold text-cyan-400 whitespace-nowrap">
                    {issue.issueId}
                  </td>
                  <td className="py-3 px-3 font-sans text-slate-200">
                    <div className="font-semibold">{issue.category}</div>
                    <div className="text-[10px] text-slate-400 truncate max-w-xs font-sans">
                      {issue.complaintText}
                    </div>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <PriorityGauge score={issue.priorityScore} level={issue.priorityLevel} compact />
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap text-slate-300">
                    <div>{issue.location}</div>
                    <div className="text-[10px] text-slate-500">{issue.ward}</div>
                  </td>
                  <td className="py-3 px-3 text-slate-300 text-[11px]">
                    <div className="truncate max-w-[180px]">{issue.department}</div>
                    <div className="text-[10px] text-emerald-400 font-mono">SLA: {issue.slaHours}h</div>
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
                    <ConsistencyBadge level={issue.consistencyFlag || 'CONSISTENT'} />
                  </td>
                  <td className="py-3 px-3 whitespace-nowrap">
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
