import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { PriorityLevel, PriorityBreakdown } from '../../types'
import { cn } from '../../lib/utils'
import { Info } from 'lucide-react'
import { CountUp } from '../reactbits/CountUp'
import { useCivicMotion } from '../../lib/motionContext'

interface PriorityGaugeProps {
  score: number // 0 to 100
  level: PriorityLevel | string
  breakdown?: PriorityBreakdown
  reasoning?: string
  compact?: boolean
  showDetails?: boolean
}

export const PriorityGauge: React.FC<PriorityGaugeProps> = ({
  score,
  level,
  breakdown,
  reasoning,
  compact = false,
  showDetails = false,
}) => {
  const [open, setOpen] = useState(false)
  const { isReduced } = useCivicMotion()
  const normLevel = (level || 'LOW').toUpperCase()

  // Color mapping per Aurora Indigo standards & backend priority thresholds (85/70/40)
  let barColor = 'bg-[#3B82F6]'
  let textColor = 'text-[#3B82F6]'
  let badgeBg = 'bg-blue-50 text-blue-800 border-blue-200'

  if (normLevel === 'CRITICAL' || score >= 85) {
    barColor = 'bg-[#EF4444]'
    textColor = 'text-[#EF4444]'
    badgeBg = 'bg-rose-50 text-rose-800 border-rose-200'
  } else if (normLevel === 'HIGH' || score >= 70) {
    barColor = 'bg-[#F97316]'
    textColor = 'text-[#F97316]'
    badgeBg = 'bg-orange-50 text-orange-800 border-orange-200'
  } else if (normLevel === 'MEDIUM' || score >= 40) {
    barColor = 'bg-[#EAB308]'
    textColor = 'text-[#EAB308]'
    badgeBg = 'bg-amber-50 text-amber-800 border-amber-200'
  }

  const safeScore = Math.min(100, Math.max(0, score))

  if (compact) {
    return (
      <div className="inline-flex items-center gap-2 font-mono text-xs">
        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden shrink-0 border border-slate-200">
          <motion.div
            initial={{ width: isReduced ? `${safeScore}%` : 0 }}
            animate={{ width: `${safeScore}%` }}
            transition={{ duration: isReduced ? 0.05 : 0.75, ease: [0.16, 1, 0.3, 1] }}
            className={cn('h-full rounded-full', barColor)}
          />
        </div>
        <span className={cn('font-bold', textColor)}>
          <CountUp to={Math.round(score)} duration={0.8} />
        </span>
      </div>
    )
  }

  const urgencyVal = typeof breakdown?.urgency === 'number' ? breakdown.urgency : Number((breakdown as any)?.urgency_points ?? 0)
  const textSevVal = typeof breakdown?.textSeverity === 'number' ? breakdown.textSeverity : Number((breakdown as any)?.text_severity_points ?? 0)
  const visSevVal = typeof breakdown?.visualSeverity === 'number' ? breakdown.visualSeverity : Number((breakdown as any)?.visual_severity_points ?? 0)
  const relRepVal = typeof breakdown?.relatedReports === 'number' ? breakdown.relatedReports : Number((breakdown as any)?.related_reports_points ?? 0)
  const recencyVal = typeof breakdown?.recency === 'number' ? breakdown.recency : Number((breakdown as any)?.recency_points ?? 0)
  const locRiskVal = typeof breakdown?.locationRisk === 'number' ? breakdown.locationRisk : Number((breakdown as any)?.location_risk_points ?? 0)

  return (
    <div className="relative font-sans text-xs">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-semibold border', badgeBg)}>
            {normLevel}
          </span>
          <span className="text-slate-600 text-xs font-medium">Risk Priority Score</span>
        </div>
        <div className="flex items-center gap-1 font-mono">
          <span className={cn('text-base font-bold', textColor)}>
            <CountUp to={Math.round(score)} duration={0.8} />
          </span>
          <span className="text-slate-400 text-xs">/ 100</span>
          {(breakdown || reasoning) && (
            <motion.button
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setOpen(!open)}
              className="text-slate-400 hover:text-[#6457E8] transition ml-1 p-0.5 rounded cursor-pointer"
              title="Explain priority factors"
            >
              <Info className="w-3.5 h-3.5" />
            </motion.button>
          )}
        </div>
      </div>

      {/* Segmented Animated Bar */}
      <div className="h-2.5 w-full bg-slate-100 border border-slate-200 rounded-full overflow-hidden flex relative">
        <motion.div
          initial={{ width: isReduced ? `${safeScore}%` : 0 }}
          animate={{ width: `${safeScore}%` }}
          transition={{ duration: isReduced ? 0.05 : 0.8, ease: [0.16, 1, 0.3, 1] }}
          className={cn('h-full rounded-full', barColor)}
        />
      </div>

      {/* Explanatory Breakdown Card with AnimatePresence */}
      <AnimatePresence>
        {(open || showDetails) && breakdown && (
          <motion.div
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 10 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.22, ease: 'easeOut' }}
            className="overflow-hidden p-3.5 bg-white border border-[#E4E7F1] rounded-xl text-xs space-y-2.5 shadow-sm z-20"
          >
            <div className="text-xs text-slate-800 border-b border-slate-100 pb-2 font-semibold flex justify-between items-center">
              <span>Authoritative 6-Factor Risk Breakdown</span>
              <span className="text-[#6457E8] font-bold font-mono">Total: {score.toFixed(1)}/100</span>
            </div>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={{
                hidden: { opacity: 0 },
                visible: {
                  opacity: 1,
                  transition: { staggerChildren: 0.05 },
                },
              }}
              className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-slate-700"
            >
              {[
                { label: 'Urgency:', val: urgencyVal.toFixed(1), max: 20, note: null },
                { label: 'Text Severity:', val: textSevVal.toFixed(1), max: 20, note: null },
                { 
                  label: 'Visual Severity:', 
                  val: visSevVal.toFixed(1), 
                  max: 20, 
                  note: visSevVal === 0 ? 'No visual defect detected' : null 
                },
                { label: 'Related Reports:', val: relRepVal.toFixed(1), max: 15, note: null },
                { label: 'Recency:', val: recencyVal.toFixed(1), max: 10, note: null },
                { label: 'Location Risk:', val: locRiskVal.toFixed(1), max: 15, note: null },
              ].map((item, idx) => (
                <motion.div
                  key={idx}
                  variants={{
                    hidden: { opacity: 0, y: 4 },
                    visible: { opacity: 1, y: 0 },
                  }}
                  className="flex flex-col justify-between p-2 bg-slate-50 rounded-lg border border-slate-100"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">{item.label}</span>
                    <span className="font-semibold text-slate-800 font-mono">
                      {item.val}/{item.max}
                    </span>
                  </div>
                  {item.note && (
                    <span className="text-[10px] text-amber-600 font-sans mt-0.5">
                      {item.note}
                    </span>
                  )}
                </motion.div>
              ))}
            </motion.div>
            {reasoning && (
              <div className="pt-2 text-[11px] text-slate-500 border-t border-slate-100 leading-relaxed font-sans">
                {reasoning}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default PriorityGauge
