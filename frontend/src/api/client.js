import axios from 'axios'

export const API_ORIGIN = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_ORIGIN ? API_ORIGIN : '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('orthoassist_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !window.location.pathname.startsWith('/login')
    ) {
      localStorage.removeItem('orthoassist_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export function assetUrl(path) {
  if (!path) return null
  const clean = String(path).replace(/^\/+/, '')
  return API_ORIGIN ? `${API_ORIGIN}/${clean}` : `/${clean}`
}

export default api