import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Settings2, Save, RotateCcw, Zap, AlertCircle } from 'lucide-react'
import { api } from '../../services/api'
import { IssueCategory } from '../../types'
import { useCivicMotion, MotionMode } from '../../lib/motionContext'
import { Portal } from './Portal'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
  onConfigSaved: () => void
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onConfigSaved,
}) => {
  const { motionMode, setMotionMode } = useCivicMotion()
  const [config, setConfig] = useState<Record<string, any>>({})
  const [selectedCategory, setSelectedCategory] = useState<string>('Roads & Footpaths')
  const [department, setDepartment] = useState('')
  const [code, setCode] = useState('')
  const [criticalAction, setCriticalAction] = useState('')
  const [criticalSla, setCriticalSla] = useState(12)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      loadConfig()
    }
  }, [isOpen])

  const loadConfig = async () => {
    try {
      const cfg = await api.getRoutingConfig()
      setConfig(cfg)
      if (cfg[selectedCategory]) {
        updateFormFields(selectedCategory, cfg)
      }
    } catch (err: any) {
      console.error(err)
      setErrorMessage(err?.message || 'Failed to load configuration.')
    }
  }

  const updateFormFields = (cat: string, cfg: Record<string, any>) => {
    const data = cfg[cat]
    if (data) {
      setDepartment(data.department || '')
      setCode(data.code || '')
      const crit = data.actions?.CRITICAL
      if (Array.isArray(crit)) {
        setCriticalAction(crit[0] || '')
        setCriticalSla(Number(crit[1]) || 12)
      } else {
        setCriticalAction(typeof crit === 'string' ? crit : '')
        setCriticalSla(Number(data.slaHours?.CRITICAL) || 12)
      }
    }
  }

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat)
    setErrorMessage(null)
    updateFormFields(cat, config)
  }

  const handleSave = async () => {
    setSaving(true)
    setSavedSuccess(false)
    setErrorMessage(null)
    try {
      const currentCatData = config[selectedCategory] || {}
      const updatedCatConfig = {
        ...currentCatData,
        department: department.trim(),
        code: code.trim(),
        actions: {
          ...currentCatData.actions,
          CRITICAL: [criticalAction.trim(), Number(criticalSla)],
        },
        slaHours: {
          ...currentCatData.slaHours,
          CRITICAL: Number(criticalSla),
        },
      }
      const res = await api.updateRoutingConfig(selectedCategory, updatedCatConfig)
      const updatedConfig = {
        ...config,
        [selectedCategory]: res?.config || updatedCatConfig,
      }
      setConfig(updatedConfig)
      setSavedSuccess(true)
      onConfigSaved()
      setTimeout(() => setSavedSuccess(false), 2500)
    } catch (err: any) {
      console.error('Failed to update routing configuration:', err)
      setErrorMessage(err?.message || 'Failed to update department routing rules.')
    } finally {
      setSaving(false)
    }
  }

  const categories = Object.keys(config)

  return (
    <Portal>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="fixed inset-0 z-[9000] layer-modal-backdrop bg-black/50 backdrop-blur-xs flex items-center justify-center p-4"
            onClick={onClose}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.18, ease: 'easeOut' }}
              onClick={(e) => e.stopPropagation()}
              className="relative z-[9001] layer-modal-content w-full max-w-2xl bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl overflow-hidden font-sans text-xs"
            >
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#E4E7F1] bg-[#F0F2F9]">
              <div className="flex items-center gap-2.5">
                <Settings2 className="w-5 h-5 text-[#6457E8]" />
                <span className="font-bold text-[#11162A] text-sm tracking-normal">
                  Municipal Dispatch & Routing Configuration
                </span>
              </div>
              <button onClick={onClose} className="text-[#65708B] hover:text-[#11162A] p-1 rounded-lg hover:bg-black/5 transition cursor-pointer">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[75vh] overflow-y-auto bg-[#F6F7FC]">
              <div className="text-[#65708B] text-xs font-sans leading-relaxed">
                Configure dynamic department assignments, automated action directives, and target SLA hours. This decouples administrative dispatch protocols from machine learning inference.
              </div>

              <div className="space-y-1.5">
                <label className="text-[#65708B] font-semibold text-xs">Select Target Domain</label>
                <div className="flex flex-wrap gap-1.5">
                  {categories.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => handleCategoryChange(cat)}
                      className={`px-3 py-1.5 rounded-lg text-xs border transition cursor-pointer ${
                        selectedCategory === cat
                          ? 'bg-[#6457E8] border-[#6457E8] text-white font-semibold shadow-xs'
                          : 'bg-white border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[#11162A] font-semibold text-xs">Responsible Department</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[#11162A] font-semibold text-xs">Department Agency Code</label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[#11162A] font-semibold text-xs">Emergency Action Directive (Critical Incidents)</label>
                <textarea
                  rows={2}
                  value={criticalAction}
                  onChange={(e) => setCriticalAction(e.target.value)}
                  className="w-full bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs font-sans leading-relaxed"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[#11162A] font-semibold text-xs">Target Resolution Window (Hours SLA)</label>
                <input
                  type="number"
                  value={criticalSla}
                  onChange={(e) => setCriticalSla(Number(e.target.value))}
                  className="w-32 bg-white border border-[#E4E7F1] rounded-xl p-2.5 text-xs text-[#11162A] outline-none focus:border-[#6457E8] focus:ring-1 focus:ring-[#6457E8] shadow-xs"
                />
              </div>

              {/* Animation & Accessibility Preferences */}
              <div className="pt-3 border-t border-[#E4E7F1] space-y-2">
                <div className="flex items-center gap-1.5 text-[#11162A] font-semibold text-xs">
                  <Zap className="w-3.5 h-3.5 text-[#6457E8]" />
                  <span>UI Animations & Motion Accessibility</span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {(['full', 'system', 'reduced'] as MotionMode[]).map((mode) => (
                    <button
                      key={mode}
                      type="button"
                      onClick={() => setMotionMode(mode)}
                      className={`p-2.5 rounded-lg border text-xs font-medium transition cursor-pointer text-center ${
                        motionMode === mode
                          ? 'bg-[#6457E8] border-[#6457E8] text-white font-semibold shadow-xs'
                          : 'bg-white border-[#E4E7F1] text-[#65708B] hover:text-[#11162A] hover:bg-slate-50'
                      }`}
                    >
                      {mode === 'full' ? 'Full Motion' : mode === 'system' ? 'System Match' : 'Reduced'}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-[#65708B]">
                  {motionMode === 'full'
                    ? 'Presentation Grade: All cinematic entrances, counters, and pipeline animations active.'
                    : motionMode === 'system'
                    ? 'Respects your operating system reduce-motion accessibility setting.'
                    : 'Disables transitions and reduces visual movement for accessibility.'}
                </p>
              </div>

              {savedSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
                  <span>Routing rule successfully updated in active system registry.</span>
                </div>
              )}

              {errorMessage && (
                <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  <span>{errorMessage}</span>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-white border-t border-[#E4E7F1] flex items-center justify-between">
              <span className="text-xs text-[#65708B]">Persists to runtime memory store</span>
              <div className="flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3.5 py-2 bg-transparent hover:bg-slate-100 text-[#65708B] hover:text-[#11162A] rounded-lg text-xs font-medium transition cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#6457E8] hover:bg-[#5145CF] text-white rounded-lg font-semibold text-xs transition disabled:opacity-50 shadow-xs cursor-pointer"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{saving ? 'Saving...' : 'Apply Protocol'}</span>
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  </Portal>
)
}

export default SettingsModal
