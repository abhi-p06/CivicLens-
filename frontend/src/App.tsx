import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { MotionProvider, useCivicMotion } from './lib/motionContext'
import { api } from './services/api'
import { Issue, HotspotInfo, RecurrenceInfo } from './types'
import { Sidebar } from './components/layout/Sidebar'
import { SidebarProvider } from './components/ui/sidebar'
import { TopBar } from './components/layout/TopBar'
import { CommandPalette } from './components/common/CommandPalette'
import { ModelStatusModal } from './components/common/ModelStatusModal'
import { SettingsModal } from './components/common/SettingsModal'
import { NewComplaintModal } from './components/issues/NewComplaintModal'
import { ResolutionModal } from './components/issues/ResolutionModal'
import { IssueDetailDrawer } from './components/issues/IssueDetailDrawer'
import { ToastProvider, useToast } from './components/common/Toast'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { GuidedDemoController } from './components/demo/GuidedDemoController'
import { DEMO_SCENARIO } from './services/demoScenario'

// Views
import { OverviewView } from './components/views/OverviewView'
import { LiveIntelligenceView } from './components/views/LiveIntelligenceView'
import { AnalysisPipelineView } from './components/pipeline/AnalysisPipelineView'
import { ExplorerView } from './components/views/ExplorerView'
import { MapView } from './components/views/MapView'
import { HotspotsView } from './components/views/HotspotsView'
import { RecurringView } from './components/views/RecurringView'
import { UnreportedView } from './components/views/UnreportedView'
import { ResolutionView } from './components/views/ResolutionView'
import { AnalyticsView } from './components/views/AnalyticsView'
import { IssueIntelligenceView } from './components/views/IssueIntelligenceView'

function AppContent() {
  const { success, info } = useToast()
  const { isReduced } = useCivicMotion()
  const getInitialView = () => {
    if (typeof window !== 'undefined') {
      const hash = window.location.hash.replace('#', '')
      if (hash) return hash
      const params = new URLSearchParams(window.location.search)
      const v = params.get('view')
      if (v) return v
    }
    return 'overview'
  }
  const [activeView, setActiveView] = useState<string>(getInitialView)

  const handleSelectView = (view: string) => {
    setActiveView(view)
    if (typeof window !== 'undefined') {
      window.location.hash = view
    }
  }

  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '')
      if (hash) setActiveView(hash)
    }
    window.addEventListener('hashchange', handleHash)
    return () => window.removeEventListener('hashchange', handleHash)
  }, [])

  const [issues, setIssues] = useState<Issue[]>([])
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([])
  const [recurringIssues, setRecurringIssues] = useState<RecurrenceInfo[]>([])
  const [healthData, setHealthData] = useState<any | null>(null)
  const [selectedWard, setSelectedWard] = useState<string>('ALL WARDS (MUMBAI REGION)')

  // Demo Presentation Mode State
  const [isDemoMode, setIsDemoMode] = useState<boolean>(false)
  const [activeDemoStep, setActiveDemoStep] = useState<number>(1)

  // Modals & Drawers
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false)
  const [modelStatusOpen, setModelStatusOpen] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [newComplaintOpen, setNewComplaintOpen] = useState(false)
  const [activeScenario, setActiveScenario] = useState<number | null>(null)
  const [resolutionModalOpen, setResolutionModalOpen] = useState(false)
  const [targetResolutionIssue, setTargetResolutionIssue] = useState<Issue | null>(null)
  const [inspectingIssue, setInspectingIssue] = useState<Issue | null>(null)

  // Initial Data Fetch
  const loadData = async () => {
    try {
      const [allIssues, allHotspots, allRec, health] = await Promise.all([
        api.getIssues(),
        api.getHotspots(),
        api.getRecurringIssues(),
        api.getHealth(),
      ])
      setIssues(allIssues)
      setHotspots(allHotspots)
      setRecurringIssues(allRec)
      setHealthData(health)
    } catch (err) {
      console.error('Failed to load command center state:', err)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Keyboard shortcut listener for Demo Mode (Alt+D)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea') return

      if (e.altKey && e.key.toLowerCase() === 'd') {
        e.preventDefault()
        setIsDemoMode((prev) => {
          const next = !prev
          if (next) handleSetDemoStep(1)
          return next
        })
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [])

  // Filter issues by ward if selected
  const displayedIssues = issues.filter((i) => {
    if (selectedWard === 'ALL WARDS (MUMBAI REGION)') return true
    if (
      selectedWard.includes('N-Ward') &&
      (i.ward === 'N-Ward' || i.location.includes('Vidyavihar') || i.location.includes('Ghatkopar'))
    )
      return true
    if (selectedWard.includes('L-Ward') && (i.ward === 'L-Ward' || i.location.includes('Kurla')))
      return true
    if (
      selectedWard.includes('G/North') &&
      (i.ward === 'G/North' || i.location.includes('Dharavi'))
    )
      return true
    if (
      selectedWard.includes('K/West') &&
      (i.ward === 'K/West' || i.location.includes('Andheri'))
    )
      return true
    return true
  })

  const criticalCount = issues.filter(
    (i) => i.priorityLevel === 'CRITICAL' || i.priorityScore >= 80
  ).length
  const unreportedCount = issues.filter(
    (i) => i.metadata?.isAutoDrafted || i.source === 'patrol_camera'
  ).length

  const handleIssueCreated = (created: Issue) => {
    setIssues((prev) => [created, ...prev])
    setInspectingIssue(created)
    success('Incident Ingested & Dispatched', `Work order ${created.issueId} routed to ${created.department}`)
    loadData()
  }

  const handleIssueUpdated = (updated: Issue) => {
    setIssues((prev) => prev.map((i) => (i.issueId === updated.issueId ? updated : i)))
    setInspectingIssue(updated)
    info('Lifecycle State Advanced', `${updated.issueId} status is now ${updated.status}`)
  }

  const handleResetDemo = async () => {
    try {
      await api.resetDemo()
      await loadData()
      info('Demo State Reset', 'Baseline municipal records restored across all wards.')
    } catch (err) {
      console.error(err)
    }
  }

  const handleRunScenario = (num: number) => {
    setActiveScenario(num)
    setNewComplaintOpen(true)
  }

  const handleOpenResolution = (issue: Issue) => {
    setTargetResolutionIssue(issue)
    setResolutionModalOpen(true)
  }

  // Demo Sequence Stepper (Screens 1 to 6)
  const handleSetDemoStep = (step: number) => {
    const bounded = Math.max(1, Math.min(6, step))
    setActiveDemoStep(bounded)

    if (bounded === 1) {
      setActiveView('overview')
    } else if (bounded === 2 || bounded === 3) {
      setActiveView('analyze')
    } else if (bounded === 4) {
      setActiveView('map')
      setInspectingIssue(DEMO_SCENARIO.issueRecord)
    } else if (bounded === 5) {
      setActiveView('intelligence')
      setInspectingIssue(DEMO_SCENARIO.issueRecord)
    } else if (bounded === 6) {
      setActiveView('resolution')
      setInspectingIssue(DEMO_SCENARIO.issueRecord)
    }
  }

  const handleStartDemo = () => {
    setIsDemoMode(true)
    handleSetDemoStep(1)
    info('Presentation Demo Started', 'Screen 1: Command Center Overview. Alt+D to toggle, Alt+R to reset.')
  }

  return (
    <div className="flex h-screen w-screen bg-[#F6F7FC] text-slate-900 overflow-hidden font-sans select-none">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activeView={activeView}
        onSelectView={handleSelectView}
        criticalCount={criticalCount}
        hotspotCount={hotspots.length}
        unreportedCount={unreportedCount}
        onOpenModelStatus={() => setModelStatusOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Operational Stage */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#F6F7FC] relative">
        {/* Top Command Bar */}
        <TopBar
          activeView={activeView}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenNewComplaint={() => {
            setActiveScenario(null)
            setNewComplaintOpen(true)
          }}
          onResetDemo={handleResetDemo}
          onStartDemo={handleStartDemo}
          isDemoMode={isDemoMode}
          selectedWard={selectedWard}
          onSelectWard={setSelectedWard}
          totalIssuesCount={issues.length}
        />

        {/* View Surface with Subtle Fast Page Transition */}
        <main className="flex-1 overflow-hidden relative bg-[#F6F7FC]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: isReduced ? 0 : 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: isReduced ? 0 : -10 }}
              transition={{ duration: isReduced ? 0.05 : 0.32, ease: [0.16, 1, 0.3, 1] }}
              className="h-full w-full overflow-hidden"
            >
              {activeView === 'overview' && (
                <OverviewView
                  issues={displayedIssues}
                  hotspots={hotspots}
                  recurringIssues={recurringIssues}
                  onSelectIssue={setInspectingIssue}
                  onNavigate={setActiveView}
                  onStartDemo={handleStartDemo}
                />
              )}

              {activeView === 'live' && (
                <LiveIntelligenceView
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'analyze' && (
                <AnalysisPipelineView onIssueCreated={handleIssueCreated} />
              )}

              {activeView === 'intelligence' && (
                <IssueIntelligenceView
                  issues={displayedIssues}
                  selectedIssue={inspectingIssue || DEMO_SCENARIO.issueRecord}
                  onSelectIssue={setInspectingIssue}
                  onUpdateIssue={handleIssueUpdated}
                  onOpenResolutionModal={handleOpenResolution}
                />
              )}

              {activeView === 'explorer' && (
                <ExplorerView
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'map' && (
                <MapView
                  issues={displayedIssues}
                  hotspots={hotspots}
                  recurringIssues={recurringIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'hotspots' && (
                <HotspotsView
                  hotspots={hotspots}
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'recurring' && (
                <RecurringView
                  recurringIssues={recurringIssues}
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'unreported' && (
                <UnreportedView
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                />
              )}

              {activeView === 'resolution' && (
                <ResolutionView
                  issues={displayedIssues}
                  onSelectIssue={setInspectingIssue}
                  onOpenResolutionModal={handleOpenResolution}
                />
              )}

              {activeView === 'analytics' && (
                <AnalyticsView
                  issues={displayedIssues}
                  hotspots={hotspots}
                  recurringIssues={recurringIssues}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Presentation Demo Controller Bar */}
      <AnimatePresence>
        {isDemoMode && (
          <GuidedDemoController
            activeDemoStep={activeDemoStep}
            onSetDemoStep={handleSetDemoStep}
            onExitDemo={() => setIsDemoMode(false)}
            onResetDemo={handleResetDemo}
          />
        )}
      </AnimatePresence>

      {/* Global Modals & Drawers */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onNavigate={setActiveView}
        issues={issues}
        onSelectIssue={setInspectingIssue}
        onOpenSubmit={() => {
          setActiveScenario(null)
          setNewComplaintOpen(true)
        }}
        onResetDemo={handleResetDemo}
        onRunScenario={handleRunScenario}
      />

      <NewComplaintModal
        isOpen={newComplaintOpen}
        onClose={() => setNewComplaintOpen(false)}
        onIssueCreated={handleIssueCreated}
        initialScenario={activeScenario}
      />

      <ResolutionModal
        isOpen={resolutionModalOpen}
        onClose={() => setResolutionModalOpen(false)}
        issue={targetResolutionIssue}
        onVerified={handleIssueUpdated}
      />

      <IssueDetailDrawer
        issue={inspectingIssue}
        onClose={() => setInspectingIssue(null)}
        onUpdateIssue={handleIssueUpdated}
        onOpenResolutionModal={handleOpenResolution}
        onNavigateToIntelligence={(iss) => {
          setInspectingIssue(iss)
          setActiveView('intelligence')
        }}
      />

      <ModelStatusModal
        isOpen={modelStatusOpen}
        onClose={() => setModelStatusOpen(false)}
        healthData={healthData}
      />

      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onConfigSaved={loadData}
      />
    </div>
  )
}

export function App() {
  return (
    <ErrorBoundary fallbackTitle="CiviLens Command Center Initialization Notice">
      <MotionProvider>
        <ToastProvider>
          <SidebarProvider defaultOpen={true} className="h-screen w-screen overflow-hidden bg-[#F5F7FA]">
            <AppContent />
          </SidebarProvider>
        </ToastProvider>
      </MotionProvider>
    </ErrorBoundary>
  )
}

export default App
