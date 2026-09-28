import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import * as endpoints from '../api/endpoints'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('orthoassist_token'))
  const [doctor, setDoctor] = useState(null)
  const [doctorLoading, setDoctorLoading] = useState(!!token)

  const refreshDoctor = useCallback(async () => {
    try {
      const res = await endpoints.getMe()
      setDoctor(res.data)
      return res.data
    } catch {
      setDoctor(null)
      return null
    } finally {
      setDoctorLoading(false)
    }
  }, [])

  useEffect(() => {
    if (token) {
      refreshDoctor()
    } else {
      setDoctorLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loginUser = useCallback(async (email, password) => {
    const res = await endpoints.login(email, password)
    const newToken = res.data.access_token
    localStorage.setItem('orthoassist_token', newToken)
    setToken(newToken)
    await refreshDoctor()
    return newToken
  }, [refreshDoctor])

  const signupUser = useCallback(async (name, email, password) => {
    await endpoints.signup({ name, email, password })
    // Auto-login right after signup so it's a single smooth flow
    return loginUser(email, password)
  }, [loginUser])

  const logout = useCallback(() => {
    localStorage.removeItem('orthoassist_token')
    setToken(null)
    setDoctor(null)
  }, [])

  return (
    <AuthContext.Provider
      value={{ token, isAuthenticated: !!token, doctor, doctorLoading, loginUser, signupUser, logout, refreshDoctor }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
