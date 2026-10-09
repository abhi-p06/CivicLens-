import React, { useState } from 'react'

interface BeforeAfterSliderProps {
  beforeLabel?: string
  afterLabel?: string
  beforeSubtext?: string
  afterSubtext?: string
  confidence?: number
}

export const BeforeAfterSlider: React.FC<BeforeAfterSliderProps> = ({
  beforeLabel = 'ORIGINAL DEFECT (BEFORE)',
  afterLabel = 'POST-REPAIR RESTORATION (AFTER)',
  beforeSubtext = 'Pothole (Detected, 94% conf)',
  afterSubtext = 'Clean asphalt patch (No residual defect)',
  confidence = 0.95,
}) => {
  const [sliderPos, setSliderPos] = useState(50)

  return (
    <div className="relative w-full h-44 sm:h-52 bg-[#090c13] rounded-xl overflow-hidden border border-slate-800 select-none font-mono text-xs shadow-inner">
      {/* Background / Before Layer */}
      <div className="absolute inset-0 bg-[#120808] flex items-center justify-center p-4">
        <div className="text-center space-y-1">
          <div className="text-[10px] uppercase font-bold text-rose-400 tracking-wider">
            {beforeLabel}
          </div>
          <div className="text-slate-300 font-sans text-xs">{beforeSubtext}</div>
          <div className="inline-block mt-2 px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-[10px]">
            Visual Defect Area: 14.2%
          </div>
        </div>
      </div>

      {/* Foreground / After Layer (clipped by slider) */}
      <div
        className="absolute inset-0 bg-[#08140e] flex items-center justify-center p-4 overflow-hidden"
        style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
      >
        <div className="text-center space-y-1">
          <div className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
            {afterLabel}
          </div>
          <div className="text-slate-300 font-sans text-xs">{afterSubtext}</div>
          <div className="inline-block mt-2 px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-[10px]">
            Verification Confidence: {(confidence * 100).toFixed(1)}%
          </div>
        </div>
      </div>

      {/* Divider Line */}
      <div
        className="absolute top-0 bottom-0 w-0.5 bg-cyan-400 cursor-ew-resize z-20 shadow-[0_0_10px_#06b6d4]"
        style={{ left: `${sliderPos}%` }}
      >
        <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-6 h-6 rounded-full bg-cyan-500 border-2 border-slate-900 flex items-center justify-center text-slate-900 font-bold text-[9px] shadow-lg">
          &harr;
        </div>
      </div>

      {/* Interactive Range Input */}
      <input
        type="range"
        min={0}
        max={100}
        value={sliderPos}
        onChange={(e) => setSliderPos(Number(e.target.value))}
        className="absolute inset-0 opacity-0 cursor-ew-resize z-30 w-full h-full"
      />

      {/* Watermarks */}
      <div className="absolute bottom-2 left-3 z-10 text-[9px] text-rose-400/80 font-bold pointer-events-none">
        &larr; BEFORE REPAIR
      </div>
      <div className="absolute bottom-2 right-3 z-10 text-[9px] text-emerald-400/80 font-bold pointer-events-none">
        AFTER REPAIR &rarr;
      </div>
    </div>
  )
}
