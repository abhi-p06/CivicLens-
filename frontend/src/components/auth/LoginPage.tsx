import React from 'react'
import { motion } from 'framer-motion'
import {
  Users,
  ShieldCheck,
  Sliders,
  CheckCircle2,
  ArrowRight,
  Shield,
  Activity,
  Sparkles,
  Info
} from 'lucide-react'
import { useCivicMotion } from '../../lib/motionContext'

interface LoginPageProps {
  onSelectRole: (role: 'citizen' | 'municipal' | 'admin') => void
}

export const LoginPage: React.FC<LoginPageProps> = ({ onSelectRole }) => {
  const { isReduced } = useCivicMotion()

  const roles = [
    {
      id: 'citizen' as const,
      title: 'Citizen Portal',
      badge: 'Public Reporting',
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: Users,
      iconBg: 'bg-emerald-50 text-emerald-600 border-emerald-200',
      description:
        'Submit pothole and garbage complaints, upload photo evidence, and track verification outcomes for your neighborhood.',
      features: [
        'Pothole & road-damage reporting',
        'Garbage & litter detection reports',
        'Track personal complaint history & statuses',
      ],
      buttonText: 'Continue as Citizen',
      buttonClass: 'bg-[#6457E8] hover:bg-[#5145CF] text-white',
      footerNote: 'Open public registration available',
      route: '/login/citizen',
    },
    {
      id: 'municipal' as const,
      title: 'Municipal Officer',
      badge: 'Field Operations',
      badgeColor: 'bg-indigo-50 text-[#6457E8] border-indigo-200',
      icon: ShieldCheck,
      iconBg: 'bg-indigo-50 text-[#6457E8] border-indigo-200',
      description:
        'Triage prioritized incidents, inspect YOLO vision detections, update workflow statuses, and submit before/after verification photos.',
      features: [
        'Operations queue & tactical GIS map',
        'Inspect computer vision confidence scores',
        'Dual-image repair verification & audit history',
      ],
      buttonText: 'Officer Sign In',
      buttonClass: 'bg-[#13152E] hover:bg-[#212348] text-white',
      footerNote: 'Restricted municipal personnel',
      route: '/login/municipal',
    },
    {
      id: 'admin' as const,
      title: 'Command Administrator',
      badge: 'Platform Governance',
      badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
      icon: Sliders,
      iconBg: 'bg-purple-50 text-purple-600 border-purple-200',
      description:
        'Oversee municipal agency routing, configure departmental SLAs, monitor model health, manage accounts, and govern system resets.',
      features: [
        'Agency department routing & SLA configuration',
        'Spatiotemporal hotspot & recurrence intelligence',
        'System telemetry & user administration',
      ],
      buttonText: 'Administrator Sign In',
      buttonClass: 'bg-[#6457E8] hover:bg-[#5145CF] text-white',
      footerNote: 'Privileged credentials required',
      route: '/login/admin',
    },
  ]

  return (
    <div className="min-h-screen bg-[#F6F7FC] flex flex-col justify-between font-sans text-[#11162A]">
      {/* Top Banner Navigation */}
      <header className="h-16 px-6 sm:px-12 flex items-center justify-between border-b border-[#E4E7F1] bg-white shadow-[0_1px_2px_rgba(17,22,42,0.02)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#13152E] flex items-center justify-center text-white shadow-xs">
            <Shield className="w-5 h-5 text-[#8B5CF6]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-[#11162A]">
                CIVILENS
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#6457E8]/10 text-[#6457E8] font-bold font-mono">
                v2.4
              </span>
            </div>
            <p className="text-xs text-[#65708B] leading-none">
              Civic Infrastructure Intelligence
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#65708B]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="hidden sm:inline font-medium text-slate-700">
            Operations Engine Online
          </span>
        </div>
      </header>

      {/* Main Role Selection Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-10 sm:py-16 flex flex-col items-center justify-center">
        {/* Header Heading */}
        <motion.div
          initial={isReduced ? false : { opacity: 0, y: -12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="text-center max-w-2xl mb-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#6457E8]/10 text-[#6457E8] text-xs font-semibold mb-4 border border-[#6457E8]/20">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Role-Based Municipal Authentication</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#11162A]">
            CIVILENS Access Portal
          </h1>
          <p className="text-sm sm:text-base text-[#65708B] mt-2.5">
            Select your civic workspace role to sign in to the verified operations center.
          </p>
        </motion.div>

        {/* 3 Role Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
          {roles.map((r, index) => {
            const Icon = r.icon
            return (
              <motion.div
                key={r.id}
                initial={isReduced ? false : { opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.08 }}
                whileHover={isReduced ? {} : { y: -4, transition: { duration: 0.18 } }}
                className="bg-white rounded-2xl border border-[#E4E7F1] p-6 sm:p-7 flex flex-col justify-between shadow-[0_4px_16px_rgba(17,22,42,0.03)] hover:shadow-[0_12px_28px_rgba(100,87,232,0.08)] hover:border-[#6457E8]/40 transition-all duration-200 group"
              >
                <div>
                  {/* Top Icon & Badge */}
                  <div className="flex items-center justify-between mb-5">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center border shadow-xs ${r.iconBg}`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <span
                      className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border font-mono ${r.badgeColor}`}
                    >
                      {r.badge}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <h2 className="text-xl font-bold text-[#11162A] group-hover:text-[#6457E8] transition-colors">
                    {r.title}
                  </h2>
                  <p className="text-xs text-[#65708B] leading-relaxed mt-2 min-h-[48px]">
                    {r.description}
                  </p>

                  {/* Feature Checklist */}
                  <div className="mt-5 pt-4 border-t border-[#E4E7F1]/80 space-y-2">
                    {r.features.map((feat, fIdx) => (
                      <div
                        key={fIdx}
                        className="flex items-start gap-2 text-xs text-[#11162A]/90"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0 mt-0.5" />
                        <span className="leading-snug">{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Bottom Action Button */}
                <div className="mt-8 pt-4 border-t border-[#E4E7F1]/60">
                  <button
                    onClick={() => onSelectRole(r.id)}
                    className={`w-full py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs active:scale-[0.98] ${r.buttonClass}`}
                  >
                    <span>{r.buttonText}</span>
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                  </button>
                  <p className="text-[11px] text-center text-[#65708B] mt-2 font-medium">
                    {r.footerNote}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Local Demo Reference Box */}
        <div className="mt-12 w-full max-w-2xl bg-white/70 border border-[#E4E7F1] rounded-xl p-4 text-xs text-[#65708B] shadow-xs">
          <div className="flex items-center gap-2 font-semibold text-[#11162A] mb-2">
            <Info className="w-4 h-4 text-[#6457E8]" />
            <span>Demonstration Access & Authentication</span>
          </div>
          <p className="text-[11px] leading-relaxed">
            Role authentication is verified server-side. Demo accounts are initialized by backend development configuration and disabled in production. See <code className="text-[#6457E8]">docs/DEMO_GUIDE.md</code> for environment setup instructions.
          </p>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 px-6 text-center text-xs text-[#65708B] border-t border-[#E4E7F1] bg-white">
        CIVILENS — Multimodal Civic Infrastructure Intelligence Platform &copy; 2026. All rights reserved.
      </footer>
    </div>
  )
}
