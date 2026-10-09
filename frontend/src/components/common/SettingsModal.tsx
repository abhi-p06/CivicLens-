import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Settings2, Save, RotateCcw } from 'lucide-react'
import { api } from '../../services/api'
import { IssueCategory } from '../../types'

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
  const [config, setConfig] = useState<Record<string, any>>({})
  const [selectedCategory, setSelectedCategory] = useState<string>('Roads & Footpaths')
  const [department, setDepartment] = useState('')
  const [code, setCode] = useState('')
  const [criticalAction, setCriticalAction] = useState('')
  const [criticalSla, setCriticalSla] = useState(12)
  const [saving, setSaving] = useState(false)
  const [savedSuccess, setSavedSuccess] = useState(false)

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
    } catch (err) {
      console.error(err)
    }
  }

  const updateFormFields = (cat: string, cfg: Record<string, any>) => {
    const data = cfg[cat]
    if (data) {
      setDepartment(data.department || '')
      setCode(data.code || '')
      setCriticalAction(data.actions?.CRITICAL || '')
      setCriticalSla(data.slaHours?.CRITICAL || 12)
    }
  }

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat)
    updateFormFields(cat, config)
  }

  const handleSave = async () => {
    setSaving(true)
    setSavedSuccess(false)
    try {
      const currentCatData = config[selectedCategory] || {}
      const updatedConfig = {
        ...config,
        [selectedCategory]: {
          ...currentCatData,
          department,
          code,
          actions: {
            ...currentCatData.actions,
            CRITICAL: criticalAction,
          },
          slaHours: {
            ...currentCatData.slaHours,
            CRITICAL: Number(criticalSla),
          },
        },
      }
      await api.updateRoutingConfig(selectedCategory, updatedConfig[selectedCategory])
      setConfig(updatedConfig)
      setSavedSuccess(true)
      onConfigSaved()
      setTimeout(() => setSavedSuccess(false), 2500)
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const categories = Object.keys(config)

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.15 }}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.18, ease: 'easeOut' }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl bg-[#0e131d] border border-slate-700 rounded-xl shadow-2xl overflow-hidden font-mono text-xs"
          >
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-800 bg-[#121824]">
              <div className="flex items-center gap-2">
                <Settings2 className="w-5 h-5 text-cyan-400" />
                <span className="font-bold text-slate-100 text-sm tracking-wide">
                  MUNICIPAL DISPATCH & ROUTING CONFIGURATION
                </span>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
              <div className="text-slate-400 text-[11px] font-sans leading-relaxed">
                Configure dynamic department assignments, automated action directives, and target SLA hours. This decouples administrative dispatch protocols from machine learning inference.
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-bold uppercase text-[10px]">Select Target Domain</label>
                <div className="flex flex-wrap gap-1.5">
                  {categories.map((cat) => (
                    <button
                      key={cat}
                      type="button"
                      onClick={() => handleCategoryChange(cat)}
                      className={`px-2.5 py-1 rounded text-[11px] border transition ${
                        selectedCategory === cat
                          ? 'bg-cyan-950 border-cyan-500 text-cyan-300 font-bold'
                          : 'bg-[#121824] border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-slate-400 font-bold uppercase text-[10px]">Responsible Department</label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full bg-[#121824] border border-slate-700 rounded-lg p-2.5 text-slate-100 outline-none focus:border-cyan-500"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-slate-400 font-bold uppercase text-[10px]">Department Agency Code</label>
                  <input
                    type="text"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    className="w-full bg-[#121824] border border-slate-700 rounded-lg p-2.5 text-slate-100 outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-bold uppercase text-[10px]">Emergency Action Directive (Critical Incidents)</label>
                <textarea
                  rows={2}
                  value={criticalAction}
                  onChange={(e) => setCriticalAction(e.target.value)}
                  className="w-full bg-[#121824] border border-slate-700 rounded-lg p-2.5 text-slate-100 outline-none focus:border-cyan-500 font-sans"
                />
              </div>

              <div className="space-y-1">
                <label className="text-slate-400 font-bold uppercase text-[10px]">Target Resolution Window (Hours SLA)</label>
                <input
                  type="number"
                  value={criticalSla}
                  onChange={(e) => setCriticalSla(Number(e.target.value))}
                  className="w-32 bg-[#121824] border border-slate-700 rounded-lg p-2.5 text-slate-100 outline-none focus:border-cyan-500"
                />
              </div>

              {savedSuccess && (
                <div className="p-2.5 bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-xs flex items-center gap-2">
                  <span>Routing rule successfully updated in active system registry.</span>
                </div>
              )}
            </div>

            <div className="px-5 py-3.5 bg-[#0a0d14] border-t border-slate-800 flex items-center justify-between">
              <span className="text-[10px] text-slate-500">Persists to runtime memory store</span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-1.5 bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded text-xs transition"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-4 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium text-xs transition disabled:opacity-50"
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
  )
}

export default SettingsModal
