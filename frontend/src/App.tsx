import React, { useState, useEffect } from 'react'
import { api } from './services/api'
import { Issue, HotspotInfo, RecurrenceInfo } from './types'
import { Sidebar } from './components/layout/Sidebar'
import { TopBar } from './components/layout/TopBar'
import { CommandPalette } from './components/common/CommandPalette'
import { ModelStatusModal } from './components/common/ModelStatusModal'
import { SettingsModal } from './components/common/SettingsModal'
import { NewComplaintModal } from './components/issues/NewComplaintModal'
import { ResolutionModal } from './components/issues/ResolutionModal'
import { IssueDetailDrawer } from './components/issues/IssueDetailDrawer'

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

export function App() {
  const [activeView, setActiveView] = useState<string>('overview')
  const [issues, setIssues] = useState<Issue[]>([])
  const [hotspots, setHotspots] = useState<HotspotInfo[]>([])
  const [recurringIssues, setRecurringIssues] = useState<RecurrenceInfo[]>([])
  const [healthData, setHealthData] = useState<any | null>(null)
  const [selectedWard, setSelectedWard] = useState<string>('ALL WARDS (MUMBAI REGION)')
  
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

  // Filter issues by ward if selected
  const displayedIssues = issues.filter((i) => {
    if (selectedWard === 'ALL WARDS (MUMBAI REGION)') return true
    if (selectedWard.includes('N-Ward') && (i.ward === 'N-Ward' || i.location.includes('Vidyavihar') || i.location.includes('Ghatkopar'))) return true
    if (selectedWard.includes('L-Ward') && (i.ward === 'L-Ward' || i.location.includes('Kurla'))) return true
    if (selectedWard.includes('G/North') && (i.ward === 'G/North' || i.location.includes('Dharavi'))) return true
    if (selectedWard.includes('K/West') && (i.ward === 'K/West' || i.location.includes('Andheri'))) return true
    return true
  })

  const criticalCount = issues.filter((i) => i.priorityLevel === 'CRITICAL' || i.priorityScore >= 80).length
  const unreportedCount = issues.filter((i) => i.metadata?.isAutoDrafted || i.source === 'patrol_camera').length

  const handleIssueCreated = (created: Issue) => {
    setIssues((prev) => [created, ...prev])
    setInspectingIssue(created)
    loadData()
  }

  const handleIssueUpdated = (updated: Issue) => {
    setIssues((prev) => prev.map((i) => (i.issueId === updated.issueId ? updated : i)))
    setInspectingIssue(updated)
  }

  const handleResetDemo = async () => {
    try {
      await api.resetDemo()
      await loadData()
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

  return (
    <div className="flex h-screen w-screen bg-[#080a0f] text-slate-100 overflow-hidden font-sans select-none">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activeView={activeView}
        onSelectView={setActiveView}
        criticalCount={criticalCount}
        hotspotCount={hotspots.length}
        unreportedCount={unreportedCount}
        onOpenModelStatus={() => setModelStatusOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Operational Stage */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-[#0a0d14] relative">
        {/* Top Command Bar */}
        <TopBar
          activeView={activeView}
          onOpenCommandPalette={() => setCommandPaletteOpen(true)}
          onOpenNewComplaint={() => {
            setActiveScenario(null)
            setNewComplaintOpen(true)
          }}
          onResetDemo={handleResetDemo}
          selectedWard={selectedWard}
          onSelectWard={setSelectedWard}
          totalIssuesCount={issues.length}
        />

        {/* View Surface */}
        <main className="flex-1 overflow-hidden relative bg-[#090b10] bg-ops-grid">
          {activeView === 'overview' && (
            <OverviewView
              issues={displayedIssues}
              hotspots={hotspots}
              recurringIssues={recurringIssues}
              onSelectIssue={setInspectingIssue}
              onNavigate={setActiveView}
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

          {activeView === 'analytics' && <AnalyticsView />}
        </main>
      </div>

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
export default App
