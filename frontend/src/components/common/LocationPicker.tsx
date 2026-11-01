import React, { useState, useEffect, useRef } from 'react'
import L from 'leaflet'
import {
  MapPin,
  Navigation,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  Search,
  Crosshair,
  Compass,
  Info
} from 'lucide-react'
import {
  MUMBAI_NAVI_MUMBAI_BOUNDS,
  OUT_OF_BOUNDS_ERROR,
  isWithinSupportedRegion,
  POPULAR_CIVIC_LOCALITIES,
  LandmarkPreset
} from '../../config/geo'
import { api } from '../../services/api'

export interface LocationData {
  address: string
  latitude: number | null
  longitude: number | null
  ward: string
  method: 'gps' | 'manual'
  isValid: boolean
}

interface LocationPickerProps {
  value: LocationData
  onChange: (loc: LocationData) => void
  disabled?: boolean
  error?: string | null
}

export const LocationPicker: React.FC<LocationPickerProps> = ({
  value,
  onChange,
  disabled = false,
  error: externalError,
}) => {
  const [activeTab, setActiveTab] = useState<'gps' | 'manual'>('gps')
  const [isDetecting, setIsDetecting] = useState(false)
  const [locationStatus, setLocationStatus] = useState<string | null>(null)
  const [boundaryError, setBoundaryError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Array<{ name: string; ward: string; latitude: number; longitude: number }>>([])
  const [isSearching, setIsSearching] = useState(false)

  const mapContainerRef = useRef<HTMLDivElement | null>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)
  const markerRef = useRef<L.Marker | null>(null)

  // Initialize interactive Leaflet map picker
  useEffect(() => {
    if (!mapContainerRef.current) return

    if (!mapInstanceRef.current) {
      // Default center: Central Mumbai corridor
      const initialLat = value.latitude ?? 19.0760
      const initialLng = value.longitude ?? 72.8850

      const southWest = L.latLng(MUMBAI_NAVI_MUMBAI_BOUNDS.minLat - 0.05, MUMBAI_NAVI_MUMBAI_BOUNDS.minLng - 0.05)
      const northEast = L.latLng(MUMBAI_NAVI_MUMBAI_BOUNDS.maxLat + 0.05, MUMBAI_NAVI_MUMBAI_BOUNDS.maxLng + 0.05)
      const bounds = L.latLngBounds(southWest, northEast)

      const map = L.map(mapContainerRef.current, {
        center: [initialLat, initialLng],
        zoom: value.latitude && value.longitude ? 14 : 12,
        minZoom: 10,
        maxZoom: 18,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0,
        zoomControl: false,
        attributionControl: false,
      })

      L.control.zoom({ position: 'topright' }).addTo(map)

      // Tactical Dark Gray Canvas (consistent with CIVILENS GIS map)
      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16 }
      ).addTo(map)

      L.tileLayer(
        'https://services.arcgisonline.com/arcgis/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 16, opacity: 0.9 }
      ).addTo(map)

      // Map click handler: allows user to click anywhere in Mumbai / Navi Mumbai
      map.on('click', async (e: L.LeafletMouseEvent) => {
        const { lat, lng } = e.latlng
        await handleCoordinatesSelected(lat, lng, 'manual')
      })

      mapInstanceRef.current = map
    }

    // Update marker on map if value changes
    const map = mapInstanceRef.current
    if (map) {
      if (value.latitude && value.longitude) {
        const pinIcon = L.divIcon({
          className: 'civic-map-picker-pin',
          html: `
            <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
              <div style="position: absolute; width: 32px; height: 32px; border-radius: 9999px; background-color: #6457E8; opacity: 0.35;" class="animate-ping"></div>
              <div style="width: 16px; height: 16px; border-radius: 9999px; background-color: #6457E8; border: 2.5px solid #FFFFFF; box-shadow: 0 0 12px #6457E8;"></div>
            </div>
          `,
          iconSize: [32, 32],
          iconAnchor: [16, 16],
        })

        if (!markerRef.current) {
          markerRef.current = L.marker([value.latitude, value.longitude], {
            icon: pinIcon,
            draggable: true,
          }).addTo(map)

          markerRef.current.on('dragend', async (ev: any) => {
            const pos = ev.target.getLatLng()
            await handleCoordinatesSelected(pos.lat, pos.lng, 'manual')
          })
        } else {
          markerRef.current.setLatLng([value.latitude, value.longitude])
        }

        map.setView([value.latitude, value.longitude], Math.max(map.getZoom(), 13), { animate: true })
      } else if (markerRef.current) {
        markerRef.current.remove()
        markerRef.current = null
      }
    }

    return () => {
      // Leaflet cleanup happens on unmount
    }
  }, [value.latitude, value.longitude])

  // Process selected coordinates (from GPS, click on map, or search chip)
  const handleCoordinatesSelected = async (
    lat: number,
    lng: number,
    method: 'gps' | 'manual'
  ) => {
    const latRounded = Number(lat.toFixed(5))
    const lngRounded = Number(lng.toFixed(5))

    // 1. Boundary check against Mumbai & Navi Mumbai
    if (!isWithinSupportedRegion(latRounded, lngRounded)) {
      setBoundaryError(OUT_OF_BOUNDS_ERROR)
      setLocationStatus(null)
      onChange({
        ...value,
        latitude: latRounded,
        longitude: lngRounded,
        method,
        isValid: false,
      })
      return
    }

    setBoundaryError(null)
    setLocationStatus('Resolving locality and municipal ward...')

    try {
      // Call backend reverse-geocode for ward & clean address
      const res = await api.reverseGeocode(latRounded, lngRounded)
      if (res.valid && res.address) {
        const derivedWard = res.ward || 'N-Ward'
        onChange({
          address: res.address,
          latitude: latRounded,
          longitude: lngRounded,
          ward: derivedWard,
          method,
          isValid: true,
        })
        setLocationStatus(`Locked: ${latRounded}° N, ${lngRounded}° E • Ward: ${derivedWard}`)
      } else {
        // Fallback
        const fallbackAddress = `Coordinates: ${latRounded}, ${lngRounded}`
        onChange({
          address: value.address || fallbackAddress,
          latitude: latRounded,
          longitude: lngRounded,
          ward: 'N-Ward',
          method,
          isValid: true,
        })
        setLocationStatus(`Locked: ${latRounded}° N, ${lngRounded}° E`)
      }
    } catch {
      onChange({
        address: value.address || `GPS: ${latRounded}, ${lngRounded}`,
        latitude: latRounded,
        longitude: lngRounded,
        ward: value.ward || 'N-Ward',
        method,
        isValid: true,
      })
      setLocationStatus(`Locked: ${latRounded}° N, ${lngRounded}° E`)
    }
  }

  // OPTION A: Browser native Geolocation API
  const handleDetectGPS = () => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      setBoundaryError('Geolocation is not supported by your browser. Please select location manually.')
      setActiveTab('manual')
      return
    }

    setIsDetecting(true)
    setBoundaryError(null)
    setLocationStatus('Acquiring high-accuracy GPS fix from device...')

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        setIsDetecting(false)
        const lat = pos.coords.latitude
        const lng = pos.coords.longitude
        await handleCoordinatesSelected(lat, lng, 'gps')
      },
      (err) => {
        setIsDetecting(false)
        setLocationStatus(null)
        let msg = 'Unable to retrieve your location.'
        if (err.code === 1) {
          msg = 'Location permission denied. Please choose your location on the map below.'
        } else if (err.code === 2) {
          msg = 'GPS position unavailable. Please pick your location manually.'
        } else if (err.code === 3) {
          msg = 'GPS request timed out. Please enter location manually.'
        }
        setBoundaryError(msg)
        // Automatically open manual map selection so citizen is never blocked
        setActiveTab('manual')
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )
  }

  // Search input handler
  const handleSearchChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const q = e.target.value
    setSearchQuery(q)
    if (!q.trim()) {
      setSearchResults([])
      return
    }

    setIsSearching(true)
    try {
      const results = await api.searchLocations(q.trim(), 5)
      setSearchResults(results)
    } catch {
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  // Selection from Preset chips or search results
  const handleSelectPreset = async (preset: { name: string; ward: string; latitude: number; longitude: number }) => {
    setSearchQuery(preset.name)
    setSearchResults([])
    await handleCoordinatesSelected(preset.latitude, preset.longitude, 'manual')
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([preset.latitude, preset.longitude], 14, { duration: 1.0 })
    }
  }

  return (
    <div className="space-y-3 font-sans">
      {/* Privacy Explanation & Guidance */}
      <div className="flex items-start gap-2 bg-[#6457E8]/5 border border-[#6457E8]/20 rounded-xl p-3 text-xs text-[#11162A]">
        <Info className="w-4 h-4 text-[#6457E8] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[#6457E8]">Geographic Verification Required:</span>{' '}
          <span className="text-[#65708B]">
            Your location helps place the complaint accurately on the CIVILENS GIS map. Complaints are restricted to Mumbai and Navi Mumbai municipal jurisdictions.
          </span>
        </div>
      </div>

      {/* Option Selection Header */}
      <div className="flex items-center gap-2 border-b border-[#E4E7F1] pb-2">
        <button
          type="button"
          onClick={() => setActiveTab('gps')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            activeTab === 'gps'
              ? 'bg-[#13152E] text-white shadow-xs'
              : 'bg-white text-[#65708B] hover:text-[#11162A] hover:bg-slate-100'
          }`}
        >
          <Navigation className="w-3.5 h-3.5" />
          <span>Option A: GPS Location</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('manual')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition cursor-pointer ${
            activeTab === 'manual'
              ? 'bg-[#13152E] text-white shadow-xs'
              : 'bg-white text-[#65708B] hover:text-[#11162A] hover:bg-slate-100'
          }`}
        >
          <Compass className="w-3.5 h-3.5" />
          <span>Option B: Map Picker & Search</span>
        </button>
      </div>

      {/* OPTION A: Detect My Location Button */}
      {activeTab === 'gps' && (
        <div className="bg-[#F0F2F9] rounded-xl border border-[#E4E7F1] p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <div className="text-xs font-bold text-[#11162A] flex items-center gap-1.5">
              <Crosshair className="w-4 h-4 text-[#6457E8]" />
              <span>Use High-Accuracy GPS</span>
            </div>
            <p className="text-[11px] text-[#65708B] mt-0.5">
              Query browser coordinates to pinpoint the defect location automatically.
            </p>
          </div>

          <button
            type="button"
            onClick={handleDetectGPS}
            disabled={isDetecting || disabled}
            className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-[#6457E8] hover:bg-[#5145CF] active:scale-98 text-white text-xs font-bold transition flex items-center justify-center gap-2 cursor-pointer shadow-sm shrink-0 disabled:opacity-50"
          >
            {isDetecting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Detecting GPS...</span>
              </>
            ) : (
              <>
                <span>📍 Detect My Location</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* OPTION B: Manual Search & Preset Chips */}
      {activeTab === 'manual' && (
        <div className="space-y-2.5">
          {/* Autocomplete Search Field */}
          <div className="relative">
            <Search className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search Mumbai / Navi Mumbai locality (e.g. Vashi, Ghatkopar, Bandra, Kharghar)..."
              value={searchQuery}
              onChange={handleSearchChange}
              disabled={disabled}
              className="w-full pl-10 pr-4 py-2 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] bg-white transition"
            />
            {isSearching && (
              <Loader2 className="w-4 h-4 text-[#6457E8] animate-spin absolute right-3 top-1/2 -translate-y-1/2" />
            )}

            {/* Search Suggestions Dropdown */}
            {searchResults.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1 z-50 bg-white border border-[#E4E7F1] rounded-xl shadow-lg overflow-hidden max-h-48 overflow-y-auto">
                {searchResults.map((item, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectPreset(item)}
                    className="w-full text-left px-3.5 py-2 text-xs hover:bg-slate-50 flex items-center justify-between border-b border-slate-100 last:border-b-0 cursor-pointer"
                  >
                    <span className="font-semibold text-[#11162A]">{item.name}</span>
                    <span className="text-[10px] text-[#65708B] font-mono px-2 py-0.5 rounded bg-slate-100">
                      {item.ward}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Quick preset chips */}
          <div>
            <span className="text-[10px] font-semibold text-[#65708B] uppercase tracking-wider block mb-1.5">
              Popular Jurisdictions (Click to place pin):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {POPULAR_CIVIC_LOCALITIES.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset({
                    name: preset.name,
                    ward: preset.ward,
                    latitude: preset.lat,
                    longitude: preset.lng,
                  })}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-white hover:bg-[#6457E8]/10 hover:text-[#6457E8] border border-[#E4E7F1] text-[#11162A] transition cursor-pointer"
                >
                  {preset.name.split(',')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Leaflet Map Picker Canvas */}
      <div className="rounded-xl border border-[#E4E7F1] overflow-hidden shadow-xs relative">
        <div
          ref={mapContainerRef}
          className="w-full h-52 sm:h-60 bg-[#10162A]"
          style={{ isolation: 'isolate' }}
        />
        <div className="absolute top-2 left-2 z-[400] bg-white/90 backdrop-blur-xs px-2.5 py-1 rounded-md border border-[#E4E7F1] text-[10px] text-[#11162A] font-semibold shadow-xs flex items-center gap-1.5">
          <Crosshair className="w-3 h-3 text-[#6457E8]" />
          <span>Click anywhere on the map to pinpoint exact defect location</span>
        </div>
      </div>

      {/* Confirmed / Selected Readable Address Input */}
      <div>
        <label className="block text-xs font-semibold text-[#11162A] mb-1">
          Confirmed Civic Address / Locality Landmark
        </label>
        <div className="relative">
          <MapPin className="w-4 h-4 text-[#6457E8] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            required
            placeholder="e.g. Near Vidyavihar Station West or Vashi Sector 17"
            value={value.address}
            onChange={(e) => {
              const newAddr = e.target.value
              onChange({
                ...value,
                address: newAddr,
                isValid: Boolean(newAddr.trim() && value.latitude && value.longitude && isWithinSupportedRegion(value.latitude, value.longitude)),
              })
            }}
            disabled={disabled}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] bg-white transition"
          />
        </div>
      </div>

      {/* Active Validation & Verification Status Banner */}
      {boundaryError && (
        <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-3 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
          <span className="font-medium">{boundaryError}</span>
        </div>
      )}

      {externalError && !boundaryError && (
        <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl p-3 text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
          <span className="font-medium">{externalError}</span>
        </div>
      )}

      {value.isValid && value.latitude && value.longitude && (
        <div className="flex items-center justify-between bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl px-3 py-2 text-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span className="font-semibold">
              Location Verified: {value.latitude.toFixed(4)}° N, {value.longitude.toFixed(4)}° E
            </span>
          </div>
          <span className="font-mono text-[11px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-900">
            {value.ward || 'Municipal Ward'} ({value.method.toUpperCase()})
          </span>
        </div>
      )}
    </div>
  )
}
