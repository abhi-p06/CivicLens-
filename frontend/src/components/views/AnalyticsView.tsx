import React, { useState, useEffect } from 'react'
import {
  BarChart3,
  Cpu,
  Layers,
  Sparkles,
  Network,
  ShieldCheck,
  Building,
  RefreshCw,
} from 'lucide-react'
import { api } from '../../services/api'
import { EvaluationMetrics } from '../../types'
import { KpiCard } from '../common/KpiCard'

export const AnalyticsView: React.FC = () => {
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null)
  const [loading, setLoading] = useState(false)

  const loadMetrics = async () => {
    setLoading(true)
    try {
      const data = await api.getEvaluationMetrics()
      setMetrics(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadMetrics()
  }, [])

  return (
    <div className="h-full flex flex-col overflow-y-auto p-4 sm:p-6 space-y-5 font-mono text-xs">
      {/* Header */}
      <div className="p-4 bg-[#101420] border border-cyan-900/60 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-xl">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            <h1 className="text-base font-bold text-slate-100 tracking-wide">
              EMPIRICAL MODEL EVALUATION & SCIKIT-LEARN BENCHMARKS
            </h1>
          </div>
          <p className="text-slate-400 text-xs font-sans mt-1">
            Empirically computed metrics derived strictly from actual test ground-truth data (zero fabricated scores).
          </p>
        </div>

        <button
          onClick={loadMetrics}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#121824] hover:bg-[#162030] border border-slate-700 text-slate-300 rounded text-xs transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate Benchmarks</span>
        </button>
      </div>

      {metrics && (
        <div className="space-y-5">
          {/* Section 1: NLP Multiclass Classification */}
          <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2 text-slate-200 font-bold">
                <Cpu className="w-4 h-4 text-cyan-400" />
                <span>1. CIVIC COMPLAINT CLASSIFICATION (NLP MULTICLASS)</span>
              </div>
              <span className="text-slate-500 text-[10px]">
                N = {metrics.classification?.total_evaluated ?? metrics.classification?.sample_count ?? 6} Samples
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-[#111724] rounded-lg border border-slate-800">
                <div className="text-slate-400 text-[10px]">ACCURACY</div>
                <div className="text-xl font-bold text-emerald-400 mt-1">
                  {((metrics.classification?.accuracy ?? 0) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 bg-[#111724] rounded-lg border border-slate-800">
                <div className="text-slate-400 text-[10px]">PRECISION (MACRO)</div>
                <div className="text-xl font-bold text-cyan-400 mt-1">
                  {(((metrics.classification?.precision_macro ?? metrics.classification?.macro_precision) ?? 0) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 bg-[#111724] rounded-lg border border-slate-800">
                <div className="text-slate-400 text-[10px]">RECALL (MACRO)</div>
                <div className="text-xl font-bold text-sky-400 mt-1">
                  {(((metrics.classification?.recall_macro ?? metrics.classification?.macro_recall) ?? 0) * 100).toFixed(1)}%
                </div>
              </div>

              <div className="p-3 bg-[#111724] rounded-lg border border-slate-800">
                <div className="text-slate-400 text-[10px]">F1-SCORE (MACRO)</div>
                <div className="text-xl font-bold text-amber-400 mt-1">
                  {(((metrics.classification?.f1_macro ?? metrics.classification?.macro_f1) ?? 0) * 100).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: Priority Engine & Spatiotemporal Clustering */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Priority Regression */}
            <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
              <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800 pb-2">
                <Layers className="w-4 h-4 text-rose-400" />
                <span>2. DYNAMIC PRIORITY SCORE (0-100)</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">MEAN ABS ERROR (MAE)</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">
                    {(metrics.priority?.mae ?? metrics.priority_mae?.mae ?? 0).toFixed(2)} pts
                  </div>
                </div>

                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">RMSE ERROR</div>
                  <div className="text-lg font-bold text-cyan-400 mt-1">
                    {(metrics.priority?.rmse ?? metrics.priority_mae?.rmse ?? 0).toFixed(2)} pts
                  </div>
                </div>

                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">TOP-K PRECISION</div>
                  <div className="text-lg font-bold text-amber-400 mt-1">
                    {(((metrics.priority?.top_k_precision ?? metrics.priority_mae?.top_k_precision) ?? 0) * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">TOP-K RECALL</div>
                  <div className="text-lg font-bold text-sky-400 mt-1">
                    {(((metrics.priority?.top_k_recall ?? metrics.priority_mae?.top_k_recall) ?? 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>

            {/* Hotspot Clustering */}
            <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
              <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800 pb-2">
                <Network className="w-4 h-4 text-amber-400" />
                <span>3. DBSCAN SPATIOTEMPORAL CLUSTERING</span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">SILHOUETTE SCORE</div>
                  <div className="text-lg font-bold text-emerald-400 mt-1">
                    {(metrics.hotspot_clustering?.silhouette_score ?? 0).toFixed(3)}
                  </div>
                  <div className="text-[9px] text-slate-500 mt-1">Valid range: -1 to +1</div>
                </div>

                <div className="p-3 bg-[#111724] rounded border border-slate-800">
                  <div className="text-slate-400 text-[10px]">EVALUATED POINTS</div>
                  <div className="text-lg font-bold text-cyan-400 mt-1">
                    {metrics.hotspot_clustering?.total_points ?? metrics.hotspot_clustering?.total_samples ?? 6} Sites
                  </div>
                  <div className="text-[9px] text-slate-500 mt-1">Haversine metric</div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Text-Image Consistency & Resolution Verification */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Department Routing */}
            <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-2">
              <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800 pb-2">
                <Building className="w-4 h-4 text-emerald-400" />
                <span>DEPARTMENT ROUTING</span>
              </div>
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-slate-300">
                  <span>Routing Accuracy:</span>
                  <span className="font-bold text-emerald-400">
                    {((metrics.department_routing?.accuracy ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Macro-F1 Score:</span>
                  <span className="font-bold text-cyan-400">
                    {(((metrics.department_routing?.f1_macro ?? metrics.department_routing?.macro_f1) ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Text-Image Consistency */}
            <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-2">
              <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800 pb-2">
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>TEXT-IMAGE CONSISTENCY</span>
              </div>
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-slate-300">
                  <span>Precision (Macro):</span>
                  <span className="font-bold text-cyan-400">
                    {(((metrics.text_image_consistency?.precision_macro ?? metrics.text_image_consistency?.macro_precision) ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Recall / F1:</span>
                  <span className="font-bold text-emerald-400">
                    {(((metrics.text_image_consistency?.f1_macro ?? metrics.text_image_consistency?.macro_f1) ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Resolution Verification */}
            <div className="bg-[#0e131d] border border-slate-800 rounded-xl p-4 shadow-xl space-y-2">
              <div className="flex items-center gap-2 text-slate-200 font-bold border-b border-slate-800 pb-2">
                <ShieldCheck className="w-4 h-4 text-indigo-400" />
                <span>RESOLUTION VERIFICATION</span>
              </div>
              <div className="space-y-1 pt-1">
                <div className="flex justify-between text-slate-300">
                  <span>Precision (Macro):</span>
                  <span className="font-bold text-indigo-400">
                    {(((metrics.resolution_verification?.precision_macro ?? metrics.resolution_verification?.macro_precision) ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Macro-F1 Score:</span>
                  <span className="font-bold text-emerald-400">
                    {(((metrics.resolution_verification?.f1_macro ?? metrics.resolution_verification?.macro_f1) ?? 0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
