import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '../services/api'
import { AuthUser, UserRole } from '../types'

interface AuthContextType {
  user: AuthUser | null
  token: string | null
  role: UserRole | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (usernameOrEmail: string, password: string, expectedRole?: UserRole) => Promise<void>
  register: (payload: { username: string; email: string; password: string; name: string }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const TOKEN_KEY = 'civilens_auth_token'
const USER_KEY = 'civilens_user_profile'

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(USER_KEY)
        return stored ? JSON.parse(stored) : null
      } catch {
        return null
      }
    }
    return null
  })

  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem(TOKEN_KEY)
    }
    return null
  })

  const [isLoading, setIsLoading] = useState<boolean>(true)

  // Verify server session on initial load or token change
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY)
      if (!storedToken) {
        setUser(null)
        setToken(null)
        setIsLoading(false)
        return
      }

      try {
        const verifiedUser = await api.auth.me()
        setUser(verifiedUser)
        setToken(storedToken)
        localStorage.setItem(USER_KEY, JSON.stringify(verifiedUser))
      } catch {
        // Token invalid, expired, or rejected by server
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        setUser(null)
        setToken(null)
      } finally {
        setIsLoading(false)
      }
    }

    verifySession()
  }, [])

  const login = async (usernameOrEmail: string, password: string, expectedRole?: UserRole) => {
    setIsLoading(true)
    try {
      const res = await api.auth.login({ usernameOrEmail, password, expectedRole })
      localStorage.setItem(TOKEN_KEY, res.token)
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))
      // Also set role token for backward compatibility
      localStorage.setItem(`civilens_${res.user.role}_token`, res.token)
      setUser(res.user)
      setToken(res.token)
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (payload: { username: string; email: string; password: string; name: string }) => {
    setIsLoading(true)
    try {
      const res = await api.auth.register(payload)
      localStorage.setItem(TOKEN_KEY, res.token)
      localStorage.setItem(USER_KEY, JSON.stringify(res.user))
      localStorage.setItem(`civilens_${res.user.role}_token`, res.token)
      setUser(res.user)
      setToken(res.token)
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await api.auth.logout()
    } catch {
      // Continue clearing local state
    }
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    if (user?.role) {
      localStorage.removeItem(`civilens_${user.role}_token`)
    }
    localStorage.removeItem('civilens_token')
    localStorage.removeItem('civilens_user')
    localStorage.removeItem('civilens_citizen_token')
    localStorage.removeItem('civilens_inspector_token')
    localStorage.removeItem('civilens_admin_token')
    setUser(null)
    setToken(null)
    if (typeof window !== 'undefined') {
      window.location.replace('/login')
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || null,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
