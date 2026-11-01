import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  X,
  FileText,
  ExternalLink,
  ShieldCheck,
  Calendar,
  Building,
  CheckCircle2,
  AlertCircle,
  Hash,
  BookOpen
} from 'lucide-react'
import { GuidanceDocument } from '../../types'
import { api } from '../../services/api'
import { Portal } from '../common/Portal'

interface GuidanceDocumentModalProps {
  docId: string | null
  onClose: () => void
}

export const GuidanceDocumentModal: React.FC<GuidanceDocumentModalProps> = ({
  docId,
  onClose,
}) => {
  const [document, setDocument] = useState<GuidanceDocument | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!docId) {
      setDocument(null)
      setError(null)
      return
    }

    let isMounted = true
    setLoading(true)
    setError(null)

    api.getGuidanceDocument(docId)
      .then((doc) => {
        if (isMounted) setDocument(doc)
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load official document.')
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [docId])

  if (!docId) return null

  return (
    <Portal>
      <AnimatePresence>
        <div className="fixed inset-0 z-[9000] flex items-center justify-center p-4 sm:p-6 bg-black/50 backdrop-blur-xs">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="w-full max-w-3xl max-h-[85vh] bg-white border border-[#E4E7F1] rounded-2xl shadow-2xl flex flex-col overflow-hidden text-[#11162A]"
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#E4E7F1] bg-[#F6F7FC]">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-[#6457E8]/10 text-[#6457E8] rounded-xl border border-[#6457E8]/20">
                  <BookOpen className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[#6457E8] uppercase tracking-wider">
                      Official Government Specification
                    </span>
                    {document?.document_status === 'CURRENT' && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Current & Enforceable
                      </span>
                    )}
                    {document?.document_status === 'SUPERSEDED' && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200">
                        Superseded
                      </span>
                    )}
                  </div>
                  <h3 className="text-sm font-bold text-[#11162A] line-clamp-1 mt-0.5">
                    {document?.title || docId}
                  </h3>
                </div>
              </div>

              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-[#65708B] hover:text-[#11162A] hover:bg-black/5 transition cursor-pointer"
                title="Close Document"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5 bg-white text-xs">
              {loading && (
                <div className="py-16 text-center text-[#65708B] space-y-2">
                  <div className="inline-block w-6 h-6 border-2 border-[#6457E8] border-t-transparent rounded-full animate-spin" />
                  <p className="text-xs font-medium">Retrieving official standard document...</p>
                </div>
              )}

              {error && (
                <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 flex items-center gap-3">
                  <AlertCircle className="w-5 h-5 shrink-0 text-rose-600" />
                  <span>{error}</span>
                </div>
              )}

              {document && (
                <>
                  {/* Meta Strip */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 bg-[#F6F7FC] border border-[#E4E7F1] rounded-xl text-[11px]">
                    <div>
                      <span className="text-[#65708B] block font-medium">Issuing Authority</span>
                      <strong className="text-[#11162A] font-semibold flex items-center gap-1 mt-0.5">
                        <Building className="w-3.5 h-3.5 text-[#6457E8]" />
                        {document.source_org}
                      </strong>
                    </div>

                    <div>
                      <span className="text-[#65708B] block font-medium">Document Version</span>
                      <strong className="text-[#11162A] font-semibold block mt-0.5 font-mono">
                        {document.document_version}
                      </strong>
                    </div>

                    <div>
                      <span className="text-[#65708B] block font-medium">Publication Date</span>
                      <strong className="text-[#11162A] font-semibold flex items-center gap-1 mt-0.5">
                        <Calendar className="w-3.5 h-3.5 text-[#65708B]" />
                        {document.publication_date}
                      </strong>
                    </div>

                    <div>
                      <span className="text-[#65708B] block font-medium">Applicable Category</span>
                      <strong className="text-[#6457E8] font-bold block mt-0.5">
                        {document.applicable_category}
                      </strong>
                    </div>
                  </div>

                  {/* Summary */}
                  {document.summary && (
                    <div className="p-3.5 bg-[#F0F2F9] border border-[#E4E7F1] rounded-xl space-y-1">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-[#65708B]">
                        Executive Scope & Statutory Summary
                      </span>
                      <p className="text-[#11162A] leading-relaxed">
                        {document.summary}
                      </p>
                    </div>
                  )}

                  {/* Sections List */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between pb-1 border-b border-[#E4E7F1]">
                      <span className="text-xs font-bold text-[#11162A] uppercase tracking-wider">
                        Indexed Sections & Standard Specifications ({document.sections?.length || 0})
                      </span>
                      <span className="text-[11px] text-[#65708B] font-mono">
                        SHA-256: {document.file_hash.substring(0, 12)}...
                      </span>
                    </div>

                    {document.sections && document.sections.length > 0 ? (
                      <div className="space-y-3">
                        {document.sections.map((sec, idx) => (
                          <div
                            key={sec.section_id || idx}
                            className="p-3.5 rounded-xl border border-[#E4E7F1] bg-white hover:border-[#6457E8]/40 transition space-y-1.5 shadow-2xs"
                          >
                            <div className="flex items-center justify-between">
                              <h4 className="font-bold text-[#11162A] text-xs">
                                {sec.section_title || `Section ${idx + 1}`}
                              </h4>
                              {sec.page_number && (
                                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#F0F2F9] text-[#65708B] border border-[#E4E7F1]">
                                  Page {sec.page_number}
                                </span>
                              )}
                            </div>
                            <p className="text-slate-700 leading-relaxed font-sans text-[11.5px]">
                              {sec.content}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-[#F6F7FC] border border-[#E4E7F1] text-center text-[#65708B]">
                        Full text indexed in knowledge base. Consult source link for complete raw specification.
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-between px-6 py-3.5 border-t border-[#E4E7F1] bg-[#F6F7FC] text-xs">
              {document?.url ? (
                <a
                  href={document.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-[#6457E8] hover:text-[#5145CF] font-semibold transition"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Open Official Government Portal</span>
                </a>
              ) : (
                <span className="text-[#65708B]">CIVILENS Grounded Knowledge Base</span>
              )}

              <button
                onClick={onClose}
                className="px-4 py-1.5 bg-white border border-[#E4E7F1] hover:bg-[#F0F2F9] text-[#11162A] font-semibold rounded-lg shadow-2xs transition cursor-pointer"
              >
                Close Viewer
              </button>
            </div>
          </motion.div>
        </div>
      </AnimatePresence>
    </Portal>
  )
}

