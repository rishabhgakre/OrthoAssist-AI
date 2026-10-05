import axios from 'axios'

// In dev, Vite proxies '/api' and '/uploads' straight to the FastAPI backend
// (see vite.config.js), so this stays empty and everything is same-origin.
// In production, set VITE_API_URL to the backend's origin (e.g.
// https://api.orthoassist.ai) if the frontend isn't served from behind the
// same reverse proxy as the backend.
export const API_ORIGIN = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_ORIGIN,
})

// Attach the JWT token (if we have one) to every outgoing request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('orthoassist_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// If the backend ever returns 401 (expired/invalid token), clear it and
// send the user back to login rather than showing a confusing broken screen.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      localStorage.removeItem('orthoassist_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

/** Builds a URL for a file the backend stored (X-ray images, gait videos),
 * whose DB path already looks like "uploads/xrays/<file>". */
export function assetUrl(path) {
  if (!path) return null
  const clean = String(path).replace(/^\/+/, '')
  return `${API_ORIGIN}/${clean}`
}

export default api
