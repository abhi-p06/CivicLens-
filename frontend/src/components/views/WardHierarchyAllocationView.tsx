import React, { useState, useEffect, useMemo, useRef } from 'react'
import L from 'leaflet'
import {
  Network,
  ChevronRight,
  ChevronDown,
  Building2,
  MapPin,
  Users,
  Shield,
  Layers,
  Search,
  Plus,
  Edit2,
  Trash2,
  UserCheck,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  FolderOpen,
  Info,
  Calendar,
  Wrench,
  ArrowRight,
  X,
  ExternalLink,
} from 'lucide-react'
import { api } from '../../services/api'
import {
  HierarchyTreeNode,
  MunicipalAuthority,
  AdminWard,
  SubWard,
  LocalityBeat,
  Issue,
} from '../../types'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { cn } from '../../lib/utils'

interface WardHierarchyAllocationViewProps {
  onSelectIssue?: (issue: Issue) => void
}

export const WardHierarchyAllocationView: React.FC<WardHierarchyAllocationViewProps> = ({
  onSelectIssue,
}) => {
  const [treeData, setTreeData] = useState<HierarchyTreeNode[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedNode, setSelectedNode] = useState<HierarchyTreeNode | null>(null)
  const [expandedNodeIds, setExpandedNodeIds] = useState<Set<string>>(new Set())

  // Issues under the selected node
  const [nodeIssues, setNodeIssues] = useState<Issue[]>([])
  const [loadingIssues, setLoadingIssues] = useState<boolean>(false)

  // Sub-ward Modal (Add/Edit)
  const [subWardModalOpen, setSubWardModalOpen] = useState<boolean>(false)
  const [editingSubWard, setEditingSubWard] = useState<SubWard | null>(null)
  const [parentWardForNew, setParentWardForNew] = useState<string>('')
  const [subWardForm, setSubWardForm] = useState({
    code: '',
    name: '',
    ward_id: '',
    center_lat: 19.0760,
    center_lng: 72.8850,
    supervisor_name: '',
    assigned_department: 'Road Maintenance & Infrastructure',
  })
  const [savingSubWard, setSavingSubWard] = useState<boolean>(false)

  // Supervisor Assignment Modal
  const [supervisorModalOpen, setSupervisorModalOpen] = useState<boolean>(false)
  const [supervisorForm, setSupervisorForm] = useState({
    user_id: '',
    ward_id: '',
    sub_ward_id: '',
    role_title: 'Sub-Ward Operations Lead',
  })
  const [savingSupervisor, setSavingSupervisor] = useState<boolean>(false)

  // Map Preview
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const geojsonLayerRef = useRef<L.GeoJSON | null>(null)

  // Load Tree Data
  const loadTree = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.hierarchy.getTree()
      setTreeData(data)

      // Default expand top authorities
      const initialExpanded = new Set<string>()
      data.forEach((auth) => {
        initialExpanded.add(auth.id)
        // Expand first zone and ward by default
        if (auth.children && auth.children.length > 0) {
          auth.children.forEach((child) => {
            initialExpanded.add(child.id)
            if (child.children && child.children.length > 0) {
              child.children.slice(0, 2).forEach((gc) => initialExpanded.add(gc.id))
            }
          })
        }
      })
      setExpandedNodeIds(initialExpanded)

      // Select first ward or authority if none selected
      if (!selectedNode && data.length > 0) {
        setSelectedNode(data[0])
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load administrative hierarchy tree')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTree()
  }, [])

  // Load issues when selectedNode changes
  useEffect(() => {
    if (!selectedNode) return

    const fetchNodeIssues = async () => {
      try {
        setLoadingIssues(true)
        const allIssues = await api.getIssues()

        // Filter based on selected node level
        let filtered: Issue[] = []
        if (selectedNode.level === 'authority') {
          filtered = allIssues.filter((i) => i.authority_id === selectedNode.id || i.authority_code === selectedNode.code)
        } else if (selectedNode.level === 'ward') {
          filtered = allIssues.filter(
            (i) => i.ward_id === selectedNode.id || i.ward === selectedNode.name || i.ward === selectedNode.code
          )
        } else if (selectedNode.level === 'sub_ward') {
          filtered = allIssues.filter((i) => i.sub_ward_id === selectedNode.id)
        } else if (selectedNode.level === 'locality') {
          filtered = allIssues.filter((i) => i.locality_id === selectedNode.id)
        } else {
          filtered = allIssues
        }
        setNodeIssues(filtered)
      } catch (e) {
        console.error('Error fetching node issues:', e)
      } finally {
        setLoadingIssues(false)
      }
    }

    fetchNodeIssues()
  }, [selectedNode])

  // Mini Boundary Preview Map
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [19.0760, 72.8850],
        zoom: 11,
        zoomControl: false,
        attributionControl: false,
      })

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16 }
      ).addTo(map)

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16, opacity: 0.8 }
      ).addTo(map)

      mapInstanceRef.current = map
    }

    const map = mapInstanceRef.current
    if (!map) return

    // Render boundary if available on selectedNode
    if (geojsonLayerRef.current) {
      geojsonLayerRef.current.remove()
      geojsonLayerRef.current = null
    }

    if (selectedNode?.boundary_geojson) {
      try {
        const geoLayer = L.geoJSON(selectedNode.boundary_geojson as any, {
          style: {
            color: selectedNode.level === 'sub_ward' ? '#6457E8' : '#8B5CF6',
            weight: 2,
            dashArray: selectedNode.level === 'sub_ward' ? '4, 4' : undefined,
            fillColor: selectedNode.level === 'sub_ward' ? '#6457E8' : '#8B5CF6',
            fillOpacity: 0.15,
          },
        }).addTo(map)

        geojsonLayerRef.current = geoLayer
        const bounds = geoLayer.getBounds()
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [20, 20], maxZoom: 14 })
        }
      } catch (err) {
        console.warn('Could not render geojson on preview map:', err)
      }
    }
  }, [selectedNode])

  // Expand / Collapse Handlers
  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setExpandedNodeIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const expandAll = () => {
    const allIds = new Set<string>()
    const traverse = (nodes: HierarchyTreeNode[]) => {
      nodes.forEach((n) => {
        allIds.add(n.id)
        if (n.children && n.children.length > 0) traverse(n.children)
      })
    }
    traverse(treeData)
    setExpandedNodeIds(allIds)
  }

  const collapseAll = () => {
    setExpandedNodeIds(new Set())
  }

  // Filter tree nodes recursively by search query
  const filteredTree = useMemo(() => {
    if (!searchQuery.trim()) return treeData
    const q = searchQuery.toLowerCase()

    const filterNode = (node: HierarchyTreeNode): HierarchyTreeNode | null => {
      const matches =
        node.name.toLowerCase().includes(q) ||
        node.code.toLowerCase().includes(q) ||
        (node.supervisor && node.supervisor.toLowerCase().includes(q)) ||
        (node.department && node.department.toLowerCase().includes(q))

      let filteredChildren: HierarchyTreeNode[] = []
      if (node.children && node.children.length > 0) {
        filteredChildren = node.children
          .map((c) => filterNode(c))
          .filter((c): c is HierarchyTreeNode => c !== null)
      }

      if (matches || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren,
        }
      }
      return null
    }

    return treeData
      .map((node) => filterNode(node))
      .filter((n): n is HierarchyTreeNode => n !== null)
  }, [treeData, searchQuery])

  // Sub-Ward Add/Edit Action
  const handleOpenAddSubWard = (parentWardId: string) => {
    setEditingSubWard(null)
    setParentWardForNew(parentWardId)
    setSubWardForm({
      code: '',
      name: '',
      ward_id: parentWardId,
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: '',
      assigned_department: 'Road Maintenance & Infrastructure',
    })
    setSubWardModalOpen(true)
  }

  const handleOpenEditSubWard = (node: HierarchyTreeNode) => {
    setEditingSubWard({
      id: node.id,
      ward_id: node.parent_id || '',
      code: node.code,
      name: node.name,
      is_official: false,
      operational_type: 'CIVILENS_OPERATIONAL_SUB_WARD',
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: node.supervisor,
      assigned_department: node.department,
      is_active: true,
    })
    setParentWardForNew(node.parent_id || '')
    setSubWardForm({
      code: node.code,
      name: node.name,
      ward_id: node.parent_id || '',
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: node.supervisor || '',
      assigned_department: node.department || 'Road Maintenance & Infrastructure',
    })
    setSubWardModalOpen(true)
  }

  const handleSaveSubWard = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSavingSubWard(true)
      if (editingSubWard) {
        await api.hierarchy.updateSubWard(editingSubWard.id, {
          name: subWardForm.name,
          code: subWardForm.code,
          supervisor_name: subWardForm.supervisor_name,
          assigned_department: subWardForm.assigned_department,
        })
      } else {
        await api.hierarchy.createSubWard({
          ward_id: subWardForm.ward_id,
          code: subWardForm.code,
          name: subWardForm.name,
          center_lat: Number(subWardForm.center_lat),
          center_lng: Number(subWardForm.center_lng),
          supervisor_name: subWardForm.supervisor_name,
          assigned_department: subWardForm.assigned_department,
        })
      }
      setSubWardModalOpen(false)
      await loadTree()
    } catch (err: any) {
      alert(err?.message || 'Failed to save operational sub-ward')
    } finally {
      setSavingSubWard(false)
    }
  }

  const handleDeleteSubWard = async (subWardId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete or deactivate sub-ward "${name}"?`)) return
    try {
      await api.hierarchy.deleteSubWard(subWardId)
      await loadTree()
      if (selectedNode?.id === subWardId) {
        setSelectedNode(null)
      }
    } catch (err: any) {
      alert(err?.message || 'Failed to delete sub-ward')
    }
  }

  // Supervisor Assignment
  const handleOpenAssignSupervisor = (node: HierarchyTreeNode) => {
    setSupervisorForm({
      user_id: '',
      ward_id: node.level === 'ward' ? node.id : '',
      sub_ward_id: node.level === 'sub_ward' ? node.id : '',
      role_title: node.level === 'sub_ward' ? 'Sub-Ward Operations Lead' : 'Ward Nodal Officer',
    })
    setSupervisorModalOpen(true)
  }

  const handleSaveSupervisor = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSavingSupervisor(true)
      await api.hierarchy.assignSupervisor({
        user_id: supervisorForm.user_id,
        ward_id: supervisorForm.ward_id || undefined,
        sub_ward_id: supervisorForm.sub_ward_id || undefined,
        role_title: supervisorForm.role_title,
      })
      setSupervisorModalOpen(false)
      await loadTree()
    } catch (err: any) {
      alert(err?.message || 'Failed to assign supervisor')
    } finally {
      setSavingSupervisor(false)
    }
  }

  // Recursive Tree Node Renderer
  const renderTreeNode = (node: HierarchyTreeNode, depth = 0) => {
    const isExpanded = expandedNodeIds.has(node.id)
    const isSelected = selectedNode?.id === node.id
    const hasChildren = node.children && node.children.length > 0

    // Level Badge Colors
    const getLevelBadge = () => {
      switch (node.level) {
        case 'authority':
          return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#13152E] text-white">Authority</span>
        case 'zone':
          return <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#8B5CF6]/15 text-[#6457E8]">Zone</span>
        case 'ward':
          return <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">Admin Ward</span>
        case 'sub_ward':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-800 border border-blue-200">
              CIVILENS Sub-Ward
            </span>
          )
        case 'locality':
          return <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">Locality Beat</span>
        default:
          return null
      }
    }

    return (
      <div key={node.id} className="select-none">
        <div
          onClick={() => setSelectedNode(node)}
          style={{ paddingLeft: `${depth * 18 + 8}px` }}
          className={cn(
            'flex items-center justify-between py-2 pr-3 rounded-xl cursor-pointer text-xs transition border group',
            isSelected
              ? 'bg-[#6457E8]/10 border-[#6457E8]/30 font-medium text-[#11162A]'
              : 'border-transparent hover:bg-black/[0.03] text-[#11162A]'
          )}
        >
          <div className="flex items-center gap-2 min-w-0">
            {hasChildren ? (
              <button
                onClick={(e) => toggleExpand(node.id, e)}
                className="w-5 h-5 flex items-center justify-center rounded-md hover:bg-black/5 text-[#65708B]"
              >
                {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
            ) : (
              <span className="w-5" />
            )}

            <div className="flex items-center gap-2 truncate">
              {getLevelBadge()}
              <span className="font-semibold text-xs text-[#11162A] truncate">{node.name}</span>
              <span className="text-[11px] font-mono text-[#65708B]">({node.code})</span>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Workload Indicator Pill */}
            <div className="flex items-center gap-2 text-[11px]">
              <span
                className={cn(
                  'px-2 py-0.5 rounded-full font-mono font-medium',
                  node.total_complaints > 0
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : 'bg-slate-100 text-slate-500'
                )}
                title="Total active complaints in this jurisdiction"
              >
                {node.total_complaints} issues
              </span>

              {node.unassigned_complaints > 0 && (
                <span
                  className="px-1.5 py-0.5 rounded-full text-[10px] bg-amber-50 text-amber-700 border border-amber-200 font-semibold"
                  title="Unassigned complaints requiring allocation"
                >
                  {node.unassigned_complaints} unassigned
                </span>
              )}
            </div>

            {/* Quick Actions (Admin Only) */}
            <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition">
              {node.level === 'ward' && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handleOpenAddSubWard(node.id)
                  }}
                  className="p-1 rounded hover:bg-[#6457E8]/15 text-[#6457E8]"
                  title="Add CIVILENS Operational Sub-Ward"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              )}
              {node.level === 'sub_ward' && (
                <>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleOpenEditSubWard(node)
                    }}
                    className="p-1 rounded hover:bg-slate-200 text-slate-600"
                    title="Edit Operational Sub-Ward"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteSubWard(node.id, node.name)
                    }}
                    className="p-1 rounded hover:bg-rose-100 text-rose-600"
                    title="Delete Operational Sub-Ward"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Children Render */}
        {hasChildren && isExpanded && (
          <div className="mt-0.5 space-y-0.5">
            {node.children.map((child) => renderTreeNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 1. Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-xl bg-[#13152E] flex items-center justify-center text-white shadow-xs">
              <Network className="w-5 h-5 text-[#8B5CF6]" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[#11162A] tracking-tight">
                Ward Hierarchy & Crew Allocation
              </h1>
              <p className="text-xs text-[#65708B]">
                Hierarchical geographic governance across BMC & NMMC municipal authorities down to operational service beats
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={expandAll}
            className="px-3 py-1.5 text-xs font-semibold bg-white border border-[#E4E7F1] rounded-lg text-[#11162A] hover:bg-slate-50 transition cursor-pointer"
          >
            Expand All
          </button>
          <button
            onClick={collapseAll}
            className="px-3 py-1.5 text-xs font-semibold bg-white border border-[#E4E7F1] rounded-lg text-[#11162A] hover:bg-slate-50 transition cursor-pointer"
          >
            Collapse All
          </button>
          <button
            onClick={loadTree}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#6457E8] text-white rounded-lg hover:bg-[#5145CF] transition shadow-xs cursor-pointer"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', loading && 'animate-spin')} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 2. Authority Separation Notice Strip */}
      <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs flex items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-bold text-xs">
            BMC
          </div>
          <div>
            <div className="font-semibold text-[#11162A]">Brihanmumbai Municipal Corporation</div>
            <div className="text-[11px] text-[#65708B]">24 Official Administrative Wards • 7 Administrative Zones</div>
          </div>
        </div>

        <div className="h-6 w-px bg-[#E4E7F1]" />

        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-700 border border-blue-200 flex items-center justify-center font-bold text-xs">
            NMMC
          </div>
          <div>
            <div className="font-semibold text-[#11162A]">Navi Mumbai Municipal Corporation</div>
            <div className="text-[11px] text-[#65708B]">8 Official Administrative Wards • 2 Administrative Zones</div>
          </div>
        </div>

        <div className="h-6 w-px bg-[#E4E7F1]" />

        <div className="flex items-center gap-2 text-[11px] text-[#65708B]">
          <Info className="w-4 h-4 text-[#6457E8]" />
          <span>Strict separation enforced: BMC & NMMC do not share ward codes or routing pipelines.</span>
        </div>
      </div>

      {/* 3. Main Split View: Tree Navigation (45%) & Detail Inspector (55%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Collapsible Tree (5 cols) */}
        <div className="lg:col-span-5 bg-white border border-[#E4E7F1] rounded-2xl p-4 shadow-xs flex flex-col h-[750px]">
          <div className="mb-3 space-y-2 shrink-0">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-[#11162A] flex items-center gap-2">
                <Layers className="w-4 h-4 text-[#6457E8]" />
                <span>Geographic Hierarchy</span>
              </h2>
              <span className="text-[11px] text-[#65708B] font-mono">
                {treeData.length} Authorities
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#65708B] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search authority, ward, sub-ward, beat..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] placeholder-[#65708B] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
              />
            </div>
          </div>

          {/* Tree Scroll Container */}
          <div className="flex-1 overflow-y-auto pr-1 space-y-0.5">
            {loading ? (
              <div className="flex flex-col items-center justify-center h-48 text-[#65708B] text-xs gap-2">
                <RefreshCw className="w-5 h-5 animate-spin text-[#6457E8]" />
                <span>Loading administrative tree...</span>
              </div>
            ) : filteredTree.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#65708B]">
                No administrative entities match "{searchQuery}"
              </div>
            ) : (
              filteredTree.map((rootNode) => renderTreeNode(rootNode, 0))
            )}
          </div>
        </div>

        {/* Right Column: Jurisdiction Node Inspector (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {selectedNode ? (
            <>
              {/* Selected Node Summary Card */}
              <div className="bg-white border border-[#E4E7F1] rounded-2xl p-5 shadow-xs space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold text-[#11162A]">{selectedNode.name}</span>
                      <span className="px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-[#13152E] text-white">
                        {selectedNode.code}
                      </span>
                      {selectedNode.is_official ? (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          Official Municipal Entity
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-50 text-blue-800 border border-blue-200">
                          CIVILENS Operational Service Area
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-[#65708B] mt-1 flex items-center gap-3">
                      <span>Level: <strong className="text-[#11162A] capitalize">{selectedNode.level.replace('_', ' ')}</strong></span>
                      {selectedNode.parent_id && <span>Parent ID: <code className="font-mono">{selectedNode.parent_id}</code></span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {(selectedNode.level === 'ward' || selectedNode.level === 'sub_ward') && (
                      <button
                        onClick={() => handleOpenAssignSupervisor(selectedNode)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#F0F2F9] text-[#11162A] border border-[#E4E7F1] rounded-xl hover:bg-slate-200 transition cursor-pointer"
                      >
                        <UserCheck className="w-3.5 h-3.5 text-[#6457E8]" />
                        <span>Assign Supervisor</span>
                      </button>
                    )}
                    {selectedNode.level === 'ward' && (
                      <button
                        onClick={() => handleOpenAddSubWard(selectedNode.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#6457E8] text-white rounded-xl hover:bg-[#5145CF] transition shadow-xs cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>New Sub-Ward</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Workload Metrics Strip (From actual database records) */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-[#E4E7F1]">
                  <div className="p-3 bg-[#F6F7FC] rounded-xl">
                    <div className="text-[10px] font-semibold text-[#65708B] uppercase">Total Complaints</div>
                    <div className="text-lg font-bold text-[#11162A] mt-0.5 font-mono">{selectedNode.total_complaints}</div>
                  </div>
                  <div className="p-3 bg-amber-50/70 border border-amber-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-amber-800 uppercase">Unassigned</div>
                    <div className="text-lg font-bold text-amber-900 mt-0.5 font-mono">{selectedNode.unassigned_complaints}</div>
                  </div>
                  <div className="p-3 bg-blue-50/70 border border-blue-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-blue-800 uppercase">Assigned</div>
                    <div className="text-lg font-bold text-blue-900 mt-0.5 font-mono">{selectedNode.assigned_complaints}</div>
                  </div>
                  <div className="p-3 bg-purple-50/70 border border-purple-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-purple-800 uppercase">In Progress</div>
                    <div className="text-lg font-bold text-purple-900 mt-0.5 font-mono">{selectedNode.in_progress_tasks}</div>
                  </div>
                  <div className="p-3 bg-emerald-50/70 border border-emerald-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-emerald-800 uppercase">Completed</div>
                    <div className="text-lg font-bold text-emerald-900 mt-0.5 font-mono">{selectedNode.completed_complaints}</div>
                  </div>
                </div>

                {/* Officers, Department & Crew Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                  <div className="p-3 bg-white border border-[#E4E7F1] rounded-xl flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#6457E8]/10 text-[#6457E8] flex items-center justify-center shrink-0">
                      <Users className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[11px] text-[#65708B]">Responsible Supervisor</div>
                      <div className="font-semibold text-[#11162A]">
                        {selectedNode.supervisor || 'Unassigned (Ward Pool)'}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-white border border-[#E4E7F1] rounded-xl flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                      <Wrench className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[11px] text-[#65708B]">Assigned Department / Field Crews</div>
                      <div className="font-semibold text-[#11162A]">
                        {selectedNode.department || 'Multi-Department Service Area'} • {selectedNode.available_crews} Active Crews
                      </div>
                    </div>
                  </div>
                </div>

                {/* Geographic Boundary Preview Map */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-[#11162A] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#6457E8]" />
                      <span>Boundary Polygon & Service Beat Map</span>
                    </span>
                    <span className="text-[11px] text-[#65708B]">
                      {selectedNode.boundary_geojson ? 'Spatial Polygon Loaded' : 'Bounding Coordinates Only'}
                    </span>
                  </div>
                  <div className="h-44 w-full rounded-xl overflow-hidden border border-[#E4E7F1] relative">
                    <div ref={mapContainerRef} className="h-full w-full" />
                  </div>
                </div>
              </div>

              {/* Complaints Table under Selected Node */}
              <div className="bg-white border border-[#E4E7F1] rounded-2xl p-5 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-[#11162A] flex items-center gap-2">
                      <FolderOpen className="w-4 h-4 text-[#6457E8]" />
                      <span>Jurisdiction Complaint Queue</span>
                    </h3>
                    <p className="text-[11px] text-[#65708B]">
                      Complaints assigned to {selectedNode.name} ({nodeIssues.length} records)
                    </p>
                  </div>
                </div>

                {loadingIssues ? (
                  <div className="py-12 flex flex-col items-center justify-center text-xs text-[#65708B] gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-[#6457E8]" />
                    <span>Loading complaints for {selectedNode.name}...</span>
                  </div>
                ) : nodeIssues.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#65708B] bg-[#F6F7FC] rounded-xl border border-dashed border-[#E4E7F1]">
                    No active complaints currently routed under this administrative branch.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#E4E7F1] text-[#65708B] text-[11px]">
                          <th className="pb-2 font-semibold">ID</th>
                          <th className="pb-2 font-semibold">Category</th>
                          <th className="pb-2 font-semibold">Status</th>
                          <th className="pb-2 font-semibold">Priority</th>
                          <th className="pb-2 font-semibold">Sub-Ward / Locality</th>
                          <th className="pb-2 font-semibold">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#E4E7F1]">
                        {nodeIssues.slice(0, 10).map((issue) => (
                          <tr key={issue.issueId} className="hover:bg-[#F6F7FC] transition">
                            <td className="py-2.5 font-mono font-bold text-[#11162A]">{issue.issueId}</td>
                            <td className="py-2.5 text-[#11162A]">{issue.category}</td>
                            <td className="py-2.5">
                              <StatusBadge status={issue.status} />
                            </td>
                            <td className="py-2.5">
                              <span className="font-semibold text-rose-600 font-mono">
                                {issue.priorityScore.toFixed(1)}
                              </span>
                            </td>
                            <td className="py-2.5 text-[#65708B]">
                              {issue.sub_ward_name || issue.ward || 'Pending'}
                            </td>
                            <td className="py-2.5">
                              {onSelectIssue && (
                                <button
                                  onClick={() => onSelectIssue(issue)}
                                  className="px-2 py-1 bg-slate-100 hover:bg-[#6457E8] hover:text-white rounded text-[11px] font-semibold text-[#11162A] transition cursor-pointer"
                                >
                                  Inspect
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {nodeIssues.length > 10 && (
                      <div className="text-[11px] text-center text-[#65708B] pt-2">
                        Showing first 10 of {nodeIssues.length} complaints. Open Action Queue for full view.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white border border-[#E4E7F1] rounded-2xl p-12 text-center text-[#65708B] text-xs">
              Select an authority, administrative ward, or operational sub-ward from the tree to inspect details.
            </div>
          )}
        </div>
      </div>

      {/* Modal: Add / Edit CIVILENS Operational Sub-Ward */}
      {subWardModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9000]">
          <div className="bg-white border border-[#E4E7F1] rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#6457E8]" />
                <h3 className="text-base font-bold text-[#11162A]">
                  {editingSubWard ? 'Edit CIVILENS Operational Sub-Ward' : 'Add CIVILENS Operational Sub-Ward'}
                </h3>
              </div>
              <button
                onClick={() => setSubWardModalOpen(false)}
                className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2">
              <Info className="w-4 h-4 shrink-0 text-blue-600 mt-0.5" />
              <span>
                <strong>Operational Sub-Ward Notice:</strong> This operational service beat will be explicitly designated as <code>CIVILENS_OPERATIONAL_SUB_WARD</code> and not falsely labeled as an official municipal division.
              </span>
            </div>

            <form onSubmit={handleSaveSubWard} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Sub-Ward Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. N-04"
                    value={subWardForm.code}
                    onChange={(e) => setSubWardForm({ ...subWardForm, code: e.target.value })}
                    className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] font-mono focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Sub-Ward Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ghatkopar Industrial Zone"
                    value={subWardForm.name}
                    onChange={(e) => setSubWardForm({ ...subWardForm, name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Center Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={subWardForm.center_lat}
                    onChange={(e) => setSubWardForm({ ...subWardForm, center_lat: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] font-mono focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Center Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    value={subWardForm.center_lng}
                    onChange={(e) => setSubWardForm({ ...subWardForm, center_lng: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] font-mono focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Responsible Supervisor</label>
                <input
                  type="text"
                  placeholder="e.g. Inspector R. Deshmukh"
                  value={subWardForm.supervisor_name}
                  onChange={(e) => setSubWardForm({ ...subWardForm, supervisor_name: e.target.value })}
                  className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Responsible Department</label>
                <select
                  value={subWardForm.assigned_department}
                  onChange={(e) => setSubWardForm({ ...subWardForm, assigned_department: e.target.value })}
                  className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                >
                  <option value="Road Maintenance & Infrastructure">Road Maintenance & Infrastructure</option>
                  <option value="Solid Waste Management & Sanitation">Solid Waste Management & Sanitation</option>
                  <option value="Hydraulic & Storm Water Drainage">Hydraulic & Storm Water Drainage</option>
                  <option value="Traffic & Street Furniture">Traffic & Street Furniture</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#E4E7F1]">
                <button
                  type="button"
                  onClick={() => setSubWardModalOpen(false)}
                  className="px-4 py-2 border border-[#E4E7F1] text-[#11162A] rounded-xl hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSubWard}
                  className="px-4 py-2 bg-[#6457E8] text-white rounded-xl hover:bg-[#5145CF] font-semibold flex items-center gap-1.5 shadow-xs"
                >
                  {savingSubWard && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Operational Sub-Ward</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Assign Supervisor */}
      {supervisorModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9000]">
          <div className="bg-white border border-[#E4E7F1] rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
              <div className="flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-[#6457E8]" />
                <h3 className="text-base font-bold text-[#11162A]">Assign Supervisor</h3>
              </div>
              <button
                onClick={() => setSupervisorModalOpen(false)}
                className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSaveSupervisor} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Supervisor Officer ID or Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. officer_n_ward or Inspector Rajesh"
                  value={supervisorForm.user_id}
                  onChange={(e) => setSupervisorForm({ ...supervisorForm, user_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                />
              </div>

              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Role Designation</label>
                <input
                  type="text"
                  required
                  value={supervisorForm.role_title}
                  onChange={(e) => setSupervisorForm({ ...supervisorForm, role_title: e.target.value })}
                  className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#E4E7F1]">
                <button
                  type="button"
                  onClick={() => setSupervisorModalOpen(false)}
                  className="px-4 py-2 border border-[#E4E7F1] text-[#11162A] rounded-xl hover:bg-slate-50 font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSupervisor}
                  className="px-4 py-2 bg-[#6457E8] text-white rounded-xl hover:bg-[#5145CF] font-semibold flex items-center gap-1.5 shadow-xs"
                >
                  {savingSupervisor && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Confirm Allocation</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

