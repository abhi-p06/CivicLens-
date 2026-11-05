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
  Filter,
  Upload,
  PenTool,
  RotateCcw,
  Check,
  Lock,
  Eye,
  Sliders,
} from 'lucide-react'
import { api } from '../../services/api'
import {
  HierarchyTreeNode,
  MunicipalAuthority,
  AdminWard,
  SubWard,
  LocalityBeat,
  Issue,
  FieldTeam,
} from '../../types'
import { useAuth } from '../../context/AuthContext'
import { StatusBadge } from '../common/StatusBadge'
import { PriorityGauge } from '../common/PriorityGauge'
import { cn } from '../../lib/utils'

interface WardHierarchyAllocationViewProps {
  onSelectIssue?: (issue: Issue) => void
}

export const WardHierarchyAllocationView: React.FC<WardHierarchyAllocationViewProps> = ({
  onSelectIssue,
}) => {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isInspector = user?.role === 'inspector'
  const isCitizen = user?.role === 'citizen'

  const [rawAuthorities, setRawAuthorities] = useState<HierarchyTreeNode[]>([])
  const [treeData, setTreeData] = useState<HierarchyTreeNode[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [selectedNode, setSelectedNode] = useState<HierarchyTreeNode | null>(null)
  const [expandedNodeIds, setExpandedNodeIds] = useState<Set<string>>(new Set())

  // Issues under the selected node
  const [nodeIssues, setNodeIssues] = useState<Issue[]>([])
  const [loadingIssues, setLoadingIssues] = useState<boolean>(false)
  const [filterCategory, setFilterCategory] = useState<string>('ALL')
  const [filterStatus, setFilterStatus] = useState<string>('ALL')

  // Available Teams (for Team Configuration)
  const [allTeams, setAllTeams] = useState<FieldTeam[]>([])
  const [loadingTeams, setLoadingTeams] = useState<boolean>(false)
  const [teamModalOpen, setTeamModalOpen] = useState<boolean>(false)
  const [assignExistingTeamId, setAssignExistingTeamId] = useState<string>('')
  const [newTeamForm, setNewTeamForm] = useState({
    name: '',
    department: 'Road Infrastructure Maintenance',
    category: 'Roads & Footpaths',
    capacity: 6,
    contact_lead: 'Duty Supervisor',
  })
  const [savingTeam, setSavingTeam] = useState<boolean>(false)

  // Sub-ward Modal (Add/Edit)
  const [subWardModalOpen, setSubWardModalOpen] = useState<boolean>(false)
  const [editingSubWard, setEditingSubWard] = useState<SubWard | null>(null)
  const [parentWardForNew, setParentWardForNew] = useState<string>('')
  const [allWardsList, setAllWardsList] = useState<{ id: string; name: string; code: string; auth: string }[]>([])
  const [subWardForm, setSubWardForm] = useState({
    code: '',
    name: '',
    ward_id: '',
    center_lat: 19.0760,
    center_lng: 72.8850,
    supervisor_name: '',
    assigned_department: 'Road Infrastructure Maintenance',
    is_active: true,
    boundary_geojson: null as Record<string, any> | null,
  })
  const [savingSubWard, setSavingSubWard] = useState<boolean>(false)

  // Interactive Polygon Drawing in Sub-Ward Modal
  const [isDrawingPolygon, setIsDrawingPolygon] = useState<boolean>(false)
  const [drawnPoints, setDrawnPoints] = useState<[number, number][]>([])
  const [geoJsonInputText, setGeoJsonInputText] = useState<string>('')
  const [geoJsonError, setGeoJsonError] = useState<string | null>(null)
  const [geoJsonSuccess, setGeoJsonSuccess] = useState<string | null>(null)

  // Supervisor Assignment Modal
  const [supervisorModalOpen, setSupervisorModalOpen] = useState<boolean>(false)
  const [supervisorForm, setSupervisorForm] = useState({
    user_id: '',
    ward_id: '',
    sub_ward_id: '',
    role_title: 'Sub-Ward Operations Lead',
  })
  const [savingSupervisor, setSavingSupervisor] = useState<boolean>(false)

  // Detail GIS Map & Incident Markers
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const geojsonLayerRef = useRef<L.GeoJSON | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)

  // Modal Drawing Map
  const modalMapContainerRef = useRef<HTMLDivElement | null>(null)
  const modalMapInstanceRef = useRef<L.Map | null>(null)
  const modalDrawingLayerRef = useRef<L.LayerGroup | null>(null)

  // ---------------------------------------------------------------------------
  // 1. Data Ingestion: Build 2-City Tree Structure (Mumbai & Navi Mumbai)
  // ---------------------------------------------------------------------------
  const loadTree = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.hierarchy.getTree()
      setRawAuthorities(data)

      if (!data || data.length === 0) {
        setAllWardsList([])
        setTreeData([])
        setSelectedNode(null)
        setLoading(false)
        return
      }

      // Collect flat list of all administrative wards for dropdown selection
      const wardsCollector: { id: string; name: string; code: string; auth: string }[] = []
      data.forEach((auth) => {
        ;(auth.children || []).forEach((zone) => {
          ;(zone.children || []).forEach((ward) => {
            wardsCollector.push({
              id: ward.id,
              name: ward.name,
              code: ward.code,
              auth: auth.code,
            })
          })
        })
      })
      setAllWardsList(wardsCollector)

      // Group authorities under City Roots (Mumbai -> BMC, Navi Mumbai -> NMMC)
      const bmcAuth = data.find((a) => a.code === 'BMC' || a.id.includes('BMC'))
      const nmmcAuth = data.find((a) => a.code === 'NMMC' || a.id.includes('NMMC'))

      const cityTree: HierarchyTreeNode[] = []

      if (bmcAuth) {
        cityTree.push({
          id: 'CITY-MUMBAI',
          label: 'Mumbai',
          name: 'Mumbai',
          code: 'MUMBAI',
          level: 'city',
          type: 'city',
          is_official: true,
          is_active: true,
          boundary_geojson: bmcAuth?.boundary_geojson,
          total_complaints: bmcAuth?.total_complaints || 0,
          direct_complaints: 0,
          unassigned_complaints: bmcAuth?.unassigned_complaints || 0,
          assigned_complaints: bmcAuth?.assigned_complaints || 0,
          in_progress_tasks: bmcAuth?.in_progress_tasks || 0,
          completed_complaints: bmcAuth?.completed_complaints || 0,
          assigned_crews_count: bmcAuth?.assigned_crews_count || 0,
          children: [bmcAuth],
        })
      }

      if (nmmcAuth) {
        cityTree.push({
          id: 'CITY-NAVI-MUMBAI',
          label: 'Navi Mumbai',
          name: 'Navi Mumbai',
          code: 'NAVI_MUMBAI',
          level: 'city',
          type: 'city',
          is_official: true,
          is_active: true,
          boundary_geojson: nmmcAuth?.boundary_geojson,
          total_complaints: nmmcAuth?.total_complaints || 0,
          direct_complaints: 0,
          unassigned_complaints: nmmcAuth?.unassigned_complaints || 0,
          assigned_complaints: nmmcAuth?.assigned_complaints || 0,
          in_progress_tasks: nmmcAuth?.in_progress_tasks || 0,
          completed_complaints: nmmcAuth?.completed_complaints || 0,
          assigned_crews_count: nmmcAuth?.assigned_crews_count || 0,
          children: [nmmcAuth],
        })
      }

      // If data has other authorities not matching BMC or NMMC, include them
      const otherAuths = data.filter((a) => a !== bmcAuth && a !== nmmcAuth)
      if (otherAuths.length > 0) {
        if (cityTree.length > 0) {
          cityTree[0].children.push(...otherAuths)
        } else {
          cityTree.push(...otherAuths)
        }
      }

      setTreeData(cityTree)

      // Default expand nodes
      const initialExpanded = new Set<string>()
      cityTree.forEach((city) => {
        initialExpanded.add(city.id)
        city.children.forEach((auth) => {
          initialExpanded.add(auth.id)
          ;(auth.children || []).forEach((zone) => {
            initialExpanded.add(zone.id)
            ;(zone.children || []).forEach((ward) => {
              initialExpanded.add(ward.id)
            })
          })
        })
      })
      setExpandedNodeIds(initialExpanded)

      // Select first ward or authority if none selected
      if (!selectedNode && cityTree.length > 0) {
        const firstCity = cityTree[0]
        const firstAuth = firstCity.children[0]
        if (
          firstAuth &&
          firstAuth.children &&
          firstAuth.children[0] &&
          firstAuth.children[0].children &&
          firstAuth.children[0].children[0]
        ) {
          setSelectedNode(firstAuth.children[0].children[0])
        } else if (firstAuth) {
          setSelectedNode(firstAuth)
        } else {
          setSelectedNode(firstCity)
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load administrative hierarchy tree')
    } finally {
      setLoading(false)
    }
  }

  // Load field teams for allocation
  const loadTeams = async () => {
    try {
      setLoadingTeams(true)
      const teams = await api.admin.getTeams()
      setAllTeams(teams)
    } catch (err) {
      console.warn('Could not load operational teams:', err)
    } finally {
      setLoadingTeams(false)
    }
  }

  useEffect(() => {
    loadTree()
    loadTeams()
  }, [])

  // ---------------------------------------------------------------------------
  // 2. Fetch Node Issues when Selected Node changes
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!selectedNode) return

    const fetchNodeIssues = async () => {
      try {
        setLoadingIssues(true)
        const allIssues = await api.getIssues()

        // Filter based on selected node level
        let filtered: Issue[] = []
        if (selectedNode.level === 'city') {
          if (selectedNode.code === 'MUMBAI') {
            filtered = allIssues.filter((i) => i.authority_code === 'BMC' || (i.ward && !i.ward.startsWith('NMMC')))
          } else {
            filtered = allIssues.filter((i) => i.authority_code === 'NMMC' || (i.ward && i.ward.startsWith('NMMC')))
          }
        } else if (selectedNode.level === 'authority') {
          filtered = allIssues.filter((i) => i.authority_id === selectedNode.id || i.authority_code === selectedNode.code)
        } else if (selectedNode.level === 'zone') {
          filtered = allIssues.filter((i) => i.zone_id === selectedNode.id)
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

  // Filtered issues according to Category and Status pills
  const displayedNodeIssues = useMemo(() => {
    return nodeIssues.filter((issue) => {
      if (filterCategory !== 'ALL' && issue.category !== filterCategory) return false
      if (filterStatus !== 'ALL') {
        const s = (issue.status || '').toUpperCase()
        if (filterStatus === 'RESOLVED' && !s.includes('RESOLVED') && !s.includes('CLOSED')) return false
        if (filterStatus === 'IN_PROGRESS' && !s.includes('PROGRESS')) return false
        if (filterStatus === 'ASSIGNED' && s !== 'ASSIGNED' && s !== 'SCHEDULED') return false
        if (filterStatus === 'OPEN' && (s.includes('RESOLVED') || s.includes('PROGRESS'))) return false
      }
      return true
    })
  }, [nodeIssues, filterCategory, filterStatus])

  // ---------------------------------------------------------------------------
  // 3. Leaflet Tactical GIS Preview & Incident Markers
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [19.0760, 72.8850],
        zoom: 11,
        zoomControl: true,
        attributionControl: false,
      })

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16 }
      ).addTo(map)

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16, opacity: 0.85 }
      ).addTo(map)

      markersLayerRef.current = L.layerGroup().addTo(map)
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
        const isSubWard = selectedNode.level === 'sub_ward'
        const geoLayer = L.geoJSON(selectedNode.boundary_geojson as any, {
          style: {
            color: isSubWard ? '#6457E8' : '#8B5CF6',
            weight: isSubWard ? 2.5 : 2,
            dashArray: isSubWard ? '4, 4' : undefined,
            fillColor: isSubWard ? '#6457E8' : '#8B5CF6',
            fillOpacity: isSubWard ? 0.22 : 0.12,
          },
        }).addTo(map)

        geojsonLayerRef.current = geoLayer
        const bounds = geoLayer.getBounds()
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 })
        }
      } catch (err) {
        console.warn('Could not render geojson on preview map:', err)
      }
    }

    // Render Incident Markers for this jurisdiction
    if (markersLayerRef.current) {
      markersLayerRef.current.clearLayers()

      displayedNodeIssues.forEach((iss) => {
        if (!iss.latitude || !iss.longitude) return

        const isCritical = iss.priorityLevel === 'CRITICAL' || iss.priorityScore >= 80
        const isResolved = (iss.status || '').toUpperCase().includes('RESOLVED')
        const markerColor = isResolved
          ? '#10B981'
          : isCritical
          ? '#EF4444'
          : iss.priorityScore >= 50
          ? '#F59E0B'
          : '#3B82F6'

        const pinIcon = L.divIcon({
          className: 'civic-incident-pin',
          html: `
            <div style="position: relative; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              ${isCritical ? `<div style="position: absolute; width: 20px; height: 20px; border-radius: 9999px; background-color: ${markerColor}; opacity: 0.4;" class="animate-ping"></div>` : ''}
              <div style="width: 12px; height: 12px; border-radius: 9999px; background-color: ${markerColor}; border: 2px solid #FFFFFF; box-shadow: 0 0 8px ${markerColor};"></div>
            </div>
          `,
          iconSize: [20, 20],
          iconAnchor: [10, 10],
        })

        const marker = L.marker([iss.latitude, iss.longitude], { icon: pinIcon })
        marker.bindPopup(`
          <div style="font-family: inherit; font-size: 11px; color: #11162A; min-width: 180px; padding: 2px;">
            <div style="font-weight: 700; margin-bottom: 2px;">${iss.issueId} • ${iss.category}</div>
            <div style="color: #65708B; font-size: 10px; margin-bottom: 6px;">${iss.location || 'Location verified'}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E4E7F1; padding-top: 4px;">
              <span style="font-weight: 600; color: ${markerColor};">Priority: ${iss.priorityScore.toFixed(1)}</span>
              <span style="font-weight: 600; text-transform: uppercase; font-size: 9px;">${iss.status}</span>
            </div>
          </div>
        `)
        markersLayerRef.current?.addLayer(marker)
      })
    }
  }, [selectedNode, displayedNodeIssues])

  // ---------------------------------------------------------------------------
  // 4. Modal Interactive Drawing Map (Polygon Creation & GeoJSON Import)
  // ---------------------------------------------------------------------------
  useEffect(() => {
    if (!subWardModalOpen || !modalMapContainerRef.current) return

    if (!modalMapInstanceRef.current) {
      const map = L.map(modalMapContainerRef.current, {
        center: [subWardForm.center_lat || 19.0760, subWardForm.center_lng || 72.8850],
        zoom: 12,
        zoomControl: true,
        attributionControl: false,
      })

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16 }
      ).addTo(map)

      modalDrawingLayerRef.current = L.layerGroup().addTo(map)
      modalMapInstanceRef.current = map

      // Map click handler when drawing mode is active
      map.on('click', (e: L.LeafletMouseEvent) => {
        setDrawnPoints((prev) => [...prev, [e.latlng.lat, e.latlng.lng]])
      })
    }

    const map = modalMapInstanceRef.current
    if (!map) return

    // Re-render drawn vertices and polyline
    if (modalDrawingLayerRef.current) {
      modalDrawingLayerRef.current.clearLayers()

      if (drawnPoints.length > 0) {
        // Render markers for vertices
        drawnPoints.forEach(([lat, lng], idx) => {
          const vertexMarker = L.circleMarker([lat, lng], {
            radius: 5,
            color: '#FFFFFF',
            weight: 2,
            fillColor: '#6457E8',
            fillOpacity: 1,
          })
          vertexMarker.bindTooltip(`Vertex #${idx + 1}`, { permanent: false })
          modalDrawingLayerRef.current?.addLayer(vertexMarker)
        })

        // Render connecting line
        if (drawnPoints.length >= 2) {
          const line = L.polyline(drawnPoints, {
            color: '#6457E8',
            weight: 3,
            dashArray: '3, 6',
          })
          modalDrawingLayerRef.current?.addLayer(line)
        }

        // Preview polygon if >= 3 points
        if (drawnPoints.length >= 3) {
          const previewPoly = L.polygon(drawnPoints, {
            color: '#6457E8',
            weight: 2,
            fillColor: '#8B5CF6',
            fillOpacity: 0.25,
          })
          modalDrawingLayerRef.current?.addLayer(previewPoly)
        }
      } else if (subWardForm.boundary_geojson) {
        // Render existing or imported GeoJSON
        try {
          const geoLayer = L.geoJSON(subWardForm.boundary_geojson as any, {
            style: {
              color: '#6457E8',
              weight: 2.5,
              fillColor: '#8B5CF6',
              fillOpacity: 0.25,
            },
          })
          modalDrawingLayerRef.current?.addLayer(geoLayer)
          const b = geoLayer.getBounds()
          if (b.isValid()) map.fitBounds(b, { padding: [20, 20], maxZoom: 14 })
        } catch (e) {
          console.warn('Could not display existing boundary on modal map:', e)
        }
      }
    }
  }, [subWardModalOpen, drawnPoints, subWardForm.boundary_geojson])

  // Finish polygon drawing
  const handleCompletePolygonDrawing = () => {
    if (drawnPoints.length < 3) {
      alert('A polygon boundary requires at least 3 vertices.')
      return
    }

    // Convert drawn points [lat, lng] to GeoJSON standard [lng, lat] closed ring
    const ring = drawnPoints.map(([lat, lng]) => [Number(lng.toFixed(6)), Number(lat.toFixed(6))])
    // Close ring
    if (ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) {
      ring.push([...ring[0]])
    }

    const geojson: Record<string, any> = {
      type: 'Polygon',
      coordinates: [ring],
    }

    // Centroid calculation
    const avgLat = drawnPoints.reduce((acc, p) => acc + p[0], 0) / drawnPoints.length
    const avgLng = drawnPoints.reduce((acc, p) => acc + p[1], 0) / drawnPoints.length

    setSubWardForm({
      ...subWardForm,
      boundary_geojson: geojson,
      center_lat: Number(avgLat.toFixed(5)),
      center_lng: Number(avgLng.toFixed(5)),
    })
    setIsDrawingPolygon(false)
    setGeoJsonSuccess(`Successfully drafted polygon with ${drawnPoints.length} vertices.`)
    setGeoJsonError(null)
  }

  // GeoJSON Import Validator
  const handleValidateAndImportGeoJson = () => {
    setGeoJsonError(null)
    setGeoJsonSuccess(null)

    if (!geoJsonInputText.trim()) {
      setGeoJsonError('Please paste valid GeoJSON string.')
      return
    }

    try {
      const parsed = JSON.parse(geoJsonInputText)
      let geometry = parsed

      if (parsed.type === 'Feature') {
        geometry = parsed.geometry
      } else if (parsed.type === 'FeatureCollection' && parsed.features && parsed.features.length > 0) {
        geometry = parsed.features[0].geometry
      }

      if (!geometry || (geometry.type !== 'Polygon' && geometry.type !== 'MultiPolygon')) {
        throw new Error('Geometry must be of type "Polygon" or "MultiPolygon".')
      }

      // Extract coordinates sample to check CRS
      let sampleCoord: number[] = []
      if (geometry.type === 'Polygon') {
        sampleCoord = geometry.coordinates[0][0]
      } else if (geometry.type === 'MultiPolygon') {
        sampleCoord = geometry.coordinates[0][0][0]
      }

      if (!sampleCoord || sampleCoord.length < 2) {
        throw new Error('Could not parse coordinate array.')
      }

      // Check WGS84 range: Longitude [72-74], Latitude [18-20]
      const [lng, lat] = sampleCoord
      if (lng < 72 || lng > 74 || lat < 18 || lat > 20) {
        throw new Error(
          `Coordinates [${lng}, ${lat}] appear outside the Mumbai/Navi Mumbai bounding range (EPSG:4326 [lng, lat] expected).`
        )
      }

      setSubWardForm({
        ...subWardForm,
        boundary_geojson: geometry,
        center_lat: Number(lat.toFixed(5)),
        center_lng: Number(lng.toFixed(5)),
      })
      setDrawnPoints([])
      setGeoJsonSuccess(`Valid ${geometry.type} imported successfully. Centroid aligned.`)
    } catch (err: any) {
      setGeoJsonError(err?.message || 'Invalid GeoJSON syntax.')
    }
  }

  // ---------------------------------------------------------------------------
  // 5. Expand / Collapse & Search
  // ---------------------------------------------------------------------------
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

  // Filter tree nodes recursively
  const filteredTree = useMemo(() => {
    if (!searchQuery.trim()) return treeData
    const q = searchQuery.toLowerCase().trim()

    const filterNode = (node: HierarchyTreeNode): HierarchyTreeNode | null => {
      const nodeName = (node.name || node.label || '').toLowerCase()
      const nodeCode = (node.code || '').toLowerCase()
      const supervisor = (node.supervisor || node.supervisor_name || '').toLowerCase()
      const leadOfficer = (node.lead_officer || '').toLowerCase()
      const department = (node.department || '').toLowerCase()

      const directMatch =
        nodeName.includes(q) ||
        nodeCode.includes(q) ||
        supervisor.includes(q) ||
        leadOfficer.includes(q) ||
        department.includes(q)

      let filteredChildren: HierarchyTreeNode[] = []
      if (node.children && node.children.length > 0) {
        filteredChildren = node.children
          .map((c) => filterNode(c))
          .filter((c): c is HierarchyTreeNode => c !== null)
      }

      if (directMatch) {
        return {
          ...node,
          children: filteredChildren.length > 0 ? filteredChildren : (node.children || []),
        }
      }

      if (filteredChildren.length > 0) {
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

  // Auto-expand matching branches on search
  useEffect(() => {
    if (!searchQuery.trim()) return
    const idsToExpand = new Set<string>()
    const collectIds = (nodes: HierarchyTreeNode[]) => {
      nodes.forEach((n) => {
        idsToExpand.add(n.id)
        if (n.children && n.children.length > 0) collectIds(n.children)
      })
    }
    collectIds(filteredTree)
    setExpandedNodeIds((prev) => new Set([...prev, ...idsToExpand]))
  }, [searchQuery, filteredTree])

  // ---------------------------------------------------------------------------
  // 6. Sub-Ward CRUD Actions (Admin Only)
  // ---------------------------------------------------------------------------
  const handleOpenAddSubWard = (parentWardId?: string) => {
    if (!isAdmin) {
      alert('Only administrators can create operational sub-wards.')
      return
    }
    const defaultParent = parentWardId || (allWardsList.length > 0 ? allWardsList[0].id : 'WARD-BMC-N')
    setEditingSubWard(null)
    setParentWardForNew(defaultParent)
    setSubWardForm({
      code: '',
      name: '',
      ward_id: defaultParent,
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: '',
      assigned_department: 'Road Infrastructure Maintenance',
      is_active: true,
      boundary_geojson: null,
    })
    setDrawnPoints([])
    setGeoJsonInputText('')
    setGeoJsonError(null)
    setGeoJsonSuccess(null)
    setSubWardModalOpen(true)
  }

  const handleOpenEditSubWard = (node: HierarchyTreeNode) => {
    if (!isAdmin) {
      alert('Only administrators can modify operational sub-wards.')
      return
    }
    setEditingSubWard({
      id: node.id,
      ward_id: node.parent_id || '',
      code: node.code,
      name: node.name,
      is_official: false,
      operational_type: 'CIVILENS_OPERATIONAL_SUB_WARD',
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: node.supervisor || node.supervisor_name,
      assigned_department: node.department,
      is_active: node.is_active,
      boundary_geojson: node.boundary_geojson,
    })
    setParentWardForNew(node.parent_id || '')
    setSubWardForm({
      code: node.code,
      name: node.name,
      ward_id: node.parent_id || '',
      center_lat: 19.0760,
      center_lng: 72.8850,
      supervisor_name: node.supervisor || node.supervisor_name || '',
      assigned_department: node.department || 'Road Infrastructure Maintenance',
      is_active: node.is_active,
      boundary_geojson: node.boundary_geojson || null,
    })
    setDrawnPoints([])
    setGeoJsonInputText(node.boundary_geojson ? JSON.stringify(node.boundary_geojson, null, 2) : '')
    setGeoJsonError(null)
    setGeoJsonSuccess(null)
    setSubWardModalOpen(true)
  }

  const handleSaveSubWard = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isAdmin) return

    try {
      setSavingSubWard(true)
      if (editingSubWard) {
        await api.hierarchy.updateSubWard(editingSubWard.id, {
          name: subWardForm.name,
          code: subWardForm.code,
          supervisor_name: subWardForm.supervisor_name,
          assigned_department: subWardForm.assigned_department,
          is_active: subWardForm.is_active,
          boundary_geojson: subWardForm.boundary_geojson || undefined,
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
          boundary_geojson: subWardForm.boundary_geojson || undefined,
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
    if (!isAdmin) {
      alert('Only administrators can deactivate operational sub-wards.')
      return
    }
    if (!confirm(`Are you sure you want to deactivate or remove operational sub-ward "${name}"?`)) return
    try {
      await api.hierarchy.deleteSubWard(subWardId)
      await loadTree()
      if (selectedNode?.id === subWardId) {
        setSelectedNode(null)
      }
    } catch (err: any) {
      alert(err?.message || 'Failed to deactivate sub-ward')
    }
  }

  // ---------------------------------------------------------------------------
  // 7. Team & Crew Allocation Actions (Admin Only)
  // ---------------------------------------------------------------------------
  const handleOpenTeamModal = () => {
    if (!isAdmin) {
      alert('Only administrators can configure field crews and department allocations.')
      return
    }
    setNewTeamForm({
      name: '',
      department: selectedNode?.department || 'Road Infrastructure Maintenance',
      category: 'Roads & Footpaths',
      capacity: 6,
      contact_lead: selectedNode?.supervisor || 'Duty Supervisor',
    })
    setAssignExistingTeamId('')
    setTeamModalOpen(true)
  }

  const handleCreateAndAssignTeam = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isAdmin || !selectedNode) return

    try {
      setSavingTeam(true)
      const payload: Partial<FieldTeam> = {
        name: newTeamForm.name,
        department: newTeamForm.department,
        category: newTeamForm.category,
        capacity: Number(newTeamForm.capacity),
        contact_lead: newTeamForm.contact_lead,
        ward: selectedNode.level === 'ward' ? selectedNode.code : selectedNode.parent_id || 'ALL',
        sub_ward_id: selectedNode.level === 'sub_ward' ? selectedNode.id : undefined,
        status: 'AVAILABLE',
      }

      await api.admin.createTeam(payload)
      await loadTeams()
      await loadTree()
      setTeamModalOpen(false)
    } catch (err: any) {
      alert(err?.message || 'Failed to create field team')
    } finally {
      setSavingTeam(false)
    }
  }

  const handleAssignExistingTeam = async () => {
    if (!isAdmin || !selectedNode || !assignExistingTeamId) return

    try {
      setSavingTeam(true)
      await api.admin.updateTeam(assignExistingTeamId, {
        sub_ward_id: selectedNode.level === 'sub_ward' ? selectedNode.id : undefined,
        ward: selectedNode.level === 'ward' ? selectedNode.code : undefined,
      })
      await loadTeams()
      await loadTree()
      setAssignExistingTeamId('')
    } catch (err: any) {
      alert(err?.message || 'Failed to assign field crew')
    } finally {
      setSavingTeam(false)
    }
  }

  const handleUnassignTeam = async (teamId: string) => {
    if (!isAdmin) return
    if (!confirm('Unassign this field team from the current operational unit?')) return

    try {
      await api.admin.updateTeam(teamId, {
        sub_ward_id: undefined,
      })
      await loadTeams()
      await loadTree()
    } catch (err: any) {
      alert(err?.message || 'Failed to unassign team')
    }
  }

  // ---------------------------------------------------------------------------
  // 8. Supervisor Assignment Action
  // ---------------------------------------------------------------------------
  const handleOpenAssignSupervisor = (node: HierarchyTreeNode) => {
    if (!isAdmin) {
      alert('Only administrators can assign supervisors to administrative jurisdictions.')
      return
    }
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
    if (!isAdmin) return

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

  // ---------------------------------------------------------------------------
  // 9. Recursive Tree Node Renderer
  // ---------------------------------------------------------------------------
  const renderTreeNode = (node: HierarchyTreeNode, depth = 0) => {
    const isExpanded = expandedNodeIds.has(node.id)
    const isSelected = selectedNode?.id === node.id
    const hasChildren = node.children && node.children.length > 0

    const getLevelBadge = () => {
      switch (node.level) {
        case 'city':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#1E1B4B] text-white">
              City
            </span>
          )
        case 'authority':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-[#13152E] text-white">
              Authority
            </span>
          )
        case 'zone':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-[#8B5CF6]/15 text-[#6457E8]">
              Zone
            </span>
          )
        case 'ward':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
              Admin Ward
            </span>
          )
        case 'sub_ward':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-blue-100 text-blue-800 border border-blue-200">
              CIVILENS Sub-Ward
            </span>
          )
        case 'locality':
          return (
            <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">
              Locality Beat
            </span>
          )
        default:
          return null
      }
    }

    return (
      <div key={node.id} className="select-none">
        <div
          onClick={() => setSelectedNode(node)}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
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

          <div className="flex items-center gap-2 shrink-0">
            {/* Workload Indicator Pill */}
            <div className="flex items-center gap-1.5 text-[11px]">
              <span
                className={cn(
                  'px-2 py-0.5 rounded-full font-mono font-medium',
                  node.total_complaints > 0
                    ? 'bg-rose-50 text-rose-700 border border-rose-200'
                    : 'bg-slate-100 text-slate-500'
                )}
                title="Total active complaints in this jurisdiction branch"
              >
                {node.total_complaints} total
              </span>

              {node.direct_complaints !== undefined && node.direct_complaints > 0 && (
                <span
                  className="px-1.5 py-0.5 rounded-full text-[10px] bg-indigo-50 text-indigo-700 border border-indigo-200 font-semibold"
                  title="Direct complaints assigned to this specific jurisdiction unit"
                >
                  {node.direct_complaints} direct
                </span>
              )}

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
            {isAdmin && (
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
                      title="Deactivate Operational Sub-Ward"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </div>
            )}
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

  // ---------------------------------------------------------------------------
  // 10. Role Gate Guard: Block Citizens
  // ---------------------------------------------------------------------------
  if (isCitizen) {
    return (
      <div className="p-12 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs text-center space-y-3">
        <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
          <Lock className="w-6 h-6" />
        </div>
        <h2 className="text-base font-bold text-[#11162A]">Access Restricted</h2>
        <p className="text-xs text-[#65708B] max-w-md mx-auto">
          The Ward Hierarchy & Crew Allocation management module is restricted to authorized municipal officers
          and central administrators. Citizen accounts cannot access administrative governance tools.
        </p>
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
                Hierarchical geographic governance across Mumbai (BMC) and Navi Mumbai (NMMC) down to operational service beats
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isAdmin && (
            <button
              onClick={() => handleOpenAddSubWard()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#6457E8] text-white rounded-lg hover:bg-[#5145CF] transition shadow-xs cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Sub-Ward</span>
            </button>
          )}
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
            onClick={() => {
              loadTree()
              loadTeams()
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-white border border-[#E4E7F1] text-[#11162A] rounded-lg hover:bg-slate-50 transition shadow-xs cursor-pointer"
          >
            <RefreshCw className={cn('w-3.5 h-3.5', loading && 'animate-spin')} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Role Banner for Ward Officers (Inspectors) */}
      {isInspector && (
        <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center gap-2.5">
          <Info className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Ward Officer Notice:</strong> You are viewing operational data scoped to your authorized municipal jurisdiction.
            Master hierarchy restructuring, sub-ward creation, and city-wide crew assignments are reserved for Administrators.
          </span>
        </div>
      )}

      {/* 2. Authority Separation Notice Strip */}
      <div className="p-3.5 bg-white border border-[#E4E7F1] rounded-2xl shadow-xs flex items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-bold text-xs">
            BMC
          </div>
          <div>
            <div className="font-semibold text-[#11162A]">Brihanmumbai Municipal Corporation (Mumbai)</div>
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
          <Shield className="w-4 h-4 text-[#6457E8]" />
          <span>Strict separation: BMC and NMMC operate independent ward hierarchies and dispatch rules.</span>
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
                <span>City & Administrative Tree</span>
              </h2>
              <span className="text-[11px] text-[#65708B] font-mono">
                {treeData.length} {treeData.length === 1 ? 'City' : 'Cities'} • {rawAuthorities.length} {rawAuthorities.length === 1 ? 'Authority' : 'Authorities'}
              </span>
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-[#65708B] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search city, authority, ward, sub-ward, beat, supervisor..."
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
            ) : error ? (
              <div className="p-8 text-center text-xs space-y-3">
                <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div className="text-rose-700 font-semibold">{error}</div>
                <button
                  onClick={() => {
                    loadTree()
                    loadTeams()
                  }}
                  className="px-3 py-1.5 text-xs font-semibold bg-[#6457E8] text-white rounded-lg hover:bg-[#5145CF] transition cursor-pointer"
                >
                  Retry Loading
                </button>
              </div>
            ) : isInspector && rawAuthorities.length === 0 ? (
              <div className="p-8 text-center text-xs space-y-2">
                <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
                  <Shield className="w-5 h-5" />
                </div>
                <div className="font-semibold text-[#11162A]">No Jurisdiction Assigned</div>
                <p className="text-[#65708B] max-w-xs mx-auto">
                  No administrative jurisdiction has been assigned to this account. Please contact an administrator.
                </p>
              </div>
            ) : filteredTree.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#65708B]">
                {searchQuery ? `No administrative entities match "${searchQuery}"` : 'No administrative entities available.'}
              </div>
            ) : (
              filteredTree.map((cityNode) => renderTreeNode(cityNode, 0))
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
                    <div className="flex items-center gap-2 flex-wrap">
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
                          CIVILENS Operational Service Area (Non-Statutory)
                        </span>
                      )}
                      {!selectedNode.is_active && (
                        <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          Inactive
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-[#65708B] mt-1 flex items-center gap-3">
                      <span>
                        Level: <strong className="text-[#11162A] capitalize">{selectedNode.level.replace('_', ' ')}</strong>
                      </span>
                      {selectedNode.parent_id && (
                        <span>
                          Parent ID: <code className="font-mono">{selectedNode.parent_id}</code>
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isAdmin && (selectedNode.level === 'ward' || selectedNode.level === 'sub_ward') && (
                      <>
                        <button
                          onClick={handleOpenTeamModal}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#F0F2F9] text-[#11162A] border border-[#E4E7F1] rounded-xl hover:bg-slate-200 transition cursor-pointer"
                        >
                          <Wrench className="w-3.5 h-3.5 text-[#6457E8]" />
                          <span>Manage Crews</span>
                        </button>
                        <button
                          onClick={() => handleOpenAssignSupervisor(selectedNode)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#F0F2F9] text-[#11162A] border border-[#E4E7F1] rounded-xl hover:bg-slate-200 transition cursor-pointer"
                        >
                          <UserCheck className="w-3.5 h-3.5 text-[#6457E8]" />
                          <span>Assign Lead</span>
                        </button>
                      </>
                    )}
                    {isAdmin && selectedNode.level === 'ward' && (
                      <button
                        onClick={() => handleOpenAddSubWard(selectedNode.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-[#6457E8] text-white rounded-xl hover:bg-[#5145CF] transition shadow-xs cursor-pointer"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>New Sub-Ward</span>
                      </button>
                    )}
                    {isAdmin && selectedNode.level === 'sub_ward' && (
                      <button
                        onClick={() => handleOpenEditSubWard(selectedNode)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-100 text-[#11162A] rounded-xl hover:bg-slate-200 transition cursor-pointer"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                        <span>Edit Sub-Ward</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* Direct Complaints vs Aggregate Sub-Area Metrics Strip */}
                <div className="grid grid-cols-2 sm:grid-cols-6 gap-2 pt-2 border-t border-[#E4E7F1]">
                  <div className="p-3 bg-[#F6F7FC] rounded-xl">
                    <div className="text-[10px] font-semibold text-[#65708B] uppercase">Total Complaints</div>
                    <div className="text-lg font-bold text-[#11162A] mt-0.5 font-mono">{selectedNode.total_complaints}</div>
                    <div className="text-[10px] text-[#65708B]">Cumulative branch</div>
                  </div>
                  <div className="p-3 bg-indigo-50/70 border border-indigo-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-indigo-800 uppercase">Direct Complaints</div>
                    <div className="text-lg font-bold text-indigo-900 mt-0.5 font-mono">
                      {selectedNode.direct_complaints ?? 0}
                    </div>
                    <div className="text-[10px] text-indigo-700">Immediate level</div>
                  </div>
                  <div className="p-3 bg-amber-50/70 border border-amber-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-amber-800 uppercase">Unassigned</div>
                    <div className="text-lg font-bold text-amber-900 mt-0.5 font-mono">{selectedNode.unassigned_complaints}</div>
                    <div className="text-[10px] text-amber-700">Pending allocation</div>
                  </div>
                  <div className="p-3 bg-blue-50/70 border border-blue-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-blue-800 uppercase">Assigned</div>
                    <div className="text-lg font-bold text-blue-900 mt-0.5 font-mono">{selectedNode.assigned_complaints}</div>
                    <div className="text-[10px] text-blue-700">Dispatched</div>
                  </div>
                  <div className="p-3 bg-purple-50/70 border border-purple-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-purple-800 uppercase">In Progress</div>
                    <div className="text-lg font-bold text-purple-900 mt-0.5 font-mono">{selectedNode.in_progress_tasks}</div>
                    <div className="text-[10px] text-purple-700">Under repair</div>
                  </div>
                  <div className="p-3 bg-emerald-50/70 border border-emerald-200/50 rounded-xl">
                    <div className="text-[10px] font-semibold text-emerald-800 uppercase">Completed</div>
                    <div className="text-lg font-bold text-emerald-900 mt-0.5 font-mono">{selectedNode.completed_complaints}</div>
                    <div className="text-[10px] text-emerald-700">Verified resolved</div>
                  </div>
                </div>

                {/* Supervisor & Assigned Teams Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                  <div className="p-3 bg-white border border-[#E4E7F1] rounded-xl flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[#6457E8]/10 text-[#6457E8] flex items-center justify-center shrink-0">
                      <Users className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-[11px] text-[#65708B]">Responsible Supervisor</div>
                      <div className="font-semibold text-[#11162A]">
                        {selectedNode.supervisor || selectedNode.lead_officer || 'Unassigned (Ward Pool)'}
                      </div>
                    </div>
                  </div>

                  <div className="p-3 bg-white border border-[#E4E7F1] rounded-xl flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0">
                        <Wrench className="w-4 h-4" />
                      </div>
                      <div className="truncate">
                        <div className="text-[11px] text-[#65708B]">Assigned Field Crews</div>
                        <div className="font-semibold text-[#11162A] truncate">
                          {selectedNode.assigned_teams && selectedNode.assigned_teams.length > 0
                            ? selectedNode.assigned_teams.map((t) => t.name).join(', ')
                            : selectedNode.assigned_crews && selectedNode.assigned_crews.length > 0
                            ? selectedNode.assigned_crews.join(', ')
                            : 'No dedicated field crews allocated'}
                        </div>
                      </div>
                    </div>
                    {isAdmin && (
                      <button
                        onClick={handleOpenTeamModal}
                        className="px-2 py-1 text-[11px] font-semibold text-[#6457E8] hover:bg-[#6457E8]/10 rounded-lg shrink-0 cursor-pointer"
                      >
                        Configure
                      </button>
                    )}
                  </div>
                </div>

                {/* Direct Children Quick Jump Strip */}
                {selectedNode.children && selectedNode.children.length > 0 && (
                  <div className="pt-2 border-t border-[#E4E7F1] space-y-1.5">
                    <div className="text-[11px] font-semibold text-[#65708B] uppercase">
                      Sub-Divisions under {selectedNode.name} ({selectedNode.children.length})
                    </div>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {selectedNode.children.map((child) => (
                        <button
                          key={child.id}
                          onClick={() => setSelectedNode(child)}
                          className="px-2.5 py-1 text-[11px] font-medium bg-[#F6F7FC] hover:bg-[#6457E8]/10 hover:text-[#6457E8] border border-[#E4E7F1] rounded-lg transition cursor-pointer flex items-center gap-1"
                        >
                          <span>{child.name}</span>
                          <span className="text-[10px] text-[#65708B] font-mono">({child.total_complaints})</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tactical Boundary GIS Map & Filters */}
                <div className="space-y-2 pt-2 border-t border-[#E4E7F1]">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <span className="font-semibold text-[#11162A] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-[#6457E8]" />
                      <span>Boundary Polygon & Tactical Incident Radar</span>
                    </span>
                    <div className="flex items-center gap-2 flex-wrap text-[11px]">
                      {/* Category Filter */}
                      <select
                        value={filterCategory}
                        onChange={(e) => setFilterCategory(e.target.value)}
                        className="px-2 py-1 bg-[#F6F7FC] border border-[#E4E7F1] rounded-lg text-[#11162A] text-[11px] focus:outline-none"
                      >
                        <option value="ALL">All Categories</option>
                        <option value="Roads & Footpaths">Roads & Footpaths</option>
                        <option value="Sanitation & Garbage">Sanitation & Garbage</option>
                        <option value="Stormwater & Drainage">Stormwater & Drainage</option>
                        <option value="Streetlights & Electrical">Streetlights & Electrical</option>
                      </select>

                      {/* Status Filter */}
                      <select
                        value={filterStatus}
                        onChange={(e) => setFilterStatus(e.target.value)}
                        className="px-2 py-1 bg-[#F6F7FC] border border-[#E4E7F1] rounded-lg text-[#11162A] text-[11px] focus:outline-none"
                      >
                        <option value="ALL">All Statuses</option>
                        <option value="OPEN">Open</option>
                        <option value="ASSIGNED">Assigned</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="RESOLVED">Resolved</option>
                      </select>
                    </div>
                  </div>
                  <div className="h-64 w-full rounded-xl overflow-hidden border border-[#E4E7F1] relative">
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
                      Showing {displayedNodeIssues.length} complaints filtered under {selectedNode.name}
                    </p>
                  </div>
                </div>

                {loadingIssues ? (
                  <div className="py-12 flex flex-col items-center justify-center text-xs text-[#65708B] gap-2">
                    <RefreshCw className="w-4 h-4 animate-spin text-[#6457E8]" />
                    <span>Loading complaints for {selectedNode.name}...</span>
                  </div>
                ) : displayedNodeIssues.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#65708B] bg-[#F6F7FC] rounded-xl border border-dashed border-[#E4E7F1]">
                    No active complaints currently routed under this administrative branch matching active filters.
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
                        {displayedNodeIssues.slice(0, 10).map((issue) => (
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
                    {displayedNodeIssues.length > 10 && (
                      <div className="text-[11px] text-center text-[#65708B] pt-2">
                        Showing first 10 of {displayedNodeIssues.length} complaints.
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white border border-[#E4E7F1] rounded-2xl p-12 text-center text-[#65708B] text-xs">
              Select a city, municipal authority, administrative ward, or operational sub-ward from the tree to inspect details.
            </div>
          )}
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* Modal 1: Add / Edit CIVILENS Operational Sub-Ward & Boundary GIS     */}
      {/* --------------------------------------------------------------------- */}
      {subWardModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9000]">
          <div className="bg-white border border-[#E4E7F1] rounded-2xl max-w-2xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-[#6457E8]" />
                <h3 className="text-base font-bold text-[#11162A]">
                  {editingSubWard ? 'Edit CIVILENS Operational Sub-Ward' : 'Create Operational Sub-Ward'}
                </h3>
              </div>
              <button
                onClick={() => setSubWardModalOpen(false)}
                className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start gap-2">
              <Info className="w-4 h-4 shrink-0 text-blue-600 mt-0.5" />
              <span>
                <strong>Operational Sub-Ward Notice:</strong> This sub-division is designated as a{' '}
                <code>CIVILENS_OPERATIONAL_SUB_WARD</code> with <code>is_official=false</code>. It serves for tactical crew
                dispatch and must not be falsely presented as statutory government divisions.
              </span>
            </div>

            <form onSubmit={handleSaveSubWard} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Parent Administrative Ward</label>
                <select
                  required
                  value={subWardForm.ward_id}
                  onChange={(e) => setSubWardForm({ ...subWardForm, ward_id: e.target.value })}
                  className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                >
                  {allWardsList.map((w) => (
                    <option key={w.id} value={w.id}>
                      [{w.auth}] {w.name} ({w.code})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Sub-Ward Code</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. N-04 or V-03"
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
                    placeholder="e.g. Somaiya North Innovation Zone"
                    value={subWardForm.name}
                    onChange={(e) => setSubWardForm({ ...subWardForm, name: e.target.value })}
                    className="w-full px-3 py-2 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none focus:ring-1 focus:ring-[#6457E8]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
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
                    <option value="Road Infrastructure Maintenance">Road Infrastructure Maintenance</option>
                    <option value="Solid Waste Management & Sanitation">Solid Waste Management & Sanitation</option>
                    <option value="Hydraulic & Storm Water Drainage">Hydraulic & Storm Water Drainage</option>
                    <option value="Traffic & Street Furniture">Traffic & Street Furniture</option>
                  </select>
                </div>
              </div>

              {/* GIS Boundary Configuration Tabs: Interactive Draw or GeoJSON Import */}
              <div className="p-3.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#11162A] flex items-center gap-1.5">
                    <MapPin className="w-4 h-4 text-[#6457E8]" />
                    <span>Geographic Boundary Definition (GIS)</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setIsDrawingPolygon(!isDrawingPolygon)
                        setDrawnPoints([])
                      }}
                      className={cn(
                        'flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold cursor-pointer transition',
                        isDrawingPolygon
                          ? 'bg-rose-50 text-rose-700 border border-rose-300'
                          : 'bg-white border border-[#E4E7F1] text-[#11162A] hover:bg-slate-100'
                      )}
                    >
                      <PenTool className="w-3.5 h-3.5 text-[#6457E8]" />
                      <span>{isDrawingPolygon ? 'Cancel Drawing' : 'Draw Polygon on Map'}</span>
                    </button>
                  </div>
                </div>

                {isDrawingPolygon ? (
                  <div className="p-2.5 bg-purple-50 border border-purple-200 rounded-lg space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-purple-900">
                      <span>Click on the map below to place polygon boundary points ({drawnPoints.length} vertices added)</span>
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setDrawnPoints((prev) => prev.slice(0, -1))}
                          disabled={drawnPoints.length === 0}
                          className="px-2 py-0.5 bg-white border border-purple-200 rounded text-purple-800 disabled:opacity-50"
                        >
                          Undo Point
                        </button>
                        <button
                          type="button"
                          onClick={() => setDrawnPoints([])}
                          disabled={drawnPoints.length === 0}
                          className="px-2 py-0.5 bg-white border border-purple-200 rounded text-rose-700 disabled:opacity-50"
                        >
                          Clear Points
                        </button>
                        <button
                          type="button"
                          onClick={handleCompletePolygonDrawing}
                          disabled={drawnPoints.length < 3}
                          className="px-2.5 py-0.5 bg-[#6457E8] text-white rounded font-semibold disabled:opacity-50 flex items-center gap-1"
                        >
                          <Check className="w-3 h-3" />
                          <span>Complete Polygon</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <label className="block text-[11px] text-[#65708B]">
                      Paste validated GeoJSON Polygon / MultiPolygon or draw directly:
                    </label>
                    <div className="flex gap-2">
                      <textarea
                        rows={2}
                        placeholder='{"type": "Polygon", "coordinates": [[[72.88, 19.07], [72.90, 19.07], [72.90, 19.09], [72.88, 19.07]]]}'
                        value={geoJsonInputText}
                        onChange={(e) => setGeoJsonInputText(e.target.value)}
                        className="flex-1 px-3 py-1.5 bg-white border border-[#E4E7F1] rounded-xl font-mono text-[11px] text-[#11162A] focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={handleValidateAndImportGeoJson}
                        className="px-3 py-1.5 bg-white border border-[#E4E7F1] hover:bg-slate-100 rounded-xl font-semibold text-[11px] shrink-0"
                      >
                        Import GeoJSON
                      </button>
                    </div>
                  </div>
                )}

                {geoJsonError && (
                  <div className="p-2 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-[11px]">
                    {geoJsonError}
                  </div>
                )}
                {geoJsonSuccess && (
                  <div className="p-2 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-[11px]">
                    {geoJsonSuccess}
                  </div>
                )}

                {/* Modal Map Preview */}
                <div className="h-44 w-full rounded-xl overflow-hidden border border-[#E4E7F1]">
                  <div ref={modalMapContainerRef} className="h-full w-full" />
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-[#E4E7F1]">
                {editingSubWard ? (
                  <button
                    type="button"
                    onClick={() => handleDeleteSubWard(editingSubWard.id, editingSubWard.name)}
                    className="px-3 py-2 text-rose-600 hover:bg-rose-50 rounded-xl font-semibold flex items-center gap-1.5"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Deactivate Sub-Ward</span>
                  </button>
                ) : (
                  <div />
                )}

                <div className="flex items-center gap-2">
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
                    <span>{editingSubWard ? 'Save Changes' : 'Create Operational Sub-Ward'}</span>
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Modal 2: Manage Field Crews & Team Allocations                       */}
      {/* --------------------------------------------------------------------- */}
      {teamModalOpen && selectedNode && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9000]">
          <div className="bg-white border border-[#E4E7F1] rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
              <div className="flex items-center gap-2">
                <Wrench className="w-5 h-5 text-[#6457E8]" />
                <div>
                  <h3 className="text-base font-bold text-[#11162A]">Configure Field Crews & Teams</h3>
                  <p className="text-xs text-[#65708B]">
                    Allocating teams for {selectedNode.name} ({selectedNode.code})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setTeamModalOpen(false)}
                className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Currently Assigned Teams */}
            <div className="space-y-2">
              <div className="text-xs font-bold text-[#11162A] uppercase">Active Assigned Field Teams</div>
              {selectedNode.assigned_teams && selectedNode.assigned_teams.length > 0 ? (
                <div className="space-y-2">
                  {selectedNode.assigned_teams.map((t) => (
                    <div
                      key={t.id}
                      className="p-3 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="font-bold text-[#11162A]">{t.name}</div>
                        <div className="text-[11px] text-[#65708B] flex items-center gap-2 mt-0.5">
                          <span>{t.department}</span>
                          <span>•</span>
                          <span>Cap: {t.capacity || 6} crew</span>
                          <span>•</span>
                          <span
                            className={cn(
                              'font-semibold uppercase text-[10px]',
                              t.status === 'AVAILABLE' ? 'text-emerald-700' : 'text-amber-700'
                            )}
                          >
                            {t.status}
                          </span>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleUnassignTeam(t.id)}
                        className="px-2.5 py-1 text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg text-xs font-semibold"
                      >
                        Unassign
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-slate-50 border border-dashed border-[#E4E7F1] rounded-xl text-center text-xs text-[#65708B]">
                  No dedicated field teams currently allocated to this unit.
                </div>
              )}
            </div>

            {/* Assign Existing Available Team */}
            <div className="p-3.5 bg-slate-50 border border-[#E4E7F1] rounded-xl space-y-2 text-xs">
              <label className="block font-bold text-[#11162A]">Assign Existing Team to this Jurisdiction</label>
              <div className="flex gap-2">
                <select
                  value={assignExistingTeamId}
                  onChange={(e) => setAssignExistingTeamId(e.target.value)}
                  className="flex-1 px-3 py-1.5 bg-white border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none"
                >
                  <option value="">Select an available field team...</option>
                  {allTeams
                    .filter((t) => t.sub_ward_id !== selectedNode.id)
                    .map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.department} - {t.status})
                      </option>
                    ))}
                </select>
                <button
                  type="button"
                  onClick={handleAssignExistingTeam}
                  disabled={!assignExistingTeamId || savingTeam}
                  className="px-3 py-1.5 bg-[#6457E8] text-white rounded-xl font-semibold disabled:opacity-50"
                >
                  Assign
                </button>
              </div>
            </div>

            {/* Create & Allocate New Team */}
            <form onSubmit={handleCreateAndAssignTeam} className="space-y-3 pt-2 border-t border-[#E4E7F1] text-xs">
              <div className="font-bold text-[#11162A] uppercase">Or Create New Dedicated Field Team</div>

              <div>
                <label className="block font-semibold text-[#11162A] mb-1">Team Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ward N Rapid Asphalt Squad"
                  value={newTeamForm.name}
                  onChange={(e) => setNewTeamForm({ ...newTeamForm, name: e.target.value })}
                  className="w-full px-3 py-1.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Department</label>
                  <select
                    value={newTeamForm.department}
                    onChange={(e) => setNewTeamForm({ ...newTeamForm, department: e.target.value })}
                    className="w-full px-3 py-1.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none"
                  >
                    <option value="Road Infrastructure Maintenance">Road Infrastructure Maintenance</option>
                    <option value="Solid Waste Management & Sanitation">Solid Waste Management & Sanitation</option>
                    <option value="Hydraulic & Storm Water Drainage">Hydraulic & Storm Water Drainage</option>
                    <option value="Traffic & Street Furniture">Traffic & Street Furniture</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-[#11162A] mb-1">Crew Capacity (Members)</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={newTeamForm.capacity}
                    onChange={(e) => setNewTeamForm({ ...newTeamForm, capacity: Number(e.target.value) })}
                    className="w-full px-3 py-1.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[#11162A] focus:outline-none"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setTeamModalOpen(false)}
                  className="px-4 py-2 border border-[#E4E7F1] text-[#11162A] rounded-xl hover:bg-slate-50 font-semibold"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={savingTeam}
                  className="px-4 py-2 bg-[#6457E8] text-white rounded-xl hover:bg-[#5145CF] font-semibold flex items-center gap-1.5 shadow-xs"
                >
                  {savingTeam && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  <span>Create & Deploy Crew</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* Modal 3: Assign Supervisor                                            */}
      {/* --------------------------------------------------------------------- */}
      {supervisorModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-[9000]">
          <div className="bg-white border border-[#E4E7F1] rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E7F1]">
              <div className="flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-[#6457E8]" />
                <h3 className="text-base font-bold text-[#11162A]">Assign Jurisdiction Supervisor</h3>
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
                  placeholder="e.g. officer_n_ward or Inspector Rajesh Deshmukh"
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
