import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ArrowLeft,
  Lock,
  Mail,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Shield,
  Sliders,
  Users,
  CheckCircle2,
  Sparkles
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { UserRole } from '../../types'
import { useCivicMotion } from '../../lib/motionContext'

interface RoleLoginFormProps {
  role: 'citizen' | 'municipal' | 'admin'
  onBack: () => void
  onSuccess: (role: UserRole) => void
}

export const RoleLoginForm: React.FC<RoleLoginFormProps> = ({ role, onBack, onSuccess }) => {
  const { login, register, isLoading: authLoading } = useAuth()
  const { isReduced } = useCivicMotion()

  // For Citizen role, allow toggling between Sign In and Registration
  const [isRegisterMode, setIsRegisterMode] = useState(false)

  // Form State
  const [usernameOrEmail, setUsernameOrEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [regUsername, setRegUsername] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const roleMeta = {
    citizen: {
      title: 'Citizen Portal Login',
      badge: 'Public Workspace',
      icon: Users,
      badgeColor: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      iconBg: 'bg-emerald-50 text-emerald-600 border-emerald-200',
      description: 'Sign in to submit complaints, attach photos, and check your resolution history.',
      demoEmail: 'citizen@civilens.org',
    },
    municipal: {
      title: 'Municipal Officer Login',
      badge: 'Field Operations',
      icon: ShieldCheck,
      badgeColor: 'bg-indigo-50 text-[#6457E8] border-indigo-200',
      iconBg: 'bg-indigo-50 text-[#6457E8] border-indigo-200',
      description: 'Authorized field inspectors and ward officers login to triage incidents and verify repairs.',
      demoEmail: 'inspector@civilens.org',
    },
    admin: {
      title: 'Administrator Login',
      badge: 'Command & Governance',
      icon: Sliders,
      badgeColor: 'bg-purple-50 text-purple-700 border-purple-200',
      iconBg: 'bg-purple-50 text-purple-600 border-purple-200',
      description: 'Authorized administrators login to manage department routing, review telemetry, and govern settings.',
      demoEmail: 'admin@civilens.org',
    },
  }[role]

  const handleFillDemo = () => {
    setUsernameOrEmail(roleMeta.demoEmail)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (isRegisterMode && role === 'citizen') {
      if (!name.trim()) {
        setError('Please enter your full name.')
        return
      }
      if (!email.trim() || !email.includes('@')) {
        setError('Please enter a valid email address.')
        return
      }
      if (!regUsername.trim() || regUsername.trim().length < 3) {
        setError('Username must be at least 3 characters.')
        return
      }
      if (!password || password.length < 6) {
        setError('Password must be at least 6 characters.')
        return
      }

      setIsSubmitting(true)
      try {
        await register({
          username: regUsername.trim(),
          email: email.trim(),
          password,
          name: name.trim(),
        })
        onSuccess('citizen')
      } catch (err: any) {
        setError(err.message || 'Registration failed. Please try again.')
      } finally {
        setIsSubmitting(false)
      }
    } else {
      if (!usernameOrEmail.trim()) {
        setError('Please enter your username or email.')
        return
      }
      if (!password) {
        setError('Please enter your password.')
        return
      }

      setIsSubmitting(true)
      try {
        const expectedRole: UserRole =
          role === 'municipal' ? 'inspector' : (role as UserRole)
        await login(usernameOrEmail.trim(), password, expectedRole)
        onSuccess(expectedRole)
      } catch (err: any) {
        setError(err.message || 'Login failed. Please verify your credentials.')
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const Icon = roleMeta.icon

  return (
    <div className="min-h-screen bg-[#F6F7FC] flex flex-col justify-between font-sans text-[#11162A]">
      {/* Top Banner */}
      <header className="h-16 px-6 sm:px-12 flex items-center justify-between border-b border-[#E4E7F1] bg-white shadow-[0_1px_2px_rgba(17,22,42,0.02)]">
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-[#65708B] hover:text-[#11162A] transition-colors cursor-pointer group"
        >
          <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          <span>Back to role selection</span>
        </button>

        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-[#13152E] flex items-center justify-center text-white">
            <Shield className="w-4 h-4 text-[#8B5CF6]" />
          </div>
          <span className="font-bold text-sm tracking-tight text-[#11162A]">
            CIVILENS
          </span>
        </div>
      </header>

      {/* Main Form Container */}
      <main className="flex-1 max-w-lg w-full mx-auto px-6 py-10 sm:py-14 flex flex-col justify-center">
        <motion.div
          initial={isReduced ? false : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="bg-white rounded-2xl border border-[#E4E7F1] p-7 sm:p-9 shadow-[0_8px_24px_rgba(17,22,42,0.04)]"
        >
          {/* Header */}
          <div className="text-center mb-6">
            <div
              className={`w-12 h-12 rounded-xl flex items-center justify-center border mx-auto mb-3 shadow-xs ${roleMeta.iconBg}`}
            >
              <Icon className="w-6 h-6" />
            </div>

            <div className="inline-block mb-2">
              <span
                className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border font-mono ${roleMeta.badgeColor}`}
              >
                {roleMeta.badge}
              </span>
            </div>

            <h1 className="text-2xl font-extrabold text-[#11162A]">
              {isRegisterMode && role === 'citizen' ? 'Create Citizen Account' : roleMeta.title}
            </h1>
            <p className="text-xs text-[#65708B] mt-1.5 leading-relaxed">
              {roleMeta.description}
            </p>
          </div>

          {/* Error Banner */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mb-5 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5 overflow-hidden"
              >
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                <span className="leading-snug">{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && role === 'citizen' ? (
              <>
                {/* Full Name */}
                <div>
                  <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. Ramesh Kumar"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                    />
                  </div>
                </div>

                {/* Email */}
                <div>
                  <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="email"
                      required
                      placeholder="e.g. ramesh@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                    />
                  </div>
                </div>

                {/* Username */}
                <div>
                  <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                    Choose Username
                  </label>
                  <div className="relative">
                    <User className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      required
                      placeholder="e.g. ramesh_k"
                      value={regUsername}
                      onChange={(e) => setRegUsername(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                    />
                  </div>
                </div>
              </>
            ) : (
              /* Username or Email */
              <div>
                <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                  Email or Username
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    autoComplete="username"
                    placeholder="Enter your registered email or username"
                    value={usernameOrEmail}
                    onChange={(e) => setUsernameOrEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                  />
                </div>
              </div>
            )}

            {/* Password Field with Show/Hide toggle */}
            <div>
              <label className="block text-xs font-semibold text-[#11162A] mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-[#65708B] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-[#E4E7F1] focus:border-[#6457E8] focus:ring-2 focus:ring-[#6457E8]/20 outline-none text-xs sm:text-sm text-[#11162A] transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#65708B] hover:text-[#11162A] cursor-pointer"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={isSubmitting || authLoading}
                className="w-full py-2.5 px-4 bg-[#6457E8] hover:bg-[#5145CF] disabled:opacity-60 text-white rounded-xl text-xs sm:text-sm font-semibold transition active:scale-[0.98] cursor-pointer shadow-sm flex items-center justify-center gap-2"
              >
                {isSubmitting || authLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Verifying session...</span>
                  </>
                ) : (
                  <span>
                    {isRegisterMode && role === 'citizen'
                      ? 'Create Citizen Account'
                      : 'Sign In to Workspace'}
                  </span>
                )}
              </button>
            </div>
          </form>

          {/* Quick-Fill Demo Helper */}
          {!isRegisterMode && (
            <div className="mt-5 pt-4 border-t border-[#E4E7F1] flex items-center justify-between text-xs">
              <span className="text-[#65708B]">Local demonstration?</span>
              <button
                type="button"
                onClick={handleFillDemo}
                className="text-[#6457E8] hover:text-[#5145CF] font-semibold hover:underline inline-flex items-center gap-1 cursor-pointer"
              >
                <Sparkles className="w-3 h-3" />
                <span>Fill demo account</span>
              </button>
            </div>
          )}

          {/* Citizen Registration / Login Toggle */}
          {role === 'citizen' && (
            <div className="mt-4 pt-3 border-t border-[#E4E7F1] text-center text-xs text-[#65708B]">
              {isRegisterMode ? (
                <span>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegisterMode(false)
                      setError(null)
                    }}
                    className="text-[#6457E8] hover:underline font-semibold cursor-pointer"
                  >
                    Sign in here
                  </button>
                </span>
              ) : (
                <span>
                  New to CIVILENS?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setIsRegisterMode(true)
                      setError(null)
                    }}
                    className="text-[#6457E8] hover:underline font-semibold cursor-pointer"
                  >
                    Create citizen account
                  </button>
                </span>
              )}
            </div>
          )}
        </motion.div>
      </main>

      {/* Footer */}
      <footer className="py-4 px-6 text-center text-xs text-[#65708B] border-t border-[#E4E7F1] bg-white">
        CIVILENS Secure Municipal Authentication &bull; Role Enforcement Active
      </footer>
    </div>
  )
}
