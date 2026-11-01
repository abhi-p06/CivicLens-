/**
 * Configurable Geographic Boundary: Mumbai & Navi Mumbai Region
 * Ensures coordinates and complaint filings are strictly validated within supported boundaries.
 */

export interface GeoBounds {
  region: string
  minLat: number
  maxLat: number
  minLng: number
  maxLng: number
}

export const MUMBAI_NAVI_MUMBAI_BOUNDS: GeoBounds = {
  region: 'Mumbai & Navi Mumbai',
  minLat: 18.85,
  maxLat: 19.33,
  minLng: 72.75,
  maxLng: 73.18,
}

export const OUT_OF_BOUNDS_ERROR =
  'CIVILENS currently supports complaints from Mumbai and Navi Mumbai only.'

export function isWithinSupportedRegion(
  lat: number,
  lng: number,
  bounds: GeoBounds = MUMBAI_NAVI_MUMBAI_BOUNDS
): boolean {
  if (typeof lat !== 'number' || typeof lng !== 'number' || isNaN(lat) || isNaN(lng)) {
    return false
  }
  return (
    lat >= bounds.minLat &&
    lat <= bounds.maxLat &&
    lng >= bounds.minLng &&
    lng <= bounds.maxLng
  )
}

export interface LandmarkPreset {
  name: string
  ward: string
  lat: number
  lng: number
  zone: 'Mumbai' | 'Navi Mumbai'
}

export const POPULAR_CIVIC_LOCALITIES: LandmarkPreset[] = [
  // Mumbai
  { name: 'Somaiya Vidyavihar, Vidyavihar East', ward: 'N-Ward', lat: 19.0728, lng: 72.8998, zone: 'Mumbai' },
  { name: 'LBS Marg, Ghatkopar West', ward: 'N-Ward', lat: 19.0911, lng: 72.9154, zone: 'Mumbai' },
  { name: 'Kurla West Station Road', ward: 'L-Ward', lat: 19.0655, lng: 72.871, zone: 'Mumbai' },
  { name: 'Linking Road, Bandra West', ward: 'H/West', lat: 19.0601, lng: 72.8361, zone: 'Mumbai' },
  { name: 'Andheri East Metro Junction', ward: 'K/East', lat: 19.1197, lng: 72.8464, zone: 'Mumbai' },
  { name: 'Dadar TT Circle', ward: 'G/North', lat: 19.0178, lng: 72.8478, zone: 'Mumbai' },
  { name: 'Dharavi 90 Feet Road', ward: 'G/North', lat: 19.0435, lng: 72.8562, zone: 'Mumbai' },
  { name: 'Powai Hiranandani', ward: 'S-Ward', lat: 19.1176, lng: 72.906, zone: 'Mumbai' },
  { name: 'Chembur Naka', ward: 'M/West', lat: 19.0622, lng: 72.8974, zone: 'Mumbai' },
  { name: 'Borivali West Station Road', ward: 'R/Central', lat: 19.2307, lng: 72.8567, zone: 'Mumbai' },

  // Navi Mumbai
  { name: 'Sector 17, Vashi, Navi Mumbai', ward: 'NMMC Vashi', lat: 19.0771, lng: 72.9986, zone: 'Navi Mumbai' },
  { name: 'Nerul West, Navi Mumbai', ward: 'NMMC Nerul', lat: 19.033, lng: 73.0197, zone: 'Navi Mumbai' },
  { name: 'CBD Belapur, Navi Mumbai', ward: 'NMMC Belapur', lat: 19.0144, lng: 73.038, zone: 'Navi Mumbai' },
  { name: 'Utsav Chowk, Kharghar, Navi Mumbai', ward: 'CIDCO Kharghar', lat: 19.0473, lng: 73.0699, zone: 'Navi Mumbai' },
  { name: 'Panvel Bus Depot, Navi Mumbai', ward: 'PMC Panvel', lat: 18.9894, lng: 73.1175, zone: 'Navi Mumbai' },
  { name: 'Airoli Knowledge Park, Navi Mumbai', ward: 'NMMC Airoli', lat: 19.1579, lng: 72.9935, zone: 'Navi Mumbai' },
]

