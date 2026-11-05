import React, { useEffect, useRef, useState, useMemo } from 'react'
import L from 'leaflet'
import { Issue, HotspotInfo } from '../../types'
import { MUMBAI_NAVI_MUMBAI_BOUNDS } from '../../config/geo'
import { api } from '../../services/api'

export type MapLayerMode = 'markers' | 'clusters' | 'heatmap' | 'hotspots'

export interface CivicMapProps {
  issues: Issue[]
  hotspots?: HotspotInfo[]
  selectedIssue?: Issue | null
  onSelectIssue?: (issue: Issue) => void
  selectedHotspot?: HotspotInfo | null
  onSelectHotspot?: (hotspot: HotspotInfo) => void
  layerMode?: MapLayerMode
  showHotspotBoundaries?: boolean
  showHotspotCircles?: boolean
  showAdminWards?: boolean
  showSubWards?: boolean
  selectedWardCode?: string
  selectedSubWardId?: string
  onSelectWard?: (wardProps: any) => void
  onSelectSubWard?: (subWardProps: any) => void
  className?: string
}

export const CivicMap: React.FC<CivicMapProps> = ({
  issues,
  hotspots = [],
  selectedIssue,
  onSelectIssue,
  selectedHotspot,
  onSelectHotspot,
  layerMode = 'markers',
  showHotspotBoundaries = true,
  showHotspotCircles,
  showAdminWards = true,
  showSubWards = true,
  selectedWardCode,
  selectedSubWardId,
  onSelectWard,
  onSelectSubWard,
  className = 'h-full w-full',
}) => {
  const displayHotspotBoundaries =
    showHotspotCircles !== undefined ? showHotspotCircles : showHotspotBoundaries
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)

  // Dedicated Leaflet Layer Groups for Independent Toggling & Zero Lingering Artifacts
  const adminWardsLayerRef = useRef<L.LayerGroup | null>(null)
  const subWardsLayerRef = useRef<L.LayerGroup | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)
  const hotspotsLayerRef = useRef<L.LayerGroup | null>(null)
  const heatmapLayerRef = useRef<L.LayerGroup | null>(null)
  const clustersLayerRef = useRef<L.LayerGroup | null>(null)
  const hasFittedInitialBoundsRef = useRef<boolean>(false)

  const [boundariesGeoJson, setBoundariesGeoJson] = useState<any | null>(null)
  const [wardsVisible, setWardsVisible] = useState<boolean>(showAdminWards)
  const [subWardsVisible, setSubWardsVisible] = useState<boolean>(showSubWards)
  const [currentZoom, setCurrentZoom] = useState<number>(13)

  // Keep internal toggle state synchronized if parent props change
  useEffect(() => {
    setWardsVisible(showAdminWards)
  }, [showAdminWards])

  useEffect(() => {
    setSubWardsVisible(showSubWards)
  }, [showSubWards])

  // Load GIS Boundaries once from backend API
  useEffect(() => {
    let active = true
    api.hierarchy
      .getGisBoundaries()
      .then((data) => {
        if (active) setBoundariesGeoJson(data)
      })
      .catch((e) => console.warn('Could not load GIS boundaries:', e))
    return () => {
      active = false
    }
  }, [])

  // 1. Initialize Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      const southWest = L.latLng(
        MUMBAI_NAVI_MUMBAI_BOUNDS.minLat - 0.05,
        MUMBAI_NAVI_MUMBAI_BOUNDS.minLng - 0.05
      )
      const northEast = L.latLng(
        MUMBAI_NAVI_MUMBAI_BOUNDS.maxLat + 0.05,
        MUMBAI_NAVI_MUMBAI_BOUNDS.maxLng + 0.05
      )
      const regionBounds = L.latLngBounds(southWest, northEast)

      // Centered on the active urban corridor (Vidyavihar / Ghatkopar / Kurla)
      const map = L.map(mapContainerRef.current, {
        center: [19.0728, 72.8998],
        zoom: 13,
        minZoom: 10,
        maxZoom: 18,
        maxBounds: regionBounds,
        maxBoundsViscosity: 1.0,
        zoomControl: false,
        attributionControl: false,
      })

      // Zoom Controls top-right
      L.control.zoom({ position: 'topright' }).addTo(map)

      // Track zoom level for dynamic, zoom-aware clustering
      map.on('zoomend', () => {
        setCurrentZoom(map.getZoom())
      })

      // ESRI Dark Gray Canvas (High contrast roads, zero watermark, dark graphite)
      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 16,
          attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ',
        }
      ).addTo(map)

      // ESRI Dark Gray Reference Labels Overlay
      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 16,
          opacity: 0.85,
        }
      ).addTo(map)

      // Independent Layer Groups
      const awl = L.layerGroup().addTo(map)
      const swl = L.layerGroup().addTo(map)
      const ml = L.layerGroup().addTo(map)
      const hl = L.layerGroup().addTo(map)
      const hml = L.layerGroup().addTo(map)
      const cl = L.layerGroup().addTo(map)

      adminWardsLayerRef.current = awl
      subWardsLayerRef.current = swl
      markersLayerRef.current = ml
      hotspotsLayerRef.current = hl
      heatmapLayerRef.current = hml
      clustersLayerRef.current = cl
      mapInstanceRef.current = map
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // 2. Render Administrative Ward GIS Boundaries (Official 24 BMC Wards)
  useEffect(() => {
    const awl = adminWardsLayerRef.current
    if (!awl) return
    awl.clearLayers()

    if (!wardsVisible || !boundariesGeoJson) return

    const features = boundariesGeoJson.features || []
    features.forEach((feature: any) => {
      const type = feature.properties?.type || (feature.properties?.layer === 'ward' ? 'ADMIN_WARD' : '')
      if (type !== 'ADMIN_WARD') return

      const props = feature.properties || {}
      const isSelected = selectedWardCode && (props.code === selectedWardCode || props.name?.includes(selectedWardCode))
      const wardComplaintsCount = issues.filter(
        (i) => i.ward === props.code || (i.ward && props.code && i.ward.includes(props.code))
      ).length

      const geo = L.geoJSON(feature, {
        style: {
          color: isSelected ? '#A78BFA' : '#8B5CF6',
          weight: isSelected ? 3.5 : 2.0,
          opacity: isSelected ? 1.0 : 0.8,
          dashArray: undefined,
          fillColor: isSelected ? '#C4B5FD' : '#8B5CF6',
          fillOpacity: isSelected ? 0.16 : 0.05,
        },
        onEachFeature: (_, layer) => {
          const authorityLabel = props.authority_id === 'AUTH-NMMC' ? 'Navi Mumbai (NMMC)' : 'Brihanmumbai (BMC)'
          const content = `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; color: #11162A; line-height: 1.45; min-width: 190px;">
              <div style="font-weight: 700; color: #13152E; font-size: 13px; margin-bottom: 2px;">
                ${props.name} <span style="font-family: monospace; font-size: 11px; color: #6457E8;">(${props.code})</span>
              </div>
              <div style="display: inline-block; padding: 1px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; background: #EEF2FF; color: #4338CA; margin-bottom: 6px;">
                ${authorityLabel}
              </div>
              <div style="color: #65708B;">Office: <span style="color: #11162A; font-weight: 500;">${props.office_location || 'Municipal Ward Office'}</span></div>
              <div style="color: #65708B;">Nodal Officer: <span style="color: #11162A; font-weight: 500;">${props.lead_officer || 'Officer In Charge'}</span></div>
              <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #E4E7F1; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #65708B;">Active Incidents:</span>
                <strong style="color: #6457E8; font-size: 12px;">${wardComplaintsCount}</strong>
              </div>
            </div>
          `
          layer.bindPopup(content)
          layer.bindTooltip(`${props.name} (${props.code})`, { sticky: true })

          layer.on('click', () => {
            if (onSelectWard) {
              onSelectWard({ ...props, complaintCount: wardComplaintsCount })
            }
          })
        },
      })
      awl.addLayer(geo)
    })
  }, [boundariesGeoJson, wardsVisible, selectedWardCode, issues, onSelectWard])

  // 3. Render CIVILENS Operational Sub-Ward Boundaries (Corridors, is_official=False)
  useEffect(() => {
    const swl = subWardsLayerRef.current
    if (!swl) return
    swl.clearLayers()

    if (!subWardsVisible || !boundariesGeoJson) return

    const features = boundariesGeoJson.features || []
    features.forEach((feature: any) => {
      const type = feature.properties?.type || (feature.properties?.layer === 'sub_ward' ? 'CIVILENS_OPERATIONAL_SUB_WARD' : '')
      if (type !== 'CIVILENS_OPERATIONAL_SUB_WARD') return

      const props = feature.properties || {}
      const isSelected = selectedSubWardId && (props.id === selectedSubWardId || props.code === selectedSubWardId)
      const subWardComplaintsCount = issues.filter(
        (i) => i.sub_ward_id === props.id || (props.code && i.sub_ward_id && i.sub_ward_id.includes(props.code)) || (props.name && i.sub_ward_name === props.name)
      ).length

      const geo = L.geoJSON(feature, {
        style: {
          color: isSelected ? '#818CF8' : '#6457E8',
          weight: isSelected ? 3.0 : 1.8,
          opacity: isSelected ? 1.0 : 0.9,
          dashArray: '5, 5',
          fillColor: isSelected ? '#A5B4FC' : '#6457E8',
          fillOpacity: isSelected ? 0.22 : 0.08,
        },
        onEachFeature: (_, layer) => {
          const content = `
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; color: #11162A; line-height: 1.45; min-width: 190px;">
              <div style="font-weight: 700; color: #6457E8; font-size: 13px;">${props.name}</div>
              <div style="display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 9.5px; font-weight: 600; background: #E0E7FF; color: #3730A3; margin: 4px 0 6px 0;">
                CIVILENS Operational Service Area (Beat)
              </div>
              <div style="color: #65708B;">Sub-Ward Code: <strong style="color: #11162A;">${props.code}</strong></div>
              <div style="color: #65708B;">Supervisor: <strong style="color: #11162A;">${props.supervisor_name || 'Area Supervisor'}</strong></div>
              <div style="color: #65708B;">Department: <strong style="color: #11162A;">${props.assigned_department || 'Infrastructure & Public Works'}</strong></div>
              <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #E4E7F1; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #65708B;">Active Beat Tasks:</span>
                <strong style="color: #6457E8; font-size: 12px;">${subWardComplaintsCount}</strong>
              </div>
            </div>
          `
          layer.bindPopup(content)
          layer.bindTooltip(`${props.name} (${props.code})`, { sticky: true })

          layer.on('click', () => {
            if (onSelectSubWard) {
              onSelectSubWard({ ...props, complaintCount: subWardComplaintsCount })
            }
          })
        },
      })
      swl.addLayer(geo)
    })
  }, [boundariesGeoJson, subWardsVisible, selectedSubWardId, issues, onSelectSubWard])

  // 4. Render Tactical Incident Layers based on layerMode (Markers, Clusters, Heatmap, Hotspots)
  useEffect(() => {
    const map = mapInstanceRef.current
    const ml = markersLayerRef.current
    const hl = hotspotsLayerRef.current
    const hml = heatmapLayerRef.current
    const cl = clustersLayerRef.current

    if (!map || !ml || !hl || !hml || !cl) return

    ml.clearLayers()
    hl.clearLayers()
    hml.clearLayers()
    cl.clearLayers()

    // -----------------------------------------------------------------
    // A. HOTSPOT VISUALIZATION (Boundaries, Radii, Centroids)
    // -----------------------------------------------------------------
    if (displayHotspotBoundaries && hotspots.length > 0) {
      hotspots.forEach((h) => {
        const isSelected = selectedHotspot?.hotspotId === h.hotspotId
        const isCritical = h.hotspotLevel === 'CRITICAL' || h.averagePriority >= 75
        const color = isCritical ? '#ef4444' : '#f97316'

        const lat = typeof h.center?.lat === 'number' ? h.center.lat : Array.isArray(h.center) ? Number(h.center[0]) : null
        const lng = typeof h.center?.lng === 'number' ? h.center.lng : Array.isArray(h.center) ? Number(h.center[1]) : null
        if (lat === null || lng === null || isNaN(lat) || isNaN(lng)) return

        const circle = L.circle([lat, lng], {
          radius: h.radiusMeters || 500,
          color: color,
          fillColor: color,
          fillOpacity: isSelected ? 0.28 : 0.12,
          weight: isSelected ? 2.5 : 1.5,
          dashArray: '5, 5',
        })

        const beaconIcon = L.divIcon({
          className: 'custom-beacon',
          html: `
            <div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <div style="position: absolute; width: 28px; height: 28px; border-radius: 9999px; background-color: ${color}; opacity: 0.35;" class="animate-ping"></div>
              <div style="width: 10px; height: 10px; border-radius: 9999px; background-color: ${color}; border: 2px solid #080a0f;"></div>
            </div>
          `,
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        })

        const beacon = L.marker([lat, lng], { icon: beaconIcon })

        const tooltipHtml = `
          <div style="font-family: monospace; font-size: 11px; padding: 4px;">
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
              <strong style="color: ${color}; font-size: 12px;">${h.hotspotId}</strong>
              <span style="color: ${color}; font-weight: bold; font-size: 10px; border: 1px solid ${color}; padding: 1px 4px; border-radius: 3px;">
                ${h.hotspotLevel}
              </span>
            </div>
            <div style="color: #f1f5f9; font-weight: bold; margin-top: 2px;">${h.dominantCategory}</div>
            <div style="color: #94a3b8; font-size: 10px; margin-top: 2px;">
              Cluster Size: <strong style="color: #e2e8f0;">${h.issueCount} Issues</strong>
            </div>
          </div>
        `
        beacon.bindTooltip(tooltipHtml, { sticky: true, className: 'leaflet-dark-tooltip' })

        const handleHotspotClick = () => {
          map.flyTo([lat, lng], 14, { duration: 1.0, easeLinearity: 0.25 })
          if (onSelectHotspot) onSelectHotspot(h)
        }

        circle.on('click', handleHotspotClick)
        beacon.on('click', handleHotspotClick)

        hl.addLayer(circle)
        hl.addLayer(beacon)
      })
    }

    // -----------------------------------------------------------------
    // B. HEATMAP LAYER (Smooth Priority & Density Radii)
    // -----------------------------------------------------------------
    if (layerMode === 'heatmap') {
      issues.forEach((issue) => {
        if (!issue.latitude || !issue.longitude) return

        const isCrit = issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
        const isHigh = issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
        const heatColor = isCrit ? '#EF4444' : isHigh ? '#F97316' : '#6457E8'
        const heatRadius = isCrit ? 450 : isHigh ? 320 : 220

        const heatCircle = L.circle([issue.latitude, issue.longitude], {
          radius: heatRadius,
          color: heatColor,
          fillColor: heatColor,
          fillOpacity: 0.22,
          weight: 0,
        })

        heatCircle.on('click', () => {
          map.flyTo([issue.latitude, issue.longitude], 15, { duration: 0.85 })
          if (onSelectIssue) onSelectIssue(issue)
        })

        hml.addLayer(heatCircle)
      })
      return
    }

    // -----------------------------------------------------------------
    // C. DYNAMIC ZOOM-AWARE MARKER CLUSTERING LAYER
    // -----------------------------------------------------------------
    if (layerMode === 'clusters') {
      // Dynamic spatial threshold: decreases as user zooms in, cleanly separating clusters
      const zoom = map.getZoom()
      const clusterThreshold = Math.max(0.003, 0.045 / Math.pow(1.8, Math.max(10, zoom) - 10))
      const clusters: { centerLat: number; centerLng: number; items: Issue[] }[] = []

      issues.forEach((issue) => {
        if (!issue.latitude || !issue.longitude) return

        let placed = false
        for (const clus of clusters) {
          const dLat = Math.abs(clus.centerLat - issue.latitude)
          const dLng = Math.abs(clus.centerLng - issue.longitude)
          if (dLat < clusterThreshold && dLng < clusterThreshold) {
            clus.items.push(issue)
            clus.centerLat = (clus.centerLat + issue.latitude) / 2
            clus.centerLng = (clus.centerLng + issue.longitude) / 2
            placed = true
            break
          }
        }

        if (!placed) {
          clusters.push({
            centerLat: issue.latitude,
            centerLng: issue.longitude,
            items: [issue],
          })
        }
      })

      clusters.forEach((clus) => {
        const hasCritical = clus.items.some((i) => i.priorityLevel === 'CRITICAL' || i.priorityScore >= 80)
        const hasHigh = clus.items.some((i) => i.priorityLevel === 'HIGH' || i.priorityScore >= 65)
        const clusterClass = hasCritical ? 'critical' : hasHigh ? 'high' : ''
        const size = Math.min(50, Math.max(32, 26 + clus.items.length * 3))

        const clusterIcon = L.divIcon({
          className: 'custom-cluster-wrapper',
          html: `
            <div class="tactical-cluster-icon ${clusterClass}" style="width: ${size}px; height: ${size}px; display: flex; align-items: center; justify-content: center; border-radius: 9999px; font-weight: bold; font-family: monospace; font-size: 11px; background: ${
              hasCritical ? '#EF4444' : hasHigh ? '#F97316' : '#6457E8'
            }; color: #FFFFFF; border: 2px solid #FFFFFF; box-shadow: 0 0 12px rgba(0,0,0,0.5);">
              <span>${clus.items.length}</span>
            </div>
          `,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        })

        const marker = L.marker([clus.centerLat, clus.centerLng], { icon: clusterIcon })

        marker.on('click', () => {
          if (clus.items.length === 1) {
            map.flyTo([clus.centerLat, clus.centerLng], 15, { duration: 0.85 })
            if (onSelectIssue) onSelectIssue(clus.items[0])
          } else {
            map.setView([clus.centerLat, clus.centerLng], map.getZoom() + 2, { animate: true })
          }
        })

        marker.bindTooltip(
          `<div style="font-family: monospace; font-size: 11px; color: #FFFFFF;">
            Cluster: <strong>${clus.items.length} incidents</strong><br/>
            Priority: <strong style="color: ${hasCritical ? '#ef4444' : '#f97316'};">${hasCritical ? 'CRITICAL' : hasHigh ? 'HIGH' : 'STANDARD'}</strong>
          </div>`,
          { className: 'leaflet-dark-tooltip' }
        )

        cl.addLayer(marker)
      })
      return
    }

    // -----------------------------------------------------------------
    // D. INCIDENT MARKERS WITH CATEGORY & PRIORITY DIFFERENTIATION
    // -----------------------------------------------------------------
    issues.forEach((issue) => {
      if (!issue.latitude || !issue.longitude) return

      const isCritical = issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
      const isHigh = issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
      const isMedium = issue.priorityLevel === 'MEDIUM' || issue.priorityScore >= 40
      const isSelected = selectedIssue?.issueId === issue.issueId

      // Priority color styling
      let priorityColor = '#10b981' // Green (Low)
      if (isCritical) priorityColor = '#ef4444' // Red (Critical)
      else if (isHigh) priorityColor = '#f97316' // Orange (High)
      else if (isMedium) priorityColor = '#eab308' // Yellow (Medium)

      // Category Differentiation (Distinctive SVG Icon & Ring Accent)
      const isRoadCategory =
        issue.category === 'Roads & Footpaths' ||
        issue.category?.toLowerCase().includes('road') ||
        issue.category?.toLowerCase().includes('pothole')
      const isSanitationCategory =
        issue.category === 'Sanitation & Garbage' ||
        issue.category?.toLowerCase().includes('sanitation') ||
        issue.category?.toLowerCase().includes('garbage') ||
        issue.category?.toLowerCase().includes('solid waste')

      let categoryBadgeColor = '#6457E8'
      let categorySvg = ''

      if (isRoadCategory) {
        categoryBadgeColor = '#F97316' // Road maintenance orange
        categorySvg = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 19L8 5M16 5l4 14M10 9h4M9 15h6"/>
          </svg>
        `
      } else if (isSanitationCategory) {
        categoryBadgeColor = '#10B981' // Sanitation green
        categorySvg = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        `
      } else {
        categoryBadgeColor = '#3B82F6'
        categorySvg = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        `
      }

      const outerSize = isCritical ? 34 : isHigh ? 28 : 24
      const pinHtml = `
        <div style="position: relative; width: ${outerSize}px; height: ${outerSize}px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
          ${
            isCritical
              ? `<div style="position: absolute; width: ${outerSize}px; height: ${outerSize}px; border-radius: 9999px; background-color: ${priorityColor}; opacity: 0.35;" class="animate-ping"></div>`
              : ''
          }
          ${
            isSelected
              ? `<div style="position: absolute; width: ${outerSize + 12}px; height: ${outerSize + 12}px; border-radius: 9999px; border: 2px solid #8B5CF6; box-shadow: 0 0 16px rgba(139,92,246,0.8); background: rgba(139,92,246,0.15);" class="animate-pulse"></div>`
              : ''
          }
          <div style="width: ${outerSize - 4}px; height: ${outerSize - 4}px; border-radius: 9999px; background-color: #13152E; border: 2px solid ${priorityColor}; display: flex; align-items: center; justify-content: center; color: ${categoryBadgeColor}; box-shadow: 0 0 ${
        isSelected ? '14px #8B5CF6' : isCritical ? '10px ' + priorityColor : '6px rgba(0,0,0,0.5)'
      };">
            ${categorySvg}
          </div>
        </div>
      `

      const customIcon = L.divIcon({
        className: 'custom-incident-pin',
        html: pinHtml,
        iconSize: [outerSize, outerSize],
        iconAnchor: [outerSize / 2, outerSize / 2],
      })

      const marker = L.marker([issue.latitude, issue.longitude], {
        icon: customIcon,
        zIndexOffset: isSelected ? 2000 : isCritical ? 1000 : isHigh ? 500 : 100,
      })

      const routingPath = issue.routing_path || `${issue.authority_id || 'BMC'} → ${issue.ward || 'General Ward'}`
      const popupHtml = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; font-size: 11px; padding: 6px; min-width: 240px; line-height: 1.45; color: #11162A;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <strong style="color: #6457E8; font-size: 12px; font-family: monospace;">${issue.issueId}</strong>
            <span style="color: ${priorityColor}; font-weight: 700; font-size: 10px; background: #F0F2F9; padding: 2px 6px; border-radius: 9999px; border: 1px solid #E4E7F1;">
              ${issue.priorityLevel} &bull; ${issue.priorityScore.toFixed(0)}
            </span>
          </div>
          <div style="color: #11162A; font-weight: 700; font-size: 12px; margin-bottom: 2px;">
            ${issue.category}
          </div>
          <div style="color: #65708B; font-size: 10.5px; margin-bottom: 6px;">
            ${issue.location} ${issue.ward ? `(${issue.ward})` : ''}
          </div>
          <div style="background: #F6F7FC; border: 1px solid #E4E7F1; border-radius: 6px; padding: 5px; margin-bottom: 6px; font-family: monospace; font-size: 10px; color: #4338CA;">
            <div style="font-weight: 600; font-size: 9px; color: #65708B; text-transform: uppercase;">Jurisdiction Routing:</div>
            ${routingPath}
          </div>
          <div style="color: #374151; font-size: 10.5px; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            ${issue.complaintText}
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #E4E7F1; padding-top: 6px;">
            <span style="color: #65708B;">SLA: <strong style="color: #11162A;">${issue.slaHours}h</strong></span>
            <span style="color: #6457E8; font-weight: 600;">${issue.status}</span>
          </div>
        </div>
      `

      marker.bindPopup(popupHtml)

      marker.on('click', () => {
        map.flyTo([issue.latitude, issue.longitude], 15, {
          duration: 0.85,
          easeLinearity: 0.25,
        })
        if (onSelectIssue) onSelectIssue(issue)
      })

      ml.addLayer(marker)
    })
  }, [
    issues,
    hotspots,
    selectedIssue,
    selectedHotspot,
    layerMode,
    displayHotspotBoundaries,
    currentZoom,
    onSelectIssue,
    onSelectHotspot,
  ])

  // 5. Framing Active Incident Cluster Without Empty Sea Space
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || selectedIssue) return

    const validPoints: [number, number][] = []

    issues.forEach((issue) => {
      if (
        typeof issue.latitude === 'number' &&
        typeof issue.longitude === 'number' &&
        !isNaN(issue.latitude) &&
        !isNaN(issue.longitude)
      ) {
        validPoints.push([issue.latitude, issue.longitude])
      }
    })

    if (validPoints.length > 0) {
      const bounds = L.latLngBounds(validPoints)
      map.fitBounds(bounds, {
        padding: [36, 36],
        maxZoom: 14,
        animate: hasFittedInitialBoundsRef.current,
      })
      hasFittedInitialBoundsRef.current = true
    }
  }, [issues, selectedIssue])

  // 6. Smooth Camera FlyTo on selectedIssue change
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !selectedIssue) return

    if (selectedIssue.latitude && selectedIssue.longitude) {
      map.flyTo([selectedIssue.latitude, selectedIssue.longitude], 15, {
        duration: 0.85,
        easeLinearity: 0.25,
      })
    }
  }, [selectedIssue])

  return (
    <div className="relative isolate z-0 layer-map-container h-full w-full overflow-hidden rounded-lg border border-[#212348] bg-[#10162A]">
      {/* Floating Tactical Layer Controls (Positioned cleanly below the top navigation HUD) */}
      <div className="absolute top-20 left-4 z-[400] bg-[#13152E]/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-white text-[11px] flex items-center gap-3 shadow-md pointer-events-auto">
        <span className="text-[10px] uppercase font-bold text-[#8B5CF6] tracking-wider">GIS Layers:</span>
        <label className="flex items-center gap-1.5 cursor-pointer hover:text-white text-slate-300">
          <input
            type="checkbox"
            checked={wardsVisible}
            onChange={(e) => setWardsVisible(e.target.checked)}
            className="rounded border-slate-600 accent-[#8B5CF6] cursor-pointer"
          />
          <span>Admin Wards</span>
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer hover:text-white text-slate-300">
          <input
            type="checkbox"
            checked={subWardsVisible}
            onChange={(e) => setSubWardsVisible(e.target.checked)}
            className="rounded border-slate-600 accent-[#6457E8] cursor-pointer"
          />
          <span>CIVILENS Sub-Wards</span>
        </label>
      </div>

      <div ref={mapContainerRef} className={className} />
    </div>
  )
}
