import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import { Issue, HotspotInfo } from '../../types'

export type MapLayerMode = 'markers' | 'clusters' | 'heatmap' | 'hotspots'

interface CivicMapProps {
  issues: Issue[]
  hotspots?: HotspotInfo[]
  selectedIssue?: Issue | null
  onSelectIssue?: (issue: Issue) => void
  selectedHotspot?: HotspotInfo | null
  onSelectHotspot?: (hotspot: HotspotInfo) => void
  layerMode?: MapLayerMode
  showHotspotBoundaries?: boolean
  showHotspotCircles?: boolean
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
  className = 'h-full w-full',
}) => {
  const displayHotspotBoundaries =
    showHotspotCircles !== undefined ? showHotspotCircles : showHotspotBoundaries
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const markersLayerRef = useRef<L.LayerGroup | null>(null)
  const hotspotsLayerRef = useRef<L.LayerGroup | null>(null)
  const heatmapLayerRef = useRef<L.LayerGroup | null>(null)
  const clustersLayerRef = useRef<L.LayerGroup | null>(null)
  const hasFittedInitialBoundsRef = useRef<boolean>(false)

  // 1. Initialize Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      // Centered on the active urban corridor (Vidyavihar / Ghatkopar / Kurla) to eliminate empty sea space
      const map = L.map(mapContainerRef.current, {
        center: [19.0728, 72.8998],
        zoom: 13,
        minZoom: 10,
        maxZoom: 18,
        zoomControl: false,
        attributionControl: false,
      })

      // Elegant Zoom Controls top-right
      L.control.zoom({ position: 'topright' }).addTo(map)

      // Professional ESRI Dark Gray Canvas (High contrast roads, zero watermark, dark graphite)
      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 16,
          attribution: 'Tiles &copy; Esri, DeLorme, NAVTEQ',
        }
      ).addTo(map)

      // ESRI Dark Gray Reference Labels Overlay (Crisp street names & landmarks)
      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        {
          maxZoom: 16,
          opacity: 0.9,
        }
      ).addTo(map)

      // Layer Groups
      const ml = L.layerGroup().addTo(map)
      const hl = L.layerGroup().addTo(map)
      const hml = L.layerGroup().addTo(map)
      const cl = L.layerGroup().addTo(map)

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

  // 2. Render Layers based on layerMode and state
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

        // Safely extract coordinates (supports both { lat, lng } and [lat, lng])
        const lat = typeof h.center?.lat === 'number' ? h.center.lat : Array.isArray(h.center) ? Number(h.center[0]) : null
        const lng = typeof h.center?.lng === 'number' ? h.center.lng : Array.isArray(h.center) ? Number(h.center[1]) : null
        if (lat === null || lng === null || isNaN(lat) || isNaN(lng)) return

        // Hotspot Boundary Circle
        const circle = L.circle([lat, lng], {
          radius: h.radiusMeters || 600,
          color: color,
          fillColor: color,
          fillOpacity: isSelected ? 0.28 : 0.14,
          weight: isSelected ? 2.5 : 1.5,
          dashArray: '5, 5',
        })

        // Centroid Radar Beacon
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
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; margin-top: 4px; border-top: 1px solid #1e2638; padding-top: 3px;">
              <span>Growth: <strong style="color: ${h.growthRate > 0 ? '#f43f5e' : '#10b981'};">${h.growthRate > 0 ? '+' : ''}${h.growthRate}%</strong></span>
              <span>Avg Pri: <strong style="color: #38bdf8;">${h.averagePriority.toFixed(0)}</strong></span>
            </div>
          </div>
        `

        circle.bindTooltip(tooltipHtml, { className: 'leaflet-dark-tooltip' })
        beacon.bindTooltip(tooltipHtml, { className: 'leaflet-dark-tooltip' })

        const handleHotspotClick = () => {
          map.flyTo([lat, lng], 14, { duration: 1.2, easeLinearity: 0.25 })
          if (onSelectHotspot) onSelectHotspot(h)
        }

        circle.on('click', handleHotspotClick)
        beacon.on('click', handleHotspotClick)

        hl.addLayer(circle)
        hl.addLayer(beacon)
      })
    }

    // -----------------------------------------------------------------
    // B. HEATMAP LAYER (Smooth Continuous Density & Priority Heat)
    // -----------------------------------------------------------------
    if (layerMode === 'heatmap') {
      issues.forEach((issue) => {
        if (!issue.latitude || !issue.longitude) return

        const isCrit = issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
        const isHigh = issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
        const heatColor = isCrit ? '#EF4444' : isHigh ? '#F97316' : '#6457E8'
        const heatRadius = isCrit ? 600 : isHigh ? 450 : 320

        const heatCircle = L.circle([issue.latitude, issue.longitude], {
          radius: heatRadius,
          color: heatColor,
          fillColor: heatColor,
          fillOpacity: 0.24,
          weight: 0,
        })

        heatCircle.on('click', () => {
          map.flyTo([issue.latitude, issue.longitude], 15, { duration: 1.0 })
          if (onSelectIssue) onSelectIssue(issue)
        })

        hml.addLayer(heatCircle)
      })
      return
    }

    // -----------------------------------------------------------------
    // C. MARKER CLUSTERING LAYER
    // -----------------------------------------------------------------
    if (layerMode === 'clusters') {
      // Spatial distance grid clustering
      const clusterThreshold = 0.018 // ~2km spatial threshold
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
        const size = Math.min(52, Math.max(34, 28 + clus.items.length * 3))

        const clusterIcon = L.divIcon({
          className: 'custom-cluster-wrapper',
          html: `
            <div class="tactical-cluster-icon ${clusterClass}" style="width: ${size}px; height: ${size}px;">
              <span>${clus.items.length}</span>
            </div>
          `,
          iconSize: [size, size],
          iconAnchor: [size / 2, size / 2],
        })

        const marker = L.marker([clus.centerLat, clus.centerLng], { icon: clusterIcon })

        marker.on('click', () => {
          if (clus.items.length === 1) {
            map.flyTo([clus.centerLat, clus.centerLng], 15, { duration: 1.0 })
            if (onSelectIssue) onSelectIssue(clus.items[0])
          } else {
            map.setView([clus.centerLat, clus.centerLng], map.getZoom() + 2, { animate: true })
          }
        })

        marker.bindTooltip(
          `<div style="font-family: monospace; font-size: 11px;">
            Cluster: <strong>${clus.items.length} incidents</strong><br/>
            Highest Priority: <strong style="color: ${hasCritical ? '#ef4444' : '#f97316'};">${hasCritical ? 'CRITICAL' : hasHigh ? 'HIGH' : 'STANDARD'}</strong>
          </div>`,
          { className: 'leaflet-dark-tooltip' }
        )

        cl.addLayer(marker)
      })
      return
    }

    // -----------------------------------------------------------------
    // D. ISSUE MARKERS (Priority-Based Visual Emphasis)
    // -----------------------------------------------------------------
    issues.forEach((issue) => {
      if (!issue.latitude || !issue.longitude) return

      const isCritical = issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80
      const isHigh = issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65
      const isMedium = issue.priorityLevel === 'MEDIUM' || issue.priorityScore >= 40
      const isSelected = selectedIssue?.issueId === issue.issueId

      // Priority color & dimensional sizing
      let markerColor = '#10b981' // Green
      let outerSize = 22
      let coreSize = 12

      if (isCritical) {
        markerColor = '#ef4444' // Red
        outerSize = 34
        coreSize = 16
      } else if (isHigh) {
        markerColor = '#f97316' // Orange
        outerSize = 26
        coreSize = 14
      } else if (isMedium) {
        markerColor = '#eab308' // Yellow
        outerSize = 22
        coreSize = 12
      }

      // Tactical SVG Icon with strong visual emphasis on critical incidents and selected issue
      const customIcon = L.divIcon({
        className: 'custom-incident-pin',
        html: `
          <div style="position: relative; width: ${outerSize}px; height: ${outerSize}px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
            ${
              isCritical
                ? `<div style="position: absolute; width: ${outerSize}px; height: ${outerSize}px; border-radius: 9999px; background-color: ${markerColor}; opacity: 0.35;" class="animate-ping"></div>`
                : ''
            }
            ${
              isSelected
                ? `<div style="position: absolute; width: ${outerSize + 14}px; height: ${outerSize + 14}px; border-radius: 9999px; border: 2px solid #8B5CF6; box-shadow: 0 0 16px rgba(139,92,246,0.8); background: rgba(139,92,246,0.15);" class="animate-pulse"></div>`
                : ''
            }
            <div style="width: ${coreSize}px; height: ${coreSize}px; border-radius: 9999px; background-color: ${markerColor}; border: 2px solid #080a0f; box-shadow: 0 0 ${isSelected ? '18px #8B5CF6' : isCritical ? '14px ' + markerColor : '8px ' + markerColor};"></div>
          </div>
        `,
        iconSize: [outerSize, outerSize],
        iconAnchor: [outerSize / 2, outerSize / 2],
      })

      const marker = L.marker([issue.latitude, issue.longitude], {
        icon: customIcon,
        zIndexOffset: isSelected ? 2000 : isCritical ? 1000 : isHigh ? 500 : 100,
      })

      // Popup Content (Clean, readable Inter styling)
      const popupHtml = `
        <div style="font-family: 'Inter', sans-serif; font-size: 12px; padding: 6px; min-width: 230px; line-height: 1.4;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <strong style="color: #A78BFA; font-size: 12px; font-family: monospace;">${issue.issueId}</strong>
            <span style="color: ${markerColor}; font-weight: 600; font-size: 11px; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 9999px;">
              ${issue.priorityLevel} &bull; ${issue.priorityScore.toFixed(0)}
            </span>
          </div>
          <div style="color: #ffffff; font-weight: 600; font-size: 13px; margin-bottom: 2px;">${issue.category}</div>
          <div style="color: #94a3b8; font-size: 11px; margin-bottom: 6px;">${issue.location} ${issue.ward ? `(${issue.ward})` : ''}</div>
          <div style="color: #cbd5e1; font-size: 11px; line-height: 1.4; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            ${issue.complaintText}
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 6px;">
            <span>SLA: <strong style="color: #cbd5e1;">${issue.slaHours}h</strong></span>
            <span style="color: #A78BFA; font-weight: 500;">${issue.status}</span>
          </div>
        </div>
      `

      marker.bindPopup(popupHtml)

      marker.on('click', () => {
        map.flyTo([issue.latitude, issue.longitude], 15, {
          duration: 1.2,
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
    onSelectIssue,
    onSelectHotspot,
  ])

  // 3. Optimal Viewport Bounds Fitting (Framing active incident cluster without empty sea)
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    // If an issue is already explicitly selected by the user, keep focus on it
    if (selectedIssue) return

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

    hotspots.forEach((h) => {
      const lat =
        typeof h.center?.lat === 'number'
          ? h.center.lat
          : Array.isArray(h.center)
          ? Number(h.center[0])
          : null
      const lng =
        typeof h.center?.lng === 'number'
          ? h.center.lng
          : Array.isArray(h.center)
          ? Number(h.center[1])
          : null
      if (lat !== null && lng !== null && !isNaN(lat) && !isNaN(lng)) {
        validPoints.push([lat, lng])
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
  }, [issues, hotspots, selectedIssue])

  // 4. Smooth Camera FlyTo on selectedIssue change
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !selectedIssue) return

    if (selectedIssue.latitude && selectedIssue.longitude) {
      map.flyTo([selectedIssue.latitude, selectedIssue.longitude], 15, {
        duration: 1.2,
        easeLinearity: 0.25,
      })
    }
  }, [selectedIssue])

  return (
    <div className="relative isolate z-0 layer-map-container h-full w-full overflow-hidden rounded-lg border border-[#212348] bg-[#10162A]">
      <div ref={mapContainerRef} className={className} />
    </div>
  )
}

export default CivicMap
