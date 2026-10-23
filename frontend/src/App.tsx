import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence, MotionConfig } from 'framer-motion'
import { MotionProvider, useCivicMotion } from './lib/motionContext'
import { api } from './services/api'
import { Issue, HotspotInfo, RecurrenceInfo, SystemHealth } from './types'
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
import { TargetCursor } from './components/reactbits/TargetCursor'

import { Shield, Loader2 } from 'lucide-react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { LoginPage } from './components/auth/LoginPage'
import { RoleLoginForm } from './components/auth/RoleLoginForm'
import { CitizenPortalView } from './components/portal/CitizenPortalView'

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
  const { user } = useAuth()
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
    return user?.role === 'citizen' ? 'citizen_portal' : 'overview'
  }
  const [activeView, setActiveView] = useState<string>(getInitialView)

  // Enforce role boundaries on views
  useEffect(() => {
    if (user?.role === 'citizen') {
      const citizenAllowed = ['citizen_portal', 'map', 'analyze']
      if (!citizenAllowed.includes(activeView)) {
        setActiveView('citizen_portal')
      }
    } else if (user?.role === 'inspector') {
      const officerAllowed = ['overview', 'explorer', 'map', 'intelligence', 'live', 'resolution', 'analytics']
      if (!officerAllowed.includes(activeView)) {
        setActiveView('overview')
      }
    }
  }, [user?.role, activeView])

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
  const [healthData, setHealthData] = useState<SystemHealth | null>(null)
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

  // Demo Sequence Stepper (Screens 1 to 5)
  const handleSetDemoStep = (step: number) => {
    const bounded = Math.max(1, Math.min(5, step))
    setActiveDemoStep(bounded)

    if (bounded === 1 || bounded === 2 || bounded === 3) {
      setActiveView('analyze')
    } else if (bounded === 4) {
      setActiveView('map')
      setInspectingIssue(DEMO_SCENARIO.issueRecord)
    } else if (bounded === 5) {
      setActiveView('resolution')
      setInspectingIssue(DEMO_SCENARIO.issueRecord)
    }
  }

  const handleStartDemo = () => {
    setIsDemoMode(true)
    handleSetDemoStep(1)
    info('Presentation Demo Started', 'Step 1: Pothole & Road Damage Intake. Alt+D to toggle, Alt+R to reset.')
  }

  return (
    <MotionConfig reducedMotion={isReduced ? 'always' : 'never'}>
      <div className="flex h-screen w-full max-w-full bg-[#F6F7FC] text-slate-900 overflow-hidden font-sans select-none">
        {/* Precision Animated Target Cursor Reticle */}
        <TargetCursor />

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
      <div className="flex-1 min-w-0 flex flex-col h-full bg-[#F6F7FC] relative">
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

              {activeView === 'citizen_portal' && (
                <CitizenPortalView />
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
    </MotionConfig>
  )
}

function AppRouter() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const [currentPath, setCurrentPath] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return window.location.pathname
    }
    return '/'
  })

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname)
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const navigateTo = (path: string) => {
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', path)
      setCurrentPath(path)
    }
  }

  // If already authenticated and on a login route, redirect to workspace
  useEffect(() => {
    if (isAuthenticated && (currentPath === '/login' || currentPath.startsWith('/login/'))) {
      navigateTo('/')
    }
  }, [isAuthenticated, currentPath])

  // If unauthenticated and accessing a protected route, redirect URL to /login
  useEffect(() => {
    if (!authLoading && !isAuthenticated && currentPath !== '/login' && !currentPath.startsWith('/login/')) {
      if (typeof window !== 'undefined') {
        window.history.replaceState({}, '', '/login')
        setCurrentPath('/login')
      }
    }
  }, [authLoading, isAuthenticated, currentPath])

  // Loading state: display sleek Aurora Indigo security splash (never reveal privileged content!)
  if (authLoading) {
    return (
      <div className="h-screen w-screen flex flex-col items-center justify-center bg-[#F6F7FC] font-sans">
        <div className="w-12 h-12 rounded-2xl bg-[#13152E] flex items-center justify-center text-white mb-4 shadow-sm border border-white/10">
          <Shield className="w-6 h-6 text-[#8B5CF6]" />
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-[#11162A]">
          <Loader2 className="w-4 h-4 animate-spin text-[#6457E8]" />
          <span>CIVILENS Security Verification...</span>
        </div>
        <p className="text-[11px] text-[#65708B] mt-1">Verifying cryptographic session token</p>
      </div>
    )
  }

  // Explicit Login Routes
  if (currentPath === '/login') {
    return <LoginPage onSelectRole={(role) => navigateTo(`/login/${role}`)} />
  }

  if (currentPath === '/login/citizen') {
    return (
      <RoleLoginForm
        role="citizen"
        onBack={() => navigateTo('/login')}
        onSuccess={() => navigateTo('/')}
      />
    )
  }

  if (currentPath === '/login/municipal') {
    return (
      <RoleLoginForm
        role="municipal"
        onBack={() => navigateTo('/login')}
        onSuccess={() => navigateTo('/')}
      />
    )
  }

  if (currentPath === '/login/admin') {
    return (
      <RoleLoginForm
        role="admin"
        onBack={() => navigateTo('/login')}
        onSuccess={() => navigateTo('/')}
      />
    )
  }

  // Protected route boundary: unauthenticated users redirected to /login
  if (!isAuthenticated) {
    return <LoginPage onSelectRole={(role) => navigateTo(`/login/${role}`)} />
  }

  return (
    <SidebarProvider defaultOpen={true} className="h-screen w-full max-w-full overflow-hidden bg-[#F5F7FA]">
      <AppContent />
    </SidebarProvider>
  )
}

export function App() {
  return (
    <ErrorBoundary fallbackTitle="CiviLens Command Center Initialization Notice">
      <AuthProvider>
        <MotionProvider>
          <ToastProvider>
            <AppRouter />
          </ToastProvider>
        </MotionProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
