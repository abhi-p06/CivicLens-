import React, { useState, useEffect } from 'react'
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
    const item = cfg[cat]
    if (item) {
      setDepartment(item.department || '')
      setCode(item.code || '')
      const crit = item.actions?.['CRITICAL']
      if (crit) {
        setCriticalAction(crit[0] || '')
        setCriticalSla(crit[1] || 12)
      }
    }
  }

  const handleCategoryChange = (cat: string) => {
    setSelectedCategory(cat)
    updateFormFields(cat, config)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const updatedItem = {
        ...config[selectedCategory],
        department,
        code,
        actions: {
          ...config[selectedCategory]?.actions,
          CRITICAL: [criticalAction, Number(criticalSla)],
        },
      }
      await api.updateRoutingConfig(selectedCategory, updatedItem)
      setSavedSuccess(true)
      setTimeout(() => setSavedSuccess(false), 2500)
      onConfigSaved()
      loadConfig()
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  const categories = Object.keys(config)

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-[#0e131d] border border-slate-700 rounded-xl shadow-2xl overflow-hidden font-mono text-xs">
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
            <label className="text-[11px] uppercase font-bold text-slate-400">
              Civic Issue Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => handleCategoryChange(e.target.value)}
              className="w-full bg-[#121824] border border-slate-700 text-slate-200 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
            >
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-[11px] uppercase font-bold text-slate-400">
                Assigned Department Name
              </label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full bg-[#121824] border border-slate-700 text-slate-200 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
              />
            </div>
            <div className="space-y-1">
              <label className="text-[11px] uppercase font-bold text-slate-400">
                Agency / Department Code
              </label>
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full bg-[#121824] border border-slate-700 text-slate-200 rounded p-2 text-xs font-mono outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="p-3 bg-[#111723] border border-slate-800 rounded-lg space-y-2">
            <div className="text-[10px] uppercase font-bold text-rose-400">
              Critical Priority Protocol (SLA & Recommended Action)
            </div>
            <div className="space-y-1">
              <label className="text-[10px] text-slate-400">Recommended Action Directive</label>
              <textarea
                rows={2}
                value={criticalAction}
                onChange={(e) => setCriticalAction(e.target.value)}
                className="w-full bg-[#0a0d14] border border-slate-700 text-slate-200 rounded p-2 text-xs font-sans outline-none focus:border-cyan-500"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-400">Target SLA Resolution Time (Hours)</span>
              <input
                type="number"
                min={1}
                max={168}
                value={criticalSla}
                onChange={(e) => setCriticalSla(Number(e.target.value))}
                className="w-24 bg-[#0a0d14] border border-slate-700 text-slate-200 rounded p-1.5 text-xs font-mono text-right outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {savedSuccess && (
            <div className="p-2.5 bg-emerald-950/60 border border-emerald-800 text-emerald-300 rounded text-center text-xs">
              Routing protocol updated successfully without retraining ML models.
            </div>
          )}
        </div>

        <div className="px-5 py-3 bg-[#0a0d14] border-t border-slate-800 flex items-center justify-between">
          <button
            onClick={loadConfig}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Form</span>
          </button>
          <div className="flex items-center gap-2">
            <button
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
      </div>
    </div>
  )
}
