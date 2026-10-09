import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import { Issue, HotspotInfo } from '../../types'

interface CivicMapProps {
  issues: Issue[]
  hotspots?: HotspotInfo[]
  selectedIssue?: Issue | null
  onSelectIssue?: (issue: Issue) => void
  className?: string
  showHotspotCircles?: boolean
}

export const CivicMap: React.FC<CivicMapProps> = ({
  issues,
  hotspots = [],
  selectedIssue,
  onSelectIssue,
  className = 'h-full w-full',
  showHotspotCircles = true,
}) => {
  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const layerGroupRef = useRef<L.LayerGroup | null>(null)
  const hotspotLayerGroupRef = useRef<L.LayerGroup | null>(null)

  useEffect(() => {
    if (!mapContainerRef.current) return

    // Initialize Leaflet Map centered on Mumbai (default center Vidyavihar/Kurla region)
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [19.076, 72.885],
        zoom: 12,
        zoomControl: false,
        attributionControl: false,
      })

      // Add Zoom Control to top-right
      L.control.zoom({ position: 'topright' }).addTo(map)

      // Tactical Dark Matter Carto Tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map)

      const lg = L.layerGroup().addTo(map)
      const hlg = L.layerGroup().addTo(map)
      layerGroupRef.current = lg
      hotspotLayerGroupRef.current = hlg
      mapInstanceRef.current = map
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [])

  // Render Issue Markers and Hotspot Circles
  useEffect(() => {
    const map = mapInstanceRef.current
    const lg = layerGroupRef.current
    const hlg = hotspotLayerGroupRef.current
    if (!map || !lg || !hlg) return

    lg.clearLayers()
    hlg.clearLayers()

    // 1. Render DBSCAN Hotspot Circles
    if (showHotspotCircles && hotspots.length > 0) {
      hotspots.forEach((h) => {
        const circle = L.circle([h.center.lat, h.center.lng], {
          radius: h.radiusMeters || 500,
          color: h.hotspotLevel === 'CRITICAL' ? '#ef4444' : '#f97316',
          fillColor: h.hotspotLevel === 'CRITICAL' ? '#ef4444' : '#f97316',
          fillOpacity: 0.15,
          weight: 1.5,
          dashArray: '4, 4',
        })

        circle.bindTooltip(
          `<div style="font-family: monospace; font-size: 11px;">
            <strong style="color: #f97316;">${h.hotspotId}</strong><br/>
            Density: ${h.issueCount} issues | Growth: ${h.growthRate > 0 ? '+' : ''}${h.growthRate}%
          </div>`,
          { className: 'leaflet-dark-tooltip' }
        )
        hlg.addLayer(circle)
      })
    }

    // 2. Render Incident Markers
    const bounds: L.LatLngTuple[] = []

    issues.forEach((issue) => {
      if (!issue.latitude || !issue.longitude) return
      bounds.push([issue.latitude, issue.longitude])

      // Determine marker color
      let markerColor = '#10b981' // Green (Low/Resolved)
      let ringAnimation = ''

      if (issue.priorityLevel === 'CRITICAL' || issue.priorityScore >= 80) {
        markerColor = '#ef4444' // Red
        ringAnimation = 'animate-ping'
      } else if (issue.priorityLevel === 'HIGH' || issue.priorityScore >= 65) {
        markerColor = '#f97316' // Orange
      } else if (issue.priorityLevel === 'MEDIUM' || issue.priorityScore >= 40) {
        markerColor = '#eab308' // Yellow
      }

      // Tactical SVG Icon
      const customIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `
          <div style="position: relative; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
            ${
              ringAnimation
                ? `<div style="position: absolute; width: 28px; height: 28px; border-radius: 9999px; background-color: ${markerColor}; opacity: 0.35;" class="${ringAnimation}"></div>`
                : ''
            }
            <div style="width: 14px; height: 14px; border-radius: 9999px; background-color: ${markerColor}; border: 2px solid #080a0f; box-shadow: 0 0 10px ${markerColor};"></div>
          </div>
        `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      })

      const marker = L.marker([issue.latitude, issue.longitude], { icon: customIcon })

      const popupHtml = `
        <div style="font-family: monospace; font-size: 11px; padding: 4px; min-width: 190px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <strong style="color: #06b6d4; font-size: 12px;">${issue.issueId}</strong>
            <span style="color: ${markerColor}; font-weight: bold; font-size: 10px; border: 1px solid ${markerColor}; padding: 1px 4px; border-radius: 3px;">
              ${issue.priorityLevel} (${issue.priorityScore.toFixed(0)})
            </span>
          </div>
          <div style="color: #e2e8f0; font-weight: bold; margin-bottom: 2px;">${issue.category}</div>
          <div style="color: #94a3b8; font-size: 10px; margin-bottom: 4px;">${issue.location} (${issue.ward})</div>
          <div style="color: #cbd5e1; font-family: sans-serif; font-size: 10px; line-height: 1.3; margin-bottom: 6px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            ${issue.complaintText}
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b; border-top: 1px solid #1e2638; padding-top: 4px;">
            <span>SLA: ${issue.slaHours}h</span>
            <span style="color: #06b6d4;">${issue.status}</span>
          </div>
        </div>
      `

      marker.bindPopup(popupHtml)

      marker.on('click', () => {
        if (onSelectIssue) onSelectIssue(issue)
      })

      lg.addLayer(marker)
    })

    // Focus on selected issue if passed
    if (selectedIssue && selectedIssue.latitude && selectedIssue.longitude) {
      map.setView([selectedIssue.latitude, selectedIssue.longitude], 15, { animate: true })
    }
  }, [issues, hotspots, selectedIssue, showHotspotCircles, onSelectIssue])

  return (
    <div className="relative h-full w-full overflow-hidden rounded-lg border border-slate-800 bg-[#0a0d14]">
      <div ref={mapContainerRef} className={className} />
    </div>
  )
}
