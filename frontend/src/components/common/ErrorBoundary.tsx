import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertCircle, RotateCcw } from 'lucide-react'

interface Props {
  children: ReactNode
  fallbackTitle?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('CiviLens UI Error caught by boundary:', error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="h-full w-full flex items-center justify-center p-8 bg-[#080a0f] text-slate-200 font-mono text-xs">
          <div className="max-w-md w-full p-6 bg-[#0f141f] border border-rose-900/60 rounded-xl shadow-2xl space-y-4 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-rose-950/60 border border-rose-800 flex items-center justify-center text-rose-400">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-wider text-rose-300 uppercase">
                {this.props.fallbackTitle || 'Operational View Temporarily Interrupted'}
              </h2>
              <p className="text-slate-400 font-sans text-xs mt-1">
                The visual component encountered a non-fatal rendering exception.
              </p>
            </div>
            {this.state.error && (
              <div className="p-2.5 bg-black/50 border border-slate-800 rounded text-left text-[11px] text-rose-400 font-mono break-all max-h-24 overflow-y-auto">
                {this.state.error.message}
              </div>
            )}
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-bold transition active:scale-95 cursor-pointer shadow-lg shadow-cyan-950"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reload Operational State</span>
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
