import React, { useState, useRef, useCallback } from 'react'
import { CheckCircle2, ShieldAlert, Sparkles, Scan } from 'lucide-react'

interface BeforeAfterSliderProps {
  beforeImage?: string
  afterImage?: string
  beforeLabel?: string
  afterLabel?: string
  beforeSubtext?: string
  afterSubtext?: string
  confidence?: number
  isScanning?: boolean
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeImage = '/sample_pothole.jpg',
  afterImage = '/sample_repaired_pothole.jpg',
  beforeLabel = 'ORIGINAL DEFECT (BEFORE)',
  afterLabel = 'RESTORED SURFACE (AFTER)',
  beforeSubtext = 'Severe Pothole (Depth: 12cm, Area: 0.85m²)',
  afterSubtext = 'Asphalt Patch Completed (0 residual defect)',
  confidence = 0.942,
  isScanning = false,
}) => {
  const [sliderPos, setSliderPos] = useState(50)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleMove = useCallback((clientX: number) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = clientX - rect.left
    const percent = Math.max(0, Math.min(100, (x / rect.width) * 100))
    setSliderPos(percent)
  }, [])

  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length > 0) handleMove(e.touches[0].clientX)
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) handleMove(e.clientX)
  }

  return (
    <div
      ref={containerRef}
      onMouseDown={() => setIsDragging(true)}
      onMouseUp={() => setIsDragging(false)}
      onMouseLeave={() => setIsDragging(false)}
      onMouseMove={handleMouseMove}
      onTouchMove={handleTouchMove}
      className="relative w-full h-64 sm:h-80 md:h-96 rounded-xl overflow-hidden border border-slate-800 bg-[#07090e] select-none shadow-2xl group cursor-ew-resize"
    >
      {/* 1. Before Image (Background Layer) */}
      <img
        src={beforeImage}
        alt="Before repair"
        className="absolute inset-0 w-full h-full object-cover"
      />

      {/* Before Defect Bounding Box HUD */}
      <div className="absolute inset-0 pointer-events-none p-4 flex flex-col justify-between">
        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded bg-black/75 backdrop-blur-md border border-rose-500/70 text-rose-300 text-[11px] font-mono font-bold flex items-center gap-1.5 shadow-lg">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            {beforeLabel}
          </span>
          <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm text-slate-300 text-[10px] font-mono">
            {beforeSubtext}
          </span>
        </div>

        <div className="text-[10px] font-mono text-rose-400/90 font-bold bg-black/60 backdrop-blur-sm px-2 py-1 rounded w-fit">
          &larr; SLIDE RIGHT TO REVEAL REPAIRED STATE
        </div>
      </div>

      {/* 2. After Image (Clipped Overlay Layer) */}
      <div
        className="absolute inset-0 overflow-hidden"
        style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
      >
        <img
          src={afterImage}
          alt="After repair"
          className="absolute inset-0 w-full h-full object-cover"
        />

        {/* After HUD */}
        <div className="absolute inset-0 pointer-events-none p-4 flex flex-col justify-between items-end">
          <div className="flex items-center gap-2">
            <span className="hidden sm:inline-block px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm text-emerald-300 text-[10px] font-mono">
              {afterSubtext}
            </span>
            <span className="px-2.5 py-1 rounded bg-black/75 backdrop-blur-md border border-emerald-500/70 text-emerald-300 text-[11px] font-mono font-bold flex items-center gap-1.5 shadow-lg">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              {afterLabel}
            </span>
          </div>

          <div className="text-[10px] font-mono text-emerald-400/90 font-bold bg-black/60 backdrop-blur-sm px-2 py-1 rounded w-fit">
            LIKELY RESOLVED (Confidence: {(confidence * 100).toFixed(1)}%) &rarr;
          </div>
        </div>
      </div>

      {/* 3. Divider Line & Interactive Handle */}
      <div
        className="absolute top-0 bottom-0 w-1 bg-cyan-400 z-20 shadow-[0_0_15px_rgba(6,182,212,0.9)]"
        style={{ left: `${sliderPos}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-slate-900 border-2 border-cyan-400 text-cyan-300 flex items-center justify-center text-xs font-bold shadow-xl group-hover:scale-110 transition-transform">
          &harr;
        </div>
      </div>

      {/* 4. Scanning Beam Animation */}
      {isScanning && (
        <div className="absolute inset-0 z-30 pointer-events-none overflow-hidden">
          <div className="w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_20px_#06b6d4] animate-bounce" />
          <div className="absolute top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded bg-black/80 border border-cyan-500 text-cyan-300 text-[11px] font-mono font-bold flex items-center gap-2 animate-pulse">
            <Scan className="w-3.5 h-3.5" />
            COMPUTER VISION INSPECTION RUNNING...
          </div>
        </div>
      )}

      {/* Native Range Slider for accessibility & drag */}
      <input
        type="range"
        min={0}
        max={100}
        value={sliderPos}
        onChange={(e) => setSliderPos(Number(e.target.value))}
        className="absolute inset-0 opacity-0 cursor-ew-resize z-30 w-full h-full"
        aria-label="Before after comparison slider"
      />
    </div>
  )
}

export default BeforeAfterSlider
